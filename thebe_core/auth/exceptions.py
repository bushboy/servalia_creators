class AuthenticationError(Exception):
    """The request could not be authenticated."""


class AuthorizationError(Exception):
    """The caller is authenticated but not allowed to perform the action."""


class NotFoundError(Exception):
    """The requested resource does not exist."""
