"""Authentication dependency for the Phase 7 prototype API."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


def _local_api_key() -> Optional[str]:
    """Read the project-root .env key when it is not in the process environment.

    Uvicorn does not load .env files by default. Keep local startup working
    without an extra dotenv dependency, while resolving the file relative to
    this module rather than the caller's working directory.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for line in lines:
        key, separator, value = line.partition("=")
        if separator and key.strip() == "KAIROS_TWIN_API_KEY":
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value or None
    return None


def require_api_key_factory(expected_api_key: Optional[str] = None) -> Callable:
    """
    Build a FastAPI dependency requiring Authorization: Bearer <key>.

    The expected key comes from the explicit factory argument, process
    environment, or project-root .env. Missing server-side config is a 503
    rather than an open endpoint.
    """

    def require_api_key(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    ) -> None:
        configured_key = (
            expected_api_key
            or os.getenv("KAIROS_TWIN_API_KEY")
            or _local_api_key()
        )
        if not configured_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="KAIROS_TWIN_API_KEY is not configured",
            )

        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token required",
            )

        if credentials.credentials != configured_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )

    return require_api_key

