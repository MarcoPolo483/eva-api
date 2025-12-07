"""Azure AD authentication service.

Handles OAuth 2.0 authentication with Azure AD B2C and Entra ID.
"""

import logging
from typing import Any

import jwt
from azure.identity import ClientSecretCredential

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
    
    async def verify_jwt_token(self, token: str) -> JWTClaims:
        """Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            JWTClaims: Decoded token claims
            
        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        # TODO: Phase 1.4 - Implement full JWT verification
        # 1. Get public keys from Azure AD JWKS endpoint
        # 2. Verify signature
        # 3. Verify expiration
        # 4. Verify issuer and audience
        # 5. Extract and validate claims
        
        # For Phase 1, decode without verification (placeholder)
        try:
            decoded = jwt.decode(
                token,
                options={"verify_signature": False},  # TODO: Enable in Phase 1.4
                algorithms=[self.settings.jwt_algorithm],
            )
            
            return JWTClaims(
                sub=decoded.get("sub", ""),
                tenant_id=decoded.get("tid", ""),
                scopes=decoded.get("scp", "").split() if "scp" in decoded else [],
                exp=decoded.get("exp", 0),
                iat=decoded.get("iat", 0),
                iss=decoded.get("iss", ""),
                aud=decoded.get("aud", ""),
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT validation failed: {e}")
            raise
    
    async def get_access_token(
        self,
        grant_type: str,
        client_id: str,
        client_secret: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """Get access token via OAuth 2.0.
        
        Args:
            grant_type: OAuth 2.0 grant type
            client_id: Client ID
            client_secret: Client secret
            scope: Requested scopes
            
        Returns:
            dict: Token response
            
        Raises:
            Exception: If token acquisition fails
        """
        # TODO: Phase 1.4 - Implement OAuth 2.0 token flow
        # 1. Validate grant type
        # 2. Exchange credentials for access token
        # 3. Return token response
        
        logger.warning("Token acquisition not yet implemented (Phase 1.4)")
        return {
            "access_token": "placeholder_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": scope or "",
        }
