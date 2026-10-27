"""
Custom exception hierarchy
"""

# Base exception for all BusBidder domain errors
class BusBidderError(Exception):
    pass

# Raised when an identifier fails regex
class InvalidIdentifierError(ValueError, BusBidderError):
    pass

# Raised when a CSV record contains invalid data types, missing fields, or impossible values
class InvalidRecordError(ValueError, BusBidderError):
    pass

# Raised when a required data file or directory does not exist
class DataNotFoundError(ValueError, BusBidderError):
    pass