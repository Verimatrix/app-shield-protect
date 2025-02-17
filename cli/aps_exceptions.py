'''APS Exceptions'''


class ApsException(Exception):
    """APS Generic Exception."""

class ApsHttpException(ApsException):
    """A HTTP error occurred."""
