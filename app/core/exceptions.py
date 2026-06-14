"""Application errors mapped to HTTP responses in app.main."""


class AppError(Exception):
    """Base error with HTTP status and message."""

    status_code: int = 500

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class BadRequestError(AppError):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)
