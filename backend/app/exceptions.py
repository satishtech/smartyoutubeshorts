"""Custom application exceptions and FastAPI exception handlers."""
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base class for all application-level exceptions."""

    def __init__(self, message: str, code: str, status_code: int = 500) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(f"{resource} not found", "NOT_FOUND", status.HTTP_404_NOT_FOUND)


class ForbiddenError(AppException):
    def __init__(self, message: str = "You do not have access to this resource") -> None:
        super().__init__(message, "FORBIDDEN", status.HTTP_403_FORBIDDEN)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, "CONFLICT", status.HTTP_409_CONFLICT)


class ValidationAppError(AppException):
    def __init__(self, message: str = "Invalid input") -> None:
        super().__init__(message, "VALIDATION_ERROR", status.HTTP_422_UNPROCESSABLE_ENTITY)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, "UNAUTHORIZED", status.HTTP_401_UNAUTHORIZED)


class BadRequestError(AppException):
    def __init__(self, message: str = "Bad request") -> None:
        super().__init__(message, "BAD_REQUEST", status.HTTP_400_BAD_REQUEST)


class ExternalServiceError(AppException):
    """Raised when a downstream service (yt-dlp, ffmpeg, OpenAI, Anthropic, ...) fails."""

    def __init__(self, message: str = "An external service failed") -> None:
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", status.HTTP_502_BAD_GATEWAY)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning("AppException on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
        )
