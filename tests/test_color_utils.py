import pytest
from utils.color_utils import (
    hex_to_rgb,
    color_distance,
    rgb_to_xyz,
    xyz_to_lab,
    get_color_name
)

def test_hex_to_rgb_valid():
    """Test valid hex color conversion."""
    assert hex_to_rgb('#FF0000') == (255, 0, 0)  # Red
    assert hex_to_rgb('00FF00') == (0, 255, 0)   # Green
    assert hex_to_rgb('#0000FF') == (0, 0, 255)  # Blue
    assert hex_to_rgb('#FFFFFF') == (255, 255, 255)  # White
    assert hex_to_rgb('#000000') == (0, 0, 0)    # Black
    assert hex_to_rgb('#808080') == (128, 128, 128)  # Gray

def test_hex_to_rgb_invalid():
    """Test invalid hex color handling."""
    assert hex_to_rgb('invalid') is None
    assert hex_to_rgb('#XYZ') is None
    assert hex_to_rgb('') is None
    assert hex_to_rgb('#12345') is None  # Too short
    assert hex_to_rgb('#1234567') is None  # Too long
    assert hex_to_rgb('#GGGGGG') is None  # Invalid hex chars
    assert hex_to_rgb('  #FF0000  ') is None  # Extra whitespace

def test_rgb_to_xyz():
    """Test RGB to XYZ conversion."""
    # Test with known values
    xyz = rgb_to_xyz((255, 0, 0))  # Pure red
    assert len(xyz) == 3
    assert all(isinstance(v, float) for v in xyz)
    
    # Test with black and white
    black_xyz = rgb_to_xyz((0, 0, 0))
    assert all(v == 0 for v in black_xyz)
    
    white_xyz = rgb_to_xyz((255, 255, 255))
    assert all(v > 0 for v in white_xyz)

def test_xyz_to_lab():
    """Test XYZ to LAB conversion."""
    # Test with known values
    lab = xyz_to_lab((0, 0, 0))  # Black
    assert len(lab) == 3
    assert all(isinstance(v, float) for v in lab)
    
    # Test L value range (should be 0-100)
    for xyz in [(0, 0, 0), (95.047, 100, 108.883)]:
        L, a, b = xyz_to_lab(xyz)
        assert 0 <= L <= 100

def test_color_distance_basic():
    """Test basic color distance calculations."""
    # Same colors should have distance 0
    assert color_distance('#FF0000', '#FF0000') == 0
    assert color_distance('#00FF00', '#00FF00') == 0
    assert color_distance('#0000FF', '#0000FF') == 0

def test_color_distance_complementary():
    """Test distances between complementary colors."""
    # Complementary colors should have large distances
    red_cyan = color_distance('#FF0000', '#00FFFF')
    green_magenta = color_distance('#00FF00', '#FF00FF')
    blue_yellow = color_distance('#0000FF', '#FFFF00')
    
    assert red_cyan > 50
    assert green_magenta > 50
    assert blue_yellow > 50

def test_color_distance_similar():
    """Test distances between similar colors."""
    # Similar colors should have small distances
    dark_red_red = color_distance('#FF0000', '#CC0000')
    light_blue_blue = color_distance('#0000FF', '#3333FF')
    
    assert dark_red_red < 20
    assert light_blue_blue < 20

def test_color_distance_grayscale():
    """Test distances in grayscale."""
    # Test various gray shades
    white_black = color_distance('#FFFFFF', '#000000')
    gray_black = color_distance('#808080', '#000000')
    gray_white = color_distance('#808080', '#FFFFFF')
    
    assert white_black > gray_black
    assert white_black > gray_white

def test_get_color_name():
    """Test color name generation."""
    # Convert colors to Lab space first
    def get_name_for_hex(hex_color):
        rgb = hex_to_rgb(hex_color)
        xyz = rgb_to_xyz(rgb)
        lab = xyz_to_lab(xyz)
        return get_color_name(lab)
    
    # Test basic colors
    assert "Red" in get_name_for_hex('#FF0000')
    assert "Blue" in get_name_for_hex('#0000FF')
    assert "Green" in get_name_for_hex('#00FF00')
    assert "Yellow" in get_name_for_hex('#FFFF00')
    
    # Test light/dark variants
    assert "Light" in get_name_for_hex('#FFB6C1')  # Light pink
    assert "Dark" in get_name_for_hex('#800000')   # Dark red
    
    # Test neutral colors
    assert get_name_for_hex('#000000') == "Black"
    assert get_name_for_hex('#FFFFFF') == "White"
    assert "Gray" in get_name_for_hex('#808080')

def test_color_distance_perceptual():
    """Test that color distances match human perception."""
    # Similar reds should be closer than red and blue
    red1_red2 = color_distance('#FF0000', '#FF3333')
    red_blue = color_distance('#FF0000', '#0000FF')
    assert red1_red2 < red_blue
    
    # Similar light colors should be closer than light and dark
    light1_light2 = color_distance('#FFEEEE', '#FFEEFF')
    light_dark = color_distance('#FFEEEE', '#332222')
    assert light1_light2 < light_dark

def test_color_distance_symmetry():
    """Test that color distance is symmetric."""
    color1 = '#FF0000'
    color2 = '#00FF00'
    dist1 = color_distance(color1, color2)
    dist2 = color_distance(color2, color1)
    assert dist1 == dist2

def test_color_distance_invalid():
    """Test that color distance handles invalid colors."""
    # Invalid colors should return None
    assert color_distance('#FF0000', 'invalid') is None
    assert color_distance('invalid', '#FF0000') is None
    assert color_distance('invalid', 'invalid') is None
