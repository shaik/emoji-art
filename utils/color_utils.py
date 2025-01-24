import re
from typing import Tuple, Optional
import math

def hex_to_rgb(hex_color: str) -> Optional[Tuple[int, int, int]]:
    """Convert hex color to RGB tuple."""
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Validate hex color format
    if not re.match(r'^[0-9A-Fa-f]{6}$', hex_color):
        return None
    
    # Convert to RGB
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError:
        return None

def rgb_to_xyz(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert RGB to XYZ color space."""
    r, g, b = rgb
    
    # Convert to 0-1 range and apply gamma correction
    r = r / 255
    g = g / 255
    b = b / 255
    
    # Gamma correction
    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
    
    # Convert to XYZ
    r *= 100
    g *= 100
    b *= 100
    
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    
    return (x, y, z)

def xyz_to_lab(xyz: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Convert XYZ to LAB color space."""
    x, y, z = xyz
    
    # D65 illuminant reference values
    xn, yn, zn = 95.047, 100.0, 108.883
    
    # Convert XYZ to L*a*b*
    def f(t: float) -> float:
        return t ** (1/3) if t > 0.008856 else (7.787 * t) + (16/116)
    
    fx = f(x/xn)
    fy = f(y/yn)
    fz = f(z/zn)
    
    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    
    return (L, a, b)

def color_distance(color1: str, color2: str) -> Optional[float]:
    """
    Calculate the perceptual distance between two colors using CIE Lab color space.
    Returns None if either color is invalid.
    """
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    if not rgb1 or not rgb2:
        return None
        
    try:
        # Convert both colors to Lab space
        lab1 = xyz_to_lab(rgb_to_xyz(rgb1))
        lab2 = xyz_to_lab(rgb_to_xyz(rgb2))
        
        # Calculate Delta E (CIE76)
        L1, a1, b1 = lab1
        L2, a2, b2 = lab2
        
        deltaL = L1 - L2
        deltaA = a1 - a2
        deltaB = b1 - b2
        
        deltaE = math.sqrt(deltaL**2 + deltaA**2 + deltaB**2)
        
        return deltaE
        
    except (ValueError, ZeroDivisionError):
        return None

def get_color_name(lab_values: Tuple[float, float, float]) -> str:
    """
    Get a human-readable name for a color based on its Lab values.
    This is a basic implementation that can be expanded.
    """
    L, a, b = lab_values
    
    # Lightness categories
    if L < 35:  
        base = "Dark"
    elif L > 75:  
        base = "Light"
    else:
        base = ""
    
    # Color categories based on a and b values
    if abs(a) < 10 and abs(b) < 10:
        if L < 20:
            return "Black"
        elif L > 80:
            return "White"
        else:
            return "Gray"
    
    # Determine primary color based on a and b values
    if abs(a) > abs(b):
        # Red-Green axis is dominant
        if a > 0:
            hue = "Red"
        else:
            hue = "Green"
    else:
        # Blue-Yellow axis is dominant
        if b > 0:
            hue = "Yellow"
        else:
            hue = "Blue"
    
    return f"{base} {hue}".strip()
