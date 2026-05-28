# backend/src/api/middleware.py

import json
import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Logger configuré pour sortir du JSON pur — pas de formatage texte
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("steelbot")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Avant la requête
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # On laisse passer la requête au handler
        response = await call_next(request)

        # Après la requête — on calcule la latence
        latency_ms = round((time.time() - start_time) * 1000)

        log_entry = {
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }

        logger.info(json.dumps(log_entry, ensure_ascii=False))
        return response