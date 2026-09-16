# core/exceptions.py — CUSTOS Base Exceptions

class CustosException(Exception):
    """Base exception for all CUSTOS errors."""
    pass

class ConfigurationError(CustosException):
    """Raised when system or model configuration is invalid."""
    pass

class PipelineError(CustosException):
    """Raised when video ingestion or processing pipeline fails."""
    pass

class CameraError(CustosException):
    """Raised when camera stream cannot be accessed or fails."""
    pass

class DatabaseError(CustosException):
    """Raised when database query or transaction encounters a failure."""
    pass

class SecurityError(CustosException):
    """Raised when an authentication or authorization failure occurs."""
    pass
