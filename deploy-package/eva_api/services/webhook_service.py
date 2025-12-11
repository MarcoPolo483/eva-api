"""Webhook Event Delivery Service - Phase 3.

Async event delivery system with:
- HTTP POST delivery with timeout
- Exponential backoff retry (1s, 5s, 25s)
- HMAC-SHA256 signature verification
- Delivery logging to Cosmos DB
- Dead letter queue for failed events
- Background task processing
"""

import asyncio
import hashlib
import hmac
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from azure.cosmos import exceptions as cosmos_exceptions

from eva_api.config import get_settings
from eva_api.services.cosmos_service import CosmosDBService

logger = logging.getLogger(__name__)

# Retry configuration
RETRY_DELAYS = [1, 5, 25]  # seconds - exponential backoff
HTTP_TIMEOUT = 10.0  # seconds
MAX_RESPONSE_BODY_LOG = 1024  # bytes


def _get_cosmos_service() -> CosmosDBService:
    """Get Cosmos DB service instance.
    
    Returns:
        CosmosDBService: Cosmos DB service
    """
    settings = get_settings()
    return CosmosDBService(settings)


class WebhookService:
    """Service for delivering webhook events with retry logic."""

    def __init__(self):
        """Initialize webhook service."""
        self._http_client: Optional[httpx.AsyncClient] = None
        self._delivery_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the webhook delivery worker."""
        if self._running:
            logger.warning("Webhook service already running")
            return

        self._running = True
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(HTTP_TIMEOUT),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

        # Start background worker
        self._worker_task = asyncio.create_task(self._delivery_worker())
        logger.info("Webhook delivery service started")

    async def stop(self) -> None:
        """Stop the webhook delivery worker."""
        if not self._running:
            return

        self._running = False

        # Cancel worker task
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Close HTTP client
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        logger.info("Webhook delivery service stopped")

    async def deliver_event(
        self,
        webhook_id: str,
        event: Dict[str, Any],
        tenant_id: str,
    ) -> None:
        """Queue an event for delivery to a webhook.

        Args:
            webhook_id: Webhook subscription ID
            event: Event payload to deliver
            tenant_id: Tenant ID for isolation
        """
        if not self._running:
            logger.warning("Webhook service not running, starting now...")
            await self.start()

        delivery_task = {
            "webhook_id": webhook_id,
            "event": event,
            "tenant_id": tenant_id,
            "queued_at": datetime.utcnow().isoformat() + "Z",
        }

        await self._delivery_queue.put(delivery_task)
        logger.debug(f"Event queued for webhook {webhook_id}: {event['event_type']}")

    async def broadcast_event(
        self,
        event_type: str,
        event: Dict[str, Any],
        tenant_id: str,
    ) -> int:
        """Broadcast an event to all matching webhook subscriptions.

        Args:
            event_type: Event type (e.g., "document.added")
            event: Event payload
            tenant_id: Tenant ID

        Returns:
            Number of webhooks notified
        """
        try:
            # Get all active webhooks for this tenant
            cosmos = _get_cosmos_service()
            
            # Query active webhooks matching this event type
            webhooks = await cosmos.get_active_webhooks(tenant_id, event_type)
            
            # Also check for wildcard matches (e.g., "document.*" matches "document.added")
            event_prefix = event_type.split('.')[0] + '.*'
            wildcard_webhooks = await cosmos.get_active_webhooks(tenant_id, event_prefix)
            
            # Combine and deduplicate webhooks
            all_webhooks = {w['id']: w for w in webhooks + wildcard_webhooks}
            
            if not all_webhooks:
                logger.debug(f"No active webhooks for {event_type}")
                return 0
            
            # Queue delivery for each webhook
            count = 0
            for webhook in all_webhooks.values():
                await self.deliver_event(
                    webhook_id=webhook['id'],
                    event=event,
                    tenant_id=tenant_id
                )
                count += 1
            
            logger.info(f"Queued {count} webhook deliveries for {event_type}")
            return count

        except Exception as e:
            logger.error(f"Failed to broadcast event: {e}", exc_info=True)
            return 0

    async def _delivery_worker(self) -> None:
        """Background worker that processes the delivery queue."""
        logger.info("Webhook delivery worker started")

        while self._running:
            try:
                # Get next delivery task with timeout
                delivery_task = await asyncio.wait_for(
                    self._delivery_queue.get(), timeout=1.0
                )

                # Process delivery in background (don't block queue)
                asyncio.create_task(self._process_delivery(delivery_task))

            except asyncio.TimeoutError:
                # No items in queue, continue loop
                continue
            except asyncio.CancelledError:
                logger.info("Webhook delivery worker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in delivery worker: {e}", exc_info=True)
                await asyncio.sleep(1)

        logger.info("Webhook delivery worker stopped")

    async def _process_delivery(self, delivery_task: Dict[str, Any]) -> None:
        """Process a single webhook delivery with retries.

        Args:
            delivery_task: Delivery task with webhook_id, event, tenant_id
        """
        webhook_id = delivery_task["webhook_id"]
        event = delivery_task["event"]
        tenant_id = delivery_task["tenant_id"]

        try:
            # Fetch webhook details
            cosmos = _get_cosmos_service()
            webhook = await cosmos.get_webhook(webhook_id, tenant_id)
            
            if not webhook:
                logger.warning(f"Webhook {webhook_id} not found, skipping delivery")
                return
            
            if not webhook.get('is_active', False):
                logger.debug(f"Webhook {webhook_id} is inactive, skipping delivery")
                return

            # Attempt delivery with retries
            success = False
            last_error = None

            for attempt in range(len(RETRY_DELAYS) + 1):
                try:
                    result = await self._attempt_delivery(
                        webhook=webhook,
                        event=event,
                        attempt=attempt,
                    )

                    # Log delivery
                    await self._log_delivery(
                        webhook_id=webhook_id,
                        tenant_id=tenant_id,
                        event=event,
                        result=result,
                        attempt=attempt,
                    )

                    if result["success"]:
                        success = True
                        await self._update_webhook_stats(
                            webhook_id, tenant_id, success=True
                        )
                        logger.info(
                            f"Webhook {webhook_id} delivered successfully "
                            f"(attempt {attempt + 1})"
                        )
                        break
                    else:
                        last_error = result.get("error_message")

                except Exception as e:
                    last_error = str(e)
                    logger.error(
                        f"Webhook {webhook_id} delivery attempt {attempt + 1} failed: {e}"
                    )

                # Wait before retry (except on last attempt)
                if attempt < len(RETRY_DELAYS):
                    await asyncio.sleep(RETRY_DELAYS[attempt])

            if not success:
                # All retries failed - send to dead letter queue
                await self._update_webhook_stats(webhook_id, tenant_id, success=False)
                await self._send_to_dead_letter_queue(
                    webhook_id=webhook_id,
                    event=event,
                    tenant_id=tenant_id,
                    error=last_error or "All delivery attempts failed",
                )

        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Webhook {webhook_id} not found, skipping delivery")
        except Exception as e:
            logger.error(f"Failed to process delivery for webhook {webhook_id}: {e}")

    async def _attempt_delivery(
        self,
        webhook: Dict[str, Any],
        event: Dict[str, Any],
        attempt: int,
    ) -> Dict[str, Any]:
        """Attempt to deliver an event to a webhook endpoint.

        Args:
            webhook: Webhook subscription details
            event: Event payload
            attempt: Attempt number (0-indexed)

        Returns:
            Dictionary with success, status_code, response_time_ms, error_message
        """
        url = webhook["url"]
        secret = webhook.get("secret")

        # Generate HMAC signature
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "EVA-API-Webhooks/1.0",
            "X-Event-Type": event.get("event_type", "unknown"),
            "X-Event-ID": event.get("event_id", "unknown"),
            "X-Delivery-Attempt": str(attempt + 1),
        }

        if secret:
            signature = self._generate_signature(event, secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        # Perform HTTP POST
        start_time = time.time()
        try:
            response = await self._http_client.post(
                url,
                json=event,
                headers=headers,
            )

            response_time_ms = (time.time() - start_time) * 1000
            success = 200 <= response.status_code < 300

            return {
                "success": success,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "response_body": response.text[:MAX_RESPONSE_BODY_LOG],
                "error_message": None if success else f"HTTP {response.status_code}",
            }

        except httpx.TimeoutException as e:
            response_time_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "status_code": None,
                "response_time_ms": response_time_ms,
                "response_body": None,
                "error_message": f"Timeout after {HTTP_TIMEOUT}s",
            }

        except httpx.RequestError as e:
            response_time_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "status_code": None,
                "response_time_ms": response_time_ms,
                "response_body": None,
                "error_message": f"Request error: {str(e)}",
            }

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload.

        Args:
            payload: Event payload (will be JSON serialized)
            secret: Webhook secret key

        Returns:
            Hex-encoded HMAC signature
        """
        import json

        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        secret_bytes = secret.encode("utf-8")

        signature = hmac.new(secret_bytes, payload_bytes, hashlib.sha256)
        return signature.hexdigest()

    def verify_signature(
        self,
        payload: Dict[str, Any],
        signature_header: str,
        secret: str,
    ) -> bool:
        """Verify HMAC signature from webhook request.

        Args:
            payload: Event payload
            signature_header: Value from X-Webhook-Signature header
            secret: Webhook secret key

        Returns:
            True if signature is valid
        """
        try:
            # Extract signature from header (format: "sha256=<hex>")
            if not signature_header.startswith("sha256="):
                return False

            received_signature = signature_header[7:]  # Remove "sha256=" prefix
            expected_signature = self._generate_signature(payload, secret)

            # Constant-time comparison to prevent timing attacks
            return hmac.compare_digest(received_signature, expected_signature)

        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False

    async def _log_delivery(
        self,
        webhook_id: str,
        tenant_id: str,
        event: Dict[str, Any],
        result: Dict[str, Any],
        attempt: int,
    ) -> None:
        """Log webhook delivery attempt to Cosmos DB.

        Args:
            webhook_id: Webhook ID
            tenant_id: Tenant ID
            event: Event payload
            result: Delivery result
            attempt: Attempt number
        """
        try:
            cosmos = _get_cosmos_service()
            
            # Create log entry
            log_data = {
                "id": str(uuid4()),
                "webhook_id": webhook_id,
                "tenant_id": tenant_id,
                "event_type": event.get("event_type"),
                "event_id": event.get("event_id"),
                "timestamp": datetime.utcnow().isoformat(),
                "attempt": attempt,
                "status_code": result.get("status_code"),
                "response_body": result.get("response_body", "")[:1000],  # Limit size
                "error": result.get("error"),
                "duration_ms": result.get("duration_ms", 0),
                "success": result.get("success", False)
            }
            
            await cosmos.create_webhook_log(log_data)
            logger.debug(f"Logged delivery for webhook {webhook_id} (attempt {attempt})")

        except Exception as e:
            logger.error(f"Failed to log webhook delivery: {e}")

    async def _update_webhook_stats(
        self,
        webhook_id: str,
        tenant_id: str,
        success: bool,
    ) -> None:
        """Update webhook statistics (success/failure counts).

        Args:
            webhook_id: Webhook ID
            tenant_id: Tenant ID
            success: Whether delivery succeeded
        """
        try:
            cosmos = _get_cosmos_service()
            
            # Get last successful result for response time
            # This is a simplified version - ideally track response time per attempt
            response_time_ms = 0.0
            
            await cosmos.update_webhook_stats(
                webhook_id=webhook_id,
                tenant_id=tenant_id,
                success=success,
                response_time_ms=response_time_ms
            )
            logger.debug(f"Updated stats for webhook {webhook_id} (success={success})")

        except Exception as e:
            logger.error(f"Failed to update webhook stats: {e}")

    async def _send_to_dead_letter_queue(
        self,
        webhook_id: str,
        event: Dict[str, Any],
        tenant_id: str,
        error: str,
    ) -> None:
        """Send failed event to dead letter queue for manual review.

        Args:
            webhook_id: Webhook ID
            event: Event payload
            tenant_id: Tenant ID
            error: Error message
        """
        try:
            cosmos = _get_cosmos_service()
            
            # Create DLQ entry
            dlq_data = {
                "id": str(uuid4()),
                "webhook_id": webhook_id,
                "tenant_id": tenant_id,
                "event": event,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
                "retries_exhausted": True,
                "processed": False
            }
            
            await cosmos.create_dlq_entry(dlq_data)
            logger.warning(
                f"Event sent to DLQ: webhook={webhook_id}, "
                f"event_type={event.get('event_type')}, error={error}"
            )

        except Exception as e:
            logger.error(f"Failed to send event to dead letter queue: {e}")

    def _matches_wildcard(self, event_type: str, subscribed_events: List[str]) -> bool:
        """Check if event type matches any wildcard subscriptions.

        Args:
            event_type: Event type (e.g., "document.added")
            subscribed_events: List of subscribed event patterns (e.g., ["document.*"])

        Returns:
            True if event matches any subscription
        """
        for pattern in subscribed_events:
            if pattern.endswith(".*"):
                prefix = pattern[:-2]  # Remove ".*"
                if event_type.startswith(prefix + "."):
                    return True
            elif pattern == "*":
                return True

        return False


# Singleton instance
_webhook_service: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """Get singleton webhook service instance.

    Returns:
        WebhookService instance
    """
    global _webhook_service

    if _webhook_service is None:
        _webhook_service = WebhookService()

    return _webhook_service


async def start_webhook_service() -> None:
    """Start the webhook service (call from app lifespan)."""
    service = get_webhook_service()
    await service.start()


async def stop_webhook_service() -> None:
    """Stop the webhook service (call from app lifespan)."""
    service = get_webhook_service()
    await service.stop()
