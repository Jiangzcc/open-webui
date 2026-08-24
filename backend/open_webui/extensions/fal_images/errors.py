class FalImageError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class FalImageSizeError(FalImageError):
    """A client-supplied size violates the selected model's declared limits."""


__all__ = ['FalImageError', 'FalImageSizeError']
