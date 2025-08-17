from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os

# Example: API_KEY = os.environ.get("API_KEY")
API_KEY = "your-secret-api-key"
API_KEY_NAME = "X-API-KEY"

api_key_header_scheme = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header_scheme)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )
