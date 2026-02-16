"""
Константи за приложението Smart Football Predictor
"""

# ELO Constants
DEFAULT_ELO_RATING: int = 1500
ELO_K_FACTOR: int = 32
MAX_ELO_CHANGE: int = 50

# Prediction Constants
HIGH_CONFIDENCE_THRESHOLD: int = 60
MEDIUM_CONFIDENCE_THRESHOLD: int = 45
LOW_CONFIDENCE_THRESHOLD: int = 40

# Form Points
FORM_WIN_POINTS: int = 3
FORM_DRAW_POINTS: int = 1
FORM_LOSS_POINTS: int = 0

# API Constants
API_TIMEOUT: int = 10
MAX_RETRIES: int = 3
MAX_FIXTURES: int = 50

# Database Constants
VALID_TABLES = {"teams", "matches", "predictions", "team_statistics"}

# Season
CURRENT_SEASON: str = "2025"
