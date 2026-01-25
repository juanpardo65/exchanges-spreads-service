from .errors import unhandled_exception_handler
from .request_logging import request_logging_middleware

__all__ = ["request_logging_middleware", "unhandled_exception_handler", "setup_middleware"]


def setup_middleware(app):
    app.middleware("http")(request_logging_middleware)
    app.add_exception_handler(Exception, unhandled_exception_handler)
