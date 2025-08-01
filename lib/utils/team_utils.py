"""
Minimal team utilities - only includes actually used functions
Cleaned up version removing 75% of dead code
"""


class TeamUtils:
    """Minimal utility functions for team operations - only used functions"""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Portuguese text for better matching"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove accents
        replacements = {
            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",
            "é": "e",
            "è": "e",
            "ê": "e",
            "í": "i",
            "ì": "i",
            "î": "i",
            "ó": "o",
            "ò": "o",
            "õ": "o",
            "ô": "o",
            "ú": "u",
            "ù": "u",
            "û": "u",
            "ç": "c",
        }

        for original, replacement in replacements.items():
            text = text.replace(original, replacement)

        # Remove extra spaces
        return " ".join(text.split())


class ResponseFormatter:
    """Minimal response formatter - only used functions"""


# Export utility instances
team_utils = TeamUtils()
response_formatter = ResponseFormatter()
