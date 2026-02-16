"""
Custom exceptions for the Smart Football Predictor application
"""


class FootballPredictorError(Exception):
    """Base exception for the application"""

    pass


class APIError(FootballPredictorError):
    """API related error"""

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(FootballPredictorError):
    """Database related error"""

    pass


class ValidationError(FootballPredictorError):
    """Input validation error"""

    pass


class ConfigurationError(FootballPredictorError):
    """Configuration related error"""

    pass
