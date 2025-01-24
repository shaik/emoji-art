import pytest
import os
import csv
from utils.csv_parser import parse_emoji_csv, CSVValidationError, validate_row, is_valid_emoji, is_valid_hex_color
from config.config import Config

@pytest.fixture
def test_csv_path(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_path = tmp_path / "test_emoji.csv"
    return str(csv_path)

@pytest.fixture
def valid_csv_file(test_csv_path):
    """Create a valid test CSV file."""
    data = [
        ['Emoji', 'ASCII Code', 'Hex Color'],
        ['🟩', '129001', '#37c136'],
        ['🟦', '128998', '#3b80f5'],
        ['⬛', '11035', '#3c3c3c'],
        ['🚹', '128697', '#4797e6']
    ]
    
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    
    # Temporarily override the CSV path in config
    original_path = Config.EMOJI_CSV_PATH
    Config.EMOJI_CSV_PATH = test_csv_path
    yield test_csv_path
    Config.EMOJI_CSV_PATH = original_path

def test_emoji_validation():
    """Test emoji validation for various emoji types."""
    # Valid emojis
    assert is_valid_emoji('🟩')  # Square emoji
    assert is_valid_emoji('🟦')  # Square with color
    assert is_valid_emoji('⬛')  # Basic shape
    assert is_valid_emoji('🚹')  # Symbol
    
    # Invalid inputs
    assert not is_valid_emoji('')  # Empty
    assert not is_valid_emoji('abc')  # Plain text
    assert not is_valid_emoji('123')  # Numbers
    assert not is_valid_emoji(' ')  # Whitespace
    assert not is_valid_emoji('🟩🟦')  # Multiple emojis

def test_color_validation():
    """Test hex color validation."""
    # Valid colors
    assert is_valid_hex_color('#37c136')
    assert is_valid_hex_color('#3b80f5')
    assert is_valid_hex_color('#3c3c3c')
    assert is_valid_hex_color('#4797e6')
    
    # Invalid colors
    assert not is_valid_hex_color('')
    assert not is_valid_hex_color('37c136')  # Missing #
    assert not is_valid_hex_color('#37c13')  # Too short
    assert not is_valid_hex_color('#37c136ff')  # Too long
    assert not is_valid_hex_color('#GGGGGG')  # Invalid chars
    assert not is_valid_hex_color('rgb(0,0,0)')  # Wrong format

def test_parse_valid_csv(valid_csv_file):
    """Test parsing a valid CSV file."""
    emoji_data = parse_emoji_csv()
    assert len(emoji_data) == 4
    
    # Check first emoji
    assert emoji_data[0]['Emoji'] == '🟩'
    assert emoji_data[0]['ASCII Code'] == '129001'
    assert emoji_data[0]['Hex Color'] == '#37c136'
    
    # Check another emoji
    assert emoji_data[1]['Emoji'] == '🟦'
    assert emoji_data[1]['ASCII Code'] == '128998'
    assert emoji_data[1]['Hex Color'] == '#3b80f5'

def test_missing_file():
    """Test behavior when CSV file is missing."""
    Config.EMOJI_CSV_PATH = 'nonexistent.csv'
    with pytest.raises(FileNotFoundError):
        parse_emoji_csv()

def test_invalid_headers(test_csv_path):
    """Test CSV with invalid headers."""
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['wrong', 'headers', 'here'])
    
    Config.EMOJI_CSV_PATH = test_csv_path
    with pytest.raises(CSVValidationError) as exc_info:
        parse_emoji_csv()
    assert "Invalid CSV headers" in str(exc_info.value)

def test_invalid_row_data(test_csv_path):
    """Test handling of invalid row data."""
    data = [
        ['Emoji', 'ASCII Code', 'Hex Color'],
        ['invalid', 'not-a-number', 'not-a-color'],  # All invalid
        ['🟩', 'abc', '#37c136'],  # Invalid ASCII
        ['🟩', '129001', 'invalid-color'],  # Invalid color
        ['multiple-emoji-🟩🟦', '129001', '#37c136']  # Invalid emoji
    ]
    
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    
    Config.EMOJI_CSV_PATH = test_csv_path
    emoji_data = parse_emoji_csv()
    assert len(emoji_data) == 0  # No valid rows

def test_empty_csv(test_csv_path):
    """Test handling of empty CSV file."""
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Emoji', 'ASCII Code', 'Hex Color'])  # Only headers
    
    Config.EMOJI_CSV_PATH = test_csv_path
    emoji_data = parse_emoji_csv()
    assert len(emoji_data) == 0

def test_validate_row():
    """Test row validation function."""
    # Valid row
    valid_row = {
        'Emoji': '🟩',
        'ASCII Code': '129001',
        'Hex Color': '#37c136'
    }
    assert validate_row(valid_row, 1) == valid_row
    
    # Invalid emoji
    invalid_emoji = {
        'Emoji': 'abc',
        'ASCII Code': '129001',
        'Hex Color': '#37c136'
    }
    assert validate_row(invalid_emoji, 1) is None
    
    # Invalid ASCII code
    invalid_ascii = {
        'Emoji': '🟩',
        'ASCII Code': 'abc',
        'Hex Color': '#37c136'
    }
    assert validate_row(invalid_ascii, 1) is None
    
    # Invalid color
    invalid_color = {
        'Emoji': '🟩',
        'ASCII Code': '129001',
        'Hex Color': 'invalid'
    }
    assert validate_row(invalid_color, 1) is None
