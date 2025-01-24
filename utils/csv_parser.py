import csv
import re
import logging
from typing import List, Dict, Optional, Tuple
import os
from config.config import Config
import unicodedata

logger = logging.getLogger(__name__)

class CSVValidationError(Exception):
    """Custom exception for CSV validation errors."""
    pass

def is_valid_emoji(emoji: str) -> Tuple[bool, str]:
    """
    Validate if the string is a non-ASCII character or sequence.
    Returns a tuple of (is_valid, error_message).
    If valid, error_message will be empty.
    """
    if not emoji or len(emoji.strip()) == 0:
        return False, "Empty emoji"
    
    normalized = emoji.strip()
    
    try:
        # Basic validation - only check if it's not pure ASCII
        if normalized.isascii():
            return False, "Contains only ASCII characters"
            
        # Accept any non-ASCII character
        return True, ""
            
    except Exception as e:
        return False, f"Error validating emoji: {str(e)}"

def is_valid_hex_color(color: str) -> bool:
    """Validate if the string is a valid hex color code."""
    return bool(re.match(Config.HEX_COLOR_PATTERN, color))

def validate_row(row: Dict[str, str], row_number: int) -> Optional[Dict[str, str]]:
    """
    Validate a single row of emoji data.
    Returns the validated row if valid, None if invalid.
    """
    try:
        # Check if all required fields are present
        for field in Config.EMOJI_CSV_HEADERS:
            if field not in row:
                logger.warning(f"Missing field '{field}' in row {row_number}")
                return None
                
        # Validate emoji
        is_valid, error_msg = is_valid_emoji(row['Emoji'])
        if not is_valid:
            logger.warning(f"Invalid emoji in row {row_number}: {row['Emoji']} - {error_msg}")
            return None
            
        # Validate ASCII code
        try:
            ascii_code = int(row['ASCII Code'])
            if ascii_code < 0:
                logger.warning(f"Invalid ASCII code in row {row_number}: negative value")
                return None
        except ValueError:
            logger.warning(f"Invalid ASCII code in row {row_number}: not a number")
            return None
            
        # Validate hex color
        if not is_valid_hex_color(row['Hex Color']):
            logger.warning(f"Invalid hex color in row {row_number}: {row['Hex Color']}")
            return None
            
        return row
        
    except Exception as e:
        logger.error(f"Error validating row {row_number}: {str(e)}")
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
            if headers != ['Emoji', 'ASCII Code', 'Hex Color']:
                error_msg = f"Invalid CSV headers. Expected: ['Emoji', 'ASCII Code', 'Hex Color'], Got: {headers}"
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
