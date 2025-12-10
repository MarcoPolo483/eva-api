"""Azure AD authentication service.

Handles OAuth 2.0 authentication with Azure AD B2C and Entra ID.
"""

import logging
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import jwt
import requests
from azure.identity import ClientSecretCredential
from jwt import PyJWKClient

from eva_api.config import Settings
from eva_api.models.auth import JWTClaims

logger = logging.getLogger(__name__)


class AzureADService:
    """Service for Azure AD authentication."""

    def __init__(self, settings: Settings) -> None:
        """Initialize Azure AD service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._b2c_credential: ClientSecretCredential | None = None
        self._entra_credential: ClientSecretCredential | None = None

    @property
    def b2c_credential(self) -> ClientSecretCredential:
        """Get Azure AD B2C credential (lazy initialization).

        Returns:
            ClientSecretCredential: B2C credential
        """
        if not self._b2c_credential:
            self._b2c_credential = ClientSecretCredential(
                tenant_id=self.settings.azure_ad_b2c_tenant_id,
                client_id=self.settings.azure_ad_b2c_client_id,
                client_secret=self.settings.azure_ad_b2c_client_secret,
            )
        return self._b2c_credential

    @property
    def entra_credential(self) -> ClientSecretCredential:
        """Get Azure Entra ID credential (lazy initialization).

        Returns:
            ClientSecretCredential: Entra credential
        """
        if not self._entra_credential:
            self._entra_credential = ClientSecretCredential(
                tenant_id=self.settings.azure_entra_tenant_id,
                client_id=self.settings.azure_entra_client_id,
                client_secret=self.settings.azure_entra_client_secret,
            )
        return self._entra_credential

    @lru_cache(maxsize=10)
    def _get_jwks_client(self, issuer: str) -> PyJWKClient:
        """Get JWKS client for token issuer (cached).

        Args:
            issuer: Token issuer URL

        Returns:
            PyJWKClient: JWKS client for fetching public keys
        """
        # Construct JWKS URI from issuer
        if "b2clogin.com" in issuer:
            # Azure AD B2C format
            jwks_uri = f"{issuer}/discovery/v2.0/keys"
        else:
            # Azure AD format
            jwks_uri = f"{issuer}/discovery/v2.0/keys"

        logger.info(f"Creating JWKS client for: {jwks_uri}")
        return PyJWKClient(jwks_uri, cache_keys=True, max_cached_keys=10)

    async def verify_jwt_token(self, token: str) -> JWTClaims:
        """Verify and decode JWT token with full Azure AD validation.

        Args:
            token: JWT token string

        Returns:
            JWTClaims: Decoded and validated token claims

        Raises:
            jwt.InvalidTokenError: If token is invalid
            jwt.ExpiredSignatureError: If token is expired
            jwt.InvalidIssuerError: If issuer is invalid
            jwt.InvalidAudienceError: If audience is invalid
        """
        try:
            # Step 1: Decode header to get issuer and kid
            unverified_header = jwt.get_unverified_header(token)
            unverified_claims = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=[self.settings.jwt_algorithm],
            )

            issuer = unverified_claims.get("iss")
            if not issuer:
                raise jwt.InvalidTokenError("Token missing 'iss' (issuer) claim")

            logger.debug(f"Verifying token from issuer: {issuer}")

            # Step 2: Get signing key from JWKS endpoint
            jwks_client = self._get_jwks_client(issuer)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Step 3: Verify signature and claims
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=[self.settings.jwt_algorithm],
                audience=self.settings.jwt_audience if self.settings.jwt_audience else None,
                issuer=issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": bool(self.settings.jwt_audience),
                    "verify_iss": True,
                    "require": ["exp", "iat", "sub"],
                },
            )

            # Step 4: Additional validations
            current_time = datetime.now(UTC).timestamp()
            exp = decoded.get("exp", 0)

            if exp < current_time:
                raise jwt.ExpiredSignatureError("Token has expired")

            # Step 5: Extract and structure claims
            claims = JWTClaims(
                sub=decoded.get("sub", ""),
                tenant_id=decoded.get("tid", decoded.get("tenant_id", "")),
                scopes=decoded.get("scp", "").split() if "scp" in decoded else [],
                exp=exp,
                iat=decoded.get("iat", 0),
                iss=issuer,
                aud=decoded.get("aud", ""),
            )

            logger.info(f"Successfully verified token for user: {claims.sub}")
            return claims

        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Token expired")
            raise
        except jwt.InvalidIssuerError:
            logger.error("Token verification failed: Invalid issuer")
            raise
        except jwt.InvalidAudienceError:
            logger.error("Token verification failed: Invalid audience")
            raise
        except jwt.InvalidTokenError as e:
            logger.error(f"Token verification failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            raise jwt.InvalidTokenError(f"Token verification failed: {str(e)}")

    async def get_access_token(
        self,
        grant_type: str,
        client_id: str,
        client_secret: str,
        scope: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Get access token via OAuth 2.0 client credentials flow.

        Args:
            grant_type: OAuth 2.0 grant type (must be 'client_credentials')
            client_id: Client ID
            client_secret: Client secret
            scope: Requested scopes
            tenant_id: Azure tenant ID (uses Entra ID if not provided)

        Returns:
            dict: Token response with access_token, token_type, expires_in

        Raises:
            ValueError: If grant type is not supported
            requests.HTTPError: If token request fails
        """
        if grant_type != "client_credentials":
            raise ValueError(f"Unsupported grant type: {grant_type}. Only 'client_credentials' supported.")

        # Determine tenant and construct token endpoint
        tenant = tenant_id or self.settings.azure_entra_tenant_id
        if not tenant:
            raise ValueError("Tenant ID is required for token acquisition")

        token_endpoint = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

        # Prepare request payload
        payload = {
            "grant_type": grant_type,
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope or "https://graph.microsoft.com/.default",
        }

        try:
            logger.info(f"Requesting access token for client: {client_id}")
            response = requests.post(
                token_endpoint,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            response.raise_for_status()

            token_data = response.json()
            logger.info(f"Successfully acquired access token (expires in {token_data.get('expires_in')}s)")

            return {
                "access_token": token_data["access_token"],
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in", 3600),
                "scope": token_data.get("scope", scope or ""),
            }

        except requests.HTTPError as e:
            logger.error(f"Token acquisition failed: {e.response.status_code} - {e.response.text}")
            raise
        except requests.RequestException as e:
            logger.error(f"Token acquisition request failed: {e}")
            raise
        except KeyError as e:
            logger.error(f"Invalid token response format: missing {e}")
            raise ValueError(f"Invalid token response: missing {e}")
