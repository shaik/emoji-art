import csv
import re
import logging
from typing import List, Dict, Optional
import os
from config.config import Config
import unicodedata

logger = logging.getLogger(__name__)

class CSVValidationError(Exception):
    """Custom exception for CSV validation errors."""
    pass

def is_valid_emoji(emoji: str) -> bool:
    """
    Validate if the string is a single emoji character or sequence.
    Handles various emoji formats including:
    - Single unicode emojis (😀)
    - Emoji with variation selectors (❤️)
    - Emoji with skin tone modifiers (👍🏻)
    - Zero-width joiner sequences (👨‍👩‍👧‍👦)
    """
    if not emoji or len(emoji.strip()) == 0:
        return False
    
    normalized = emoji.strip()
    
    try:
        # Basic validation
        if normalized.isascii() or normalized.isalnum():
            return False
            
        # Handle ZWJ sequences
        if '\u200d' in normalized:
            parts = normalized.split('\u200d')
            # Check each part is a valid emoji character
            for part in parts:
                if not part:  # Empty part
                    continue
                # Check if the part is a valid emoji character
                if all(unicodedata.category(c).startswith(('L', 'N', 'P', 'Z')) for c in part):
                    return False
            return True
            
        # For non-ZWJ emojis, check if it's a single emoji
        # This includes variation selectors and skin tone modifiers
        base_char = normalized[0]
        if not (0x1F300 <= ord(base_char) <= 0x1F9FF or  # Emoji range
                0x2600 <= ord(base_char) <= 0x26FF or    # Misc symbols
                0x2700 <= ord(base_char) <= 0x27BF):     # Dingbats
            return False
            
        # Check remaining characters are only modifiers
        for c in normalized[1:]:
            if not (c == '\ufe0f' or                    # Variation selector
                   0x1F3FB <= ord(c) <= 0x1F3FF or      # Skin tone
                   unicodedata.category(c).startswith('M')):  # Combining marks
                return False
                
        return True
        
    except (UnicodeEncodeError, ValueError, IndexError):
        return False

def is_valid_hex_color(color: str) -> bool:
    """Validate if the string is a valid hex color code."""
    return bool(re.match(Config.HEX_COLOR_PATTERN, color))

def validate_row(row: Dict[str, str], row_number: int) -> Optional[Dict[str, str]]:
    """
    Validate a single row of emoji data.
    Returns the validated row if valid, None if invalid.
    """
    try:
        # Check for required fields
        if not all(field in row for field in Config.EMOJI_CSV_HEADERS):
            raise CSVValidationError(f"Missing required fields. Expected: {Config.EMOJI_CSV_HEADERS}")

        # Validate emoji
        if not is_valid_emoji(row['emoji']):
            raise CSVValidationError("Invalid emoji character")

        # Validate color
        if not is_valid_hex_color(row['color']):
            raise CSVValidationError("Invalid hex color code")

        # Validate name
        if not row['name'] or len(row['name'].strip()) == 0:
            raise CSVValidationError("Name cannot be empty")

        return {
            'emoji': row['emoji'].strip(),
            'color': row['color'].upper(),
            'name': row['name'].strip()
        }

    except CSVValidationError as e:
        logger.warning(f"Row {row_number}: {str(e)} - {row}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in row {row_number}: {str(e)} - {row}")
        return None

def parse_emoji_csv() -> List[Dict[str, str]]:
    """
    Parse and validate the emoji CSV file.
    Returns a list of validated emoji data dictionaries.
    """
    csv_path = Config.EMOJI_CSV_PATH
    
    if not os.path.exists(csv_path):
        error_msg = f"Emoji CSV file not found at: {csv_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    emoji_data = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Validate headers
            headers = reader.fieldnames
            if headers != Config.EMOJI_CSV_HEADERS:
                error_msg = f"Invalid CSV headers. Expected: {Config.EMOJI_CSV_HEADERS}, Got: {headers}"
                logger.error(error_msg)
                raise CSVValidationError(error_msg)
            
            # Process rows
            for row_number, row in enumerate(reader, start=2):  # Start at 2 to account for header row
                validated_row = validate_row(row, row_number)
                if validated_row:
                    emoji_data.append(validated_row)

        if not emoji_data:
            logger.warning("No valid emoji data found in CSV file")
        else:
            logger.info(f"Successfully loaded {len(emoji_data)} emoji entries")

        return emoji_data

    except (csv.Error, UnicodeDecodeError) as e:
        error_msg = f"Error reading CSV file: {str(e)}"
        logger.error(error_msg)
        raise CSVValidationError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error parsing CSV: {str(e)}"
        logger.error(error_msg)
        raise
