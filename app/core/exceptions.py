class AppError(Exception):
    """Base application error."""


class NotFoundError(AppError):
    pass


class AuthenticationError(AppError):
    pass


class AuthorizationError(AppError):
    pass


class ExternalServiceError(AppError):
    pass


class ValidationError(AppError):
    pass
