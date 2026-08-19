from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import jwt
from jwt import PyJWKClient

from thebe_core.auth.exceptions import AuthenticationError
from thebe_core.config import settings


class CircuitBreaker:
    """Simple fail-fast wrapper for flaky external identity providers."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = "closed"

    def call(self, fn, *args, **kwargs):
        if self.state == "open":
            if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
            else:
                raise AuthenticationError("Identity provider circuit breaker is open")
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            self.failures += 1
            self.last_failure_time = time.monotonic()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise AuthenticationError(
                f"Identity provider unavailable: {exc}"
            ) from exc
        self.failures = 0
        self.state = "closed"
        return result


class IdentityProvider(ABC):
    """Abstract identity provider. Validates an access token and returns the subject."""

    @abstractmethod
    def validate_token(self, token: str) -> str:
        """Validate a token and return the external subject identifier."""
        raise NotImplementedError


class OIDCIdentityProvider(IdentityProvider):
    """Generic OIDC token validator.

    Works with any OIDC-compliant provider (Keycloak, Auth0, etc.) because the
    validation only depends on the issuer, audience, and JWKS endpoint.
    """

    def __init__(self) -> None:
        issuer = settings.OIDC_ISSUER_URL
        audience = settings.OIDC_AUDIENCE or settings.OIDC_CLIENT_ID
        jwks_url = settings.OIDC_JWKS_URL

        if not issuer or not jwks_url:
            raise RuntimeError(
                "OIDC_ISSUER_URL and OIDC_JWKS_URL must be configured for OIDC auth"
            )

        self.issuer = issuer.rstrip("/")
        self.audience = audience or ""
        self._client = PyJWKClient(
            jwks_url,
            cache_keys=True,
            timeout=10,
        )
        self._circuit = CircuitBreaker()

    def _validate(self, token: str) -> str:
        signing_key = self._client.get_signing_key_from_jwt(token)

        options: dict[str, Any] = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
            "verify_nbf": True,
            "verify_iss": True,
            "verify_aud": bool(self.audience),
        }

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options=options,
            issuer=self.issuer,
            audience=self.audience or None,
        )

        subject = payload.get("sub")
        if not subject:
            raise jwt.InvalidTokenError("Token is missing 'sub' claim")

        return subject

    def validate_token(self, token: str) -> str:
        return self._circuit.call(self._validate, token)
