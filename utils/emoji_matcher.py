import colorsys
from typing import Dict, List, Tuple

class EmojiMatcher:
    # Built-in emoji data with their approximate colors
    DEFAULT_EMOJI_DATA = [
        {"emoji": "⬜", "color": "#FFFFFF"},  # White
        {"emoji": "⬛", "color": "#000000"},  # Black
        {"emoji": "🟥", "color": "#FF0000"},  # Red
        {"emoji": "🟦", "color": "#0000FF"},  # Blue
        {"emoji": "🟩", "color": "#00FF00"},  # Green
        {"emoji": "🟨", "color": "#FFFF00"},  # Yellow
        {"emoji": "🟧", "color": "#FFA500"},  # Orange
        {"emoji": "🟫", "color": "#8B4513"},  # Brown
        {"emoji": "🟪", "color": "#800080"},  # Purple
        {"emoji": "⬜", "color": "#F8F8FF"},  # Ghost White
        {"emoji": "⚪", "color": "#F0F0F0"},  # White Smoke
        {"emoji": "⚫", "color": "#080808"},  # Almost Black
        {"emoji": "❤️", "color": "#FF0000"},  # Heart Red
        {"emoji": "💙", "color": "#0000FF"},  # Heart Blue
        {"emoji": "💚", "color": "#00FF00"},  # Heart Green
        {"emoji": "💛", "color": "#FFD700"},  # Heart Yellow
        {"emoji": "🧡", "color": "#FFA500"},  # Heart Orange
        {"emoji": "💜", "color": "#800080"},  # Heart Purple
        {"emoji": "🤎", "color": "#8B4513"},  # Heart Brown
        {"emoji": "🖤", "color": "#000000"},  # Heart Black
        {"emoji": "🤍", "color": "#FFFFFF"},  # Heart White
        {"emoji": "☀️", "color": "#FFD700"},  # Sun
        {"emoji": "🌙", "color": "#C0C0C0"},  # Moon
        {"emoji": "⭐", "color": "#FFD700"},  # Star
        {"emoji": "🌺", "color": "#FF69B4"},  # Flower Pink
        {"emoji": "🌸", "color": "#FFB6C1"},  # Cherry Blossom
        {"emoji": "🍎", "color": "#FF0000"},  # Red Apple
        {"emoji": "🍏", "color": "#90EE90"},  # Green Apple
        {"emoji": "🍊", "color": "#FFA500"},  # Orange
        {"emoji": "🍋", "color": "#FFD700"},  # Lemon
        {"emoji": "🍇", "color": "#800080"},  # Grapes
        {"emoji": "🫐", "color": "#4169E1"},  # Blueberries
        {"emoji": "🥝", "color": "#90EE90"}   # Kiwi
    ]

    def __init__(self):
        """Initialize the EmojiMatcher with built-in emoji data."""
        self.emoji_data = self.DEFAULT_EMOJI_DATA
        self._cache = {}  # Cache for color matches

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        if not isinstance(hex_color, str) or not hex_color.startswith('#') or len(hex_color) != 7:
            raise ValueError(f"Invalid hex color format: {hex_color}")
        
        try:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            raise ValueError(f"Invalid hex color value: {hex_color}")

    def rgb_to_hsv(self, rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert RGB to HSV color space."""
        return colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)

    def color_distance(self, color1: str, color2: str) -> float:
        """Calculate color distance in HSV space."""
        try:
            rgb1 = self.hex_to_rgb(color1)
            rgb2 = self.hex_to_rgb(color2)
        except ValueError as e:
            raise ValueError(f"Invalid color format: {str(e)}")

        hsv1 = self.rgb_to_hsv(rgb1)
        hsv2 = self.rgb_to_hsv(rgb2)

        # Calculate weighted distance in HSV space
        h_diff = min(abs(hsv1[0] - hsv2[0]), 1 - abs(hsv1[0] - hsv2[0]))
        s_diff = abs(hsv1[1] - hsv2[1])
        v_diff = abs(hsv1[2] - hsv2[2])

        # Weight hue more heavily for better color matching
        return (h_diff * 5) + (s_diff * 3) + v_diff

    def find_closest_emoji(self, color: str) -> Dict:
        """Find the closest matching emoji for a given color."""
        # Check cache first
        if color in self._cache:
            return self._cache[color]

        try:
            # Calculate distances to all emojis
            distances = [(self.color_distance(color, emoji['color']), emoji)
                        for emoji in self.emoji_data]
            
            # Find emoji with minimum distance
            closest_emoji = min(distances, key=lambda x: x[0])[1]
            
            # Cache the result
            self._cache[color] = closest_emoji
            return closest_emoji
        except ValueError as e:
            raise ValueError(f"Error finding closest emoji: {str(e)}")
