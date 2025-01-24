import pytest
from utils.emoji_matcher import EmojiMatcher

@pytest.fixture
def emoji_matcher():
    """Create an EmojiMatcher instance."""
    return EmojiMatcher()

def test_color_distance():
    """Test color distance calculation."""
    matcher = EmojiMatcher()
    # Test exact match
    assert matcher.color_distance('#FF0000', '#FF0000') == 0
    # Test completely different colors
    assert matcher.color_distance('#FF0000', '#0000FF') > 0
    # Test similar colors
    assert matcher.color_distance('#FF0000', '#FF0101') < matcher.color_distance('#FF0000', '#0000FF')

def test_hex_to_rgb():
    """Test hex to RGB conversion."""
    matcher = EmojiMatcher()
    assert matcher.hex_to_rgb('#FF0000') == (255, 0, 0)
    assert matcher.hex_to_rgb('#00FF00') == (0, 255, 0)
    assert matcher.hex_to_rgb('#0000FF') == (0, 0, 255)
    assert matcher.hex_to_rgb('#000000') == (0, 0, 0)
    assert matcher.hex_to_rgb('#FFFFFF') == (255, 255, 255)

def test_find_closest_emoji(emoji_matcher):
    """Test finding closest emoji by color."""
    # Test with common colors
    red_emoji = emoji_matcher.find_closest_emoji('#FF0000')
    assert red_emoji is not None
    assert isinstance(red_emoji, dict)
    assert 'emoji' in red_emoji
    assert 'color' in red_emoji
    
    blue_emoji = emoji_matcher.find_closest_emoji('#0000FF')
    assert blue_emoji is not None
    assert blue_emoji != red_emoji

def test_emoji_cache(emoji_matcher):
    """Test emoji caching functionality."""
    # First call should compute distance
    result1 = emoji_matcher.find_closest_emoji('#FF0000')
    # Second call should use cache
    result2 = emoji_matcher.find_closest_emoji('#FF0000')
    assert result1 == result2

def test_invalid_color_input(emoji_matcher):
    """Test handling of invalid color input."""
    with pytest.raises(ValueError):
        emoji_matcher.find_closest_emoji('invalid')
    with pytest.raises(ValueError):
        emoji_matcher.find_closest_emoji('#FF')
    with pytest.raises(ValueError):
        emoji_matcher.find_closest_emoji('#GGGGGG')

def test_emoji_data_loaded(emoji_matcher):
    """Test that emoji data is properly loaded."""
    assert len(emoji_matcher.emoji_data) > 0
    for emoji in emoji_matcher.emoji_data:
        assert 'emoji' in emoji
        assert 'color' in emoji
        assert emoji['color'].startswith('#')

def test_color_matching_consistency(emoji_matcher):
    """Test that color matching is consistent."""
    # Test multiple times to ensure consistency
    for _ in range(5):
        result1 = emoji_matcher.find_closest_emoji('#FF0000')
        result2 = emoji_matcher.find_closest_emoji('#FF0000')
        assert result1 == result2

def test_edge_case_colors(emoji_matcher):
    """Test matching with edge case colors."""
    # Test black
    black = emoji_matcher.find_closest_emoji('#000000')
    assert black is not None
    
    # Test white
    white = emoji_matcher.find_closest_emoji('#FFFFFF')
    assert white is not None
    
    # Test gray
    gray = emoji_matcher.find_closest_emoji('#808080')
    assert gray is not None

def test_similar_colors(emoji_matcher):
    """Test that similar colors return similar emojis."""
    color1 = emoji_matcher.find_closest_emoji('#FF0000')
    color2 = emoji_matcher.find_closest_emoji('#FF0101')
    
    # Colors are very similar, should return same emoji
    assert color1 == color2
    
    # Test with slightly different colors
    color3 = emoji_matcher.find_closest_emoji('#FF0000')
    color4 = emoji_matcher.find_closest_emoji('#FF1010')
    
    # These might return different emojis, but their colors should be similar
    if color3 != color4:
        distance = emoji_matcher.color_distance(color3['color'], color4['color'])
        assert distance < emoji_matcher.color_distance('#FF0000', '#00FF00')
