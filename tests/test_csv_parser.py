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
        Config.EMOJI_CSV_HEADERS,
        ['😀', '#FFFF00', 'Smiling Face'],
        ['🐶', '#B5651D', 'Dog'],
        ['❤️', '#FF0000', 'Heart'],
        ['👨‍👩‍👧‍👦', '#FF00FF', 'Family'],
        ['👍🏻', '#FFD700', 'Thumbs Up']
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
    assert is_valid_emoji('😀')  # Basic emoji
    assert is_valid_emoji('❤️')  # With variation selector
    assert is_valid_emoji('👍🏻')  # With skin tone
    assert is_valid_emoji('👨‍👩‍👧‍👦')  # Zero-width joiner sequence
    
    # Invalid inputs
    assert not is_valid_emoji('')  # Empty
    assert not is_valid_emoji('abc')  # Plain text
    assert not is_valid_emoji('123')  # Numbers
    assert not is_valid_emoji(' ')  # Whitespace
    assert not is_valid_emoji('😀😀')  # Multiple emojis

def test_color_validation():
    """Test hex color validation."""
    # Valid colors
    assert is_valid_hex_color('#000000')
    assert is_valid_hex_color('#FFFFFF')
    assert is_valid_hex_color('#ff00ff')
    assert is_valid_hex_color('#123ABC')
    
    # Invalid colors
    assert not is_valid_hex_color('')
    assert not is_valid_hex_color('123456')  # Missing #
    assert not is_valid_hex_color('#12345')  # Too short
    assert not is_valid_hex_color('#1234567')  # Too long
    assert not is_valid_hex_color('#GGGGGG')  # Invalid chars
    assert not is_valid_hex_color('rgb(0,0,0)')  # Wrong format

def test_parse_valid_csv(valid_csv_file):
    """Test parsing a valid CSV file."""
    emoji_data = parse_emoji_csv()
    assert len(emoji_data) == 5
    
    # Check first emoji
    assert emoji_data[0]['emoji'] == '😀'
    assert emoji_data[0]['color'] == '#FFFF00'
    assert emoji_data[0]['name'] == 'Smiling Face'
    
    # Check complex emoji
    assert emoji_data[3]['emoji'] == '👨‍👩‍👧‍👦'
    assert emoji_data[3]['color'] == '#FF00FF'
    assert emoji_data[3]['name'] == 'Family'

def test_missing_file():
    """Test behavior when CSV file is missing."""
    Config.EMOJI_CSV_PATH = 'nonexistent.csv'
    with pytest.raises(FileNotFoundError):
        parse_emoji_csv()

def test_invalid_headers(test_csv_path):
    """Test CSV with invalid headers."""
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['wrong', 'headers'])
    
    Config.EMOJI_CSV_PATH = test_csv_path
    with pytest.raises(CSVValidationError) as exc_info:
        parse_emoji_csv()
    assert "Invalid CSV headers" in str(exc_info.value)

def test_invalid_row_data(test_csv_path):
    """Test handling of invalid row data."""
    data = [
        Config.EMOJI_CSV_HEADERS,
        ['abc', '#FFFF00', 'Invalid'],  # Invalid emoji
        ['😀', 'not_hex', 'Invalid Color'],   # Invalid color
        ['😀', '#FFFF00', '']                 # Empty name
    ]
    
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    
    Config.EMOJI_CSV_PATH = test_csv_path
    emoji_data = parse_emoji_csv()
    assert len(emoji_data) == 0  # All rows should be invalid

def test_empty_csv(test_csv_path):
    """Test handling of empty CSV file."""
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(Config.EMOJI_CSV_HEADERS)
    
    Config.EMOJI_CSV_PATH = test_csv_path
    emoji_data = parse_emoji_csv()
    assert len(emoji_data) == 0

def test_validate_row():
    """Test row validation function."""
    # Valid row
    valid_row = {
        'emoji': '😀',
        'color': '#FFFF00',
        'name': 'Smiling Face'
    }
    assert validate_row(valid_row, 1) is not None
    
    # Test each field validation
    invalid_emoji = {
        'emoji': 'X',
        'color': '#FFFF00',
        'name': 'Invalid'
    }
    assert validate_row(invalid_emoji, 1) is None
    
    invalid_color = {
        'emoji': '😀',
        'color': 'not_hex',
        'name': 'Invalid'
    }
    assert validate_row(invalid_color, 1) is None
    
    empty_name = {
        'emoji': '😀',
        'color': '#FFFF00',
        'name': ''
    }
    assert validate_row(empty_name, 1) is None
    
    # Complex emoji test
    complex_emoji = {
        'emoji': '👨‍👩‍👧‍👦',
        'color': '#FF00FF',
        'name': 'Family'
    }
    assert validate_row(complex_emoji, 1) is not None
