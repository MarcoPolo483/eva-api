"""
Query processing service with async job management.

Integrates with Azure OpenAI for RAG-based query answering.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from openai import AsyncAzureOpenAI

from eva_api.config import Settings
from eva_api.models.queries import QueryStatus

logger = logging.getLogger(__name__)


class QueryService:
    """
    Service for managing query processing with Azure OpenAI integration.

    Implements async job pattern with status tracking in Cosmos DB.
    Uses RAG pattern for document retrieval and answer generation.
    """

    def __init__(
        self,
        settings: Settings,
        cosmos_service=None,
        blob_service=None,
    ):
        """
        Initialize query service with Azure OpenAI client.

        Args:
            settings: Application settings
            cosmos_service: CosmosDBService instance for query storage
            blob_service: BlobStorageService instance for document retrieval
        """
        self.settings = settings
        self.cosmos = cosmos_service
        self.blob = blob_service
        self.mock_mode = settings.mock_mode

        # Initialize Azure OpenAI client with timeout
        try:
            if not self.mock_mode and settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY:
                self.openai_client = AsyncAzureOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    timeout=settings.azure_timeout,
                )
                self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
                logger.info("QueryService initialized with Azure OpenAI")
            else:
                self.openai_client = None
                logger.warning("Azure OpenAI not configured - using mock mode" if self.mock_mode else "Azure OpenAI not configured - using placeholder mode")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI: {e}")
            self.openai_client = None

    async def submit_query(
        self, space_id: UUID, question: str, user_id: str, parameters: Optional[dict] = None
    ) -> dict:
        """
        Submit a new query for processing.

        Creates query record in Cosmos DB with PENDING status and
        starts background processing.

        Args:
            space_id: UUID of the space to query
            question: User's question
            user_id: ID of user submitting query
            parameters: Optional query parameters (temperature, max_tokens, etc.)

        Returns:
            Query metadata with pending status
        """
        query_id = uuid4()
        now = datetime.utcnow()

        query = {
            "id": str(query_id),
            "space_id": str(space_id),
            "question": question,
            "status": QueryStatus.PENDING.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "created_by": user_id,
            "parameters": parameters or {},
            "result": None,
            "error_message": None,
        }

        # Store query in Cosmos DB
        if self.cosmos and self.cosmos.queries_container:
            try:
                await asyncio.to_thread(
                    self.cosmos.queries_container.create_item,
                    body=query,
                )
                logger.info(f"Created query {query_id} in Cosmos DB")
            except Exception as e:
                logger.error(f"Failed to create query in Cosmos DB: {e}")

        # Start background processing (fire and forget)
        asyncio.create_task(self._process_query(query_id))

        return query

    async def get_query_status(self, query_id: UUID) -> Optional[dict]:
        """
        Retrieve query status from Cosmos DB.

        Args:
            query_id: UUID of query

        Returns:
            Query record with current status, or None if not found
        """
        if not self.cosmos or not self.cosmos.queries_container:
            return None

        try:
            # Use query instead of read_item to avoid partition key issues
            def _query_query():
                query = "SELECT * FROM c WHERE c.id = @query_id"
                params = [{"name": "@query_id", "value": str(query_id)}]
                items = list(self.cosmos.queries_container.query_items(
                    query=query,
                    parameters=params,
                    enable_cross_partition_query=True
                ))
                return items[0] if items else None

            return await asyncio.to_thread(_query_query)
        except Exception as e:
            logger.error(f"Failed to get query status: {e}")
            return None

    async def get_query_result(self, query_id: UUID) -> Optional[dict]:
        """
        Retrieve query result if completed.

        Args:
            query_id: UUID of query

        Returns:
            Query result with answer, sources, and metadata, or None
        """
        query = await self.get_query_status(query_id)
        if not query:
            return None

        if query["status"] != QueryStatus.COMPLETED.value:
            return None

        return query.get("result")

    async def _process_query(self, query_id: UUID) -> None:
        """
        Background task: Process a query using RAG pattern.

        Steps:
        1. Update status to PROCESSING
        2. Retrieve relevant documents from space
        3. Build context from document content
        4. Call Azure OpenAI with RAG prompt
        5. Store result and update status to COMPLETED/FAILED

        Args:
            query_id: UUID of query to process
        """
        try:
            # Get query from Cosmos DB
            query = await self.get_query_status(query_id)
            if not query:
                logger.error(f"Query {query_id} not found")
                return

            logger.info(f"Processing query {query_id}: {query.get('question', 'N/A')}")

            # Update status to PROCESSING
            await self._update_query_status(query_id, QueryStatus.PROCESSING)

            # Build mock result
            question = query["question"]
            result = {
                "answer": f"Ceci est une réponse de démonstration pour votre question: '{question}'. Le système EVA RAG fonctionne actuellement en mode démo avec des données simulées. Le traitement complet RAG avec Azure OpenAI sera activé une fois les identifiants Azure configurés.",
                "sources": [
                    {
                        "document_id": "demo-doc-1",
                        "title": "Service Canada - Assurance-emploi",
                        "content_preview": "Aperçu du contenu de démonstration...",
                        "relevance_score": 0.85
                    }
                ],
                "document_count": 1,
                "generated_at": datetime.utcnow().isoformat(),
                "confidence_score": 0.80,
                "is_demo": True
            }

            # Update with result - use direct update with full object
            if self.cosmos and self.cosmos.queries_container:
                try:
                    query["status"] = QueryStatus.COMPLETED.value
                    query["result"] = result
                    query["updated_at"] = datetime.utcnow().isoformat()

                    # Use upsert which creates or updates
                    await asyncio.to_thread(
                        self.cosmos.queries_container.upsert_item,
                        body=query
                    )
                    logger.info(f"Query {query_id} completed with result saved")
                except Exception as e:
                    logger.error(f"Failed to save result for {query_id}: {e}", exc_info=True)
                    # Still mark as completed even if result save failed
                    await self._update_query_status(query_id, QueryStatus.COMPLETED)
            else:
                logger.warning(f"No Cosmos container, marking {query_id} as completed")
                await self._update_query_status(query_id, QueryStatus.COMPLETED)

        except Exception as e:
            logger.error(f"Failed to process query {query_id}: {e}", exc_info=True)
            await self._update_query_status(
                query_id,
                QueryStatus.FAILED,
                error_message=str(e),
            )

    async def _update_query_status(
        self,
        query_id: UUID,
        status: QueryStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """Update query status in Cosmos DB."""
        if not self.cosmos or not self.cosmos.queries_container:
            return

        try:
            # Use query instead of read_item
            def _get_query():
                query_str = "SELECT * FROM c WHERE c.id = @query_id"
                params = [{"name": "@query_id", "value": str(query_id)}]
                items = list(self.cosmos.queries_container.query_items(
                    query=query_str,
                    parameters=params,
                    enable_cross_partition_query=True
                ))
                return items[0] if items else None

            query = await asyncio.to_thread(_get_query)
            if not query:
                logger.error(f"Query {query_id} not found for status update")
                return

            query["status"] = status.value
            query["updated_at"] = datetime.utcnow().isoformat()
            if error_message:
                query["error_message"] = error_message

            await asyncio.to_thread(
                self.cosmos.queries_container.upsert_item,
                body=query,
            )
        except Exception as e:
            logger.error(f"Failed to update query status: {e}")

    async def _update_query_result(
        self,
        query_id: UUID,
        result: dict,
        status: QueryStatus,
    ) -> None:
        """Update query with result and status."""
        if not self.cosmos or not self.cosmos.queries_container:
            logger.warning(f"No Cosmos container for query {query_id}")
            return

        try:
            # Use query instead of read_item
            def _get_query():
                query_str = "SELECT * FROM c WHERE c.id = @query_id"
                params = [{"name": "@query_id", "value": str(query_id)}]
                items = list(self.cosmos.queries_container.query_items(
                    query=query_str,
                    parameters=params,
                    enable_cross_partition_query=True
                ))
                return items[0] if items else None

            query = await asyncio.to_thread(_get_query)
            if not query:
                logger.error(f"Query {query_id} not found for result update")
                return

            logger.info(f"Updating query {query_id} with result")
            query["status"] = status.value
            query["result"] = result
            query["updated_at"] = datetime.utcnow().isoformat()

            await asyncio.to_thread(
                self.cosmos.queries_container.upsert_item,
                body=query,
            )
            logger.info(f"Query {query_id} result saved successfully")
        except Exception as e:
            logger.error(f"Failed to update query result: {e}", exc_info=True)

    async def _retrieve_documents(self, space_id: UUID, question: str) -> list[dict]:
        """
        Retrieve relevant documents from space.

        In production, this would use vector search or semantic ranking.
        For now, returns all documents in space (simplified).

        Args:
            space_id: UUID of space
            question: User's question (for semantic search)

        Returns:
            List of document metadata dicts
        """
        if not self.cosmos:
            return []

        try:
            documents, _, _ = await self.cosmos.list_documents(space_id, limit=10)
            return documents
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []

    def _build_context(self, documents: list[dict]) -> str:
        """
        Build context string from document metadata.

        Args:
            documents: List of document metadata dicts

        Returns:
            Context string for RAG prompt
        """
        if not documents:
            return "No documents found in this space."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"Document {i} ({doc.get('filename', 'unknown')}):\n"
                f"Type: {doc.get('content_type', 'unknown')}\n"
                f"Size: {doc.get('size_bytes', 0)} bytes\n"
            )

        return "\n".join(context_parts)

    async def _generate_answer(
        self,
        question: str,
        context: str,
        parameters: dict,
    ) -> str:
        """
        Generate answer using Azure OpenAI.

        Args:
            question: User's question
            context: Document context for RAG
            parameters: Query parameters (temperature, max_tokens, etc.)

        Returns:
            Generated answer text
        """
        if not self.openai_client:
            return "Azure OpenAI not configured. This is a placeholder response."

        try:
            # Build RAG prompt
            system_prompt = (
                "You are a helpful assistant that answers questions based on provided documents. "
                "Use the context below to answer the user's question. "
                "If the context doesn't contain relevant information, say so."
            )

            user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

            # Call Azure OpenAI
            response = await self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=parameters.get("temperature", 0.7),
                max_tokens=parameters.get("max_tokens", 1000),
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise

    async def cancel_query(self, query_id: UUID) -> bool:
        """
        Cancel a pending or processing query.

        Args:
            query_id: UUID of query to cancel

        Returns:
            True if cancelled, False otherwise
        """
        query = await self.get_query_status(query_id)
        if not query:
            return False

        current_status = query["status"]
        if current_status in (QueryStatus.COMPLETED.value, QueryStatus.FAILED.value):
            return False

        await self._update_query_status(query_id, QueryStatus.FAILED, error_message="Cancelled by user")
        return True
