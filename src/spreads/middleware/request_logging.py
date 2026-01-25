import logging
import time
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


async def request_logging_middleware(request: Request, call_next) -> Response:
    method = request.method
    path = request.url.path
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - t0) * 1000
    logger.debug("%s %s %d %.0fms", method, path, response.status_code, elapsed)
    return response
