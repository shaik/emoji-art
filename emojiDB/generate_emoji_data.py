#!/usr/bin/env python3
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path

def parse_emoji_test_file(file_path):
    """Parse the emoji-test.txt file to get emoji data."""
    emojis = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Parse emoji line
            # Format: code points; status # emoji name
            try:
                # Split into code points and description
                code_points, rest = line.split(';')
                # Get status and emoji
                status_desc = rest.split('#')
                if len(status_desc) < 2:
                    continue
                    
                status = status_desc[0].strip()
                desc = status_desc[1].strip()
                
                # Only process fully-qualified emojis
                if status != 'fully-qualified':
                    continue
                
                # Get the emoji character and version
                emoji_parts = desc.split()
                if not emoji_parts:
                    continue
                    
                emoji = emoji_parts[0]  # First part is the emoji
                emojis.append(emoji)
                
            except Exception as e:
                print(f"Error parsing line: {line}")
                continue
    
    return emojis

def render_emoji_to_image(emoji_char, size=64):
    """Render an emoji to a PIL Image."""
    # Create a new image with alpha channel
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    try:
        # Try to find a suitable font that supports emojis
        font_paths = [
            '/System/Library/Fonts/Apple Color Emoji.ttc',  # macOS
            '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',  # Linux
            'C:\\Windows\\Fonts\\seguiemj.ttf'  # Windows
        ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, size // 2)  # Reduced font size
                    break
                except Exception:
                    continue
        
        if font is None:
            return None
        
        # Calculate text size and position to center
        try:
            left, top, right, bottom = draw.textbbox((0, 0), emoji_char, font=font)
            width = right - left
            height = bottom - top
            x = (size - width) / 2 - left
            y = (size - height) / 2 - top
            
            # Draw the emoji
            draw.text((x, y), emoji_char, font=font, embedded_color=True)
            
            # Convert to RGB with white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            
            return background
        except Exception:
            return None
    
    except Exception as e:
        print(f"Error rendering emoji {emoji_char}: {e}")
        return None

def calculate_average_color(image):
    """Calculate the most representative color of an emoji for pixel replacement."""
    if image is None:
        return None
    
    try:
        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Convert image to numpy array
        img_array = np.array(image)
        
        # Get dimensions
        height, width = img_array.shape[:2]
        
        # Create a circular mask to focus on the center (where emoji content usually is)
        y, x = np.ogrid[:height, :width]
        center_y, center_x = height/2, width/2
        radius = min(height, width) * 0.7  # Use 70% of the smallest dimension
        
        # Calculate distance of each pixel from center
        dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        circular_mask = dist_from_center <= radius
        
        # Get alpha channel and create mask for non-transparent pixels
        alpha = img_array[:, :, 3] / 255.0
        valid_mask = (alpha > 0.2) & circular_mask  # Ignore nearly transparent pixels
        
        if not np.any(valid_mask):
            return None
        
        # Get RGB values of valid pixels
        valid_pixels = img_array[valid_mask][:, :3]
        valid_alphas = alpha[valid_mask]
        
        # Weight colors by their alpha value
        weighted_pixels = valid_pixels * valid_alphas[:, np.newaxis]
        
        # Calculate weighted median color
        sorted_indices = np.argsort(valid_alphas)
        cumsum = np.cumsum(valid_alphas[sorted_indices])
        median_idx = np.searchsorted(cumsum, cumsum[-1] / 2)
        median_color = valid_pixels[sorted_indices[median_idx]]
        
        # Convert to hex
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(median_color[0]),
            int(median_color[1]),
            int(median_color[2])
        )
        
        return hex_color
    except Exception:
        return None

def generate_emoji_data(input_file, output_file):
    """Generate emoji data CSV file."""
    print("Generating emoji data...")
    
    # Parse emoji test file
    emojis = parse_emoji_test_file(input_file)
    total = len(emojis)
    print(f"Found {total} emojis in test file")
    
    # Header
    lines = ["Emoji,ASCII Code,Hex Color"]
    processed = 0
    
    # Keep track of used colors to avoid duplicates
    used_colors = {}  # hex_color -> emoji_line
    
    for i, emoji_char in enumerate(emojis, 1):
        try:
            # Get unicode
            unicode_value = str(ord(emoji_char[0]))  # Just use first character for multi-char emojis
                
            # Render and get color
            image = render_emoji_to_image(emoji_char)
            if image is None:
                continue
                
            hex_color = calculate_average_color(image)
            if hex_color is None:
                continue
            
            # Check if color is already used
            if hex_color not in used_colors:
                # Add to CSV
                line = f"{emoji_char},{unicode_value},{hex_color}"
                lines.append(line)
                used_colors[hex_color] = line
                processed += 1
            
            # Progress
            if i % 100 == 0:
                print(f"Processed {i}/{total} emojis ({processed} unique colors)...")
            
        except Exception as e:
            print(f"Error processing emoji {emoji_char}: {e}")
            continue
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\nDone! Generated data for {processed} emojis with unique colors")
    print(f"Filtered out {total - processed} emojis with duplicate colors")
    print(f"Output file: {output_file}")

def validate_emoji_data(file_path):
    """Validate the generated emoji data file."""
    print("\nValidating emoji data file...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("❌ Error: File is empty")
            return False
            
        # Check header
        header = lines[0].strip()
        if header != "Emoji,ASCII Code,Hex Color":
            print("❌ Error: Invalid header format")
            return False
            
        # Check data
        total_lines = len(lines)
        print(f"✓ Found {total_lines-1} emoji entries")
        
        # Sample validation
        sample_size = min(5, total_lines-1)
        print(f"\nValidating {sample_size} random entries:")
        
        import random
        sample_lines = random.sample(lines[1:], sample_size)
        
        for line in sample_lines:
            line = line.strip()
            parts = line.split(',')
            
            if len(parts) != 3:
                print(f"❌ Invalid format: {line}")
                continue
                
            emoji, ascii_code, hex_color = parts
            
            # Validate emoji
            if not emoji:
                print(f"❌ Empty emoji in line: {line}")
                continue
                
            # Validate ASCII code
            try:
                ascii_val = int(ascii_code)
                if ascii_val < 0:
                    print(f"❌ Invalid ASCII code in line: {line}")
                    continue
            except ValueError:
                print(f"❌ Non-numeric ASCII code in line: {line}")
                continue
                
            # Validate hex color
            if not (hex_color.startswith('#') and len(hex_color) == 7 and 
                   all(c in '0123456789abcdefABCDEF' for c in hex_color[1:])):
                print(f"❌ Invalid hex color in line: {line}")
                continue
                
            print(f"✓ Valid entry: {line}")
        
        # Check for duplicates
        unique_emojis = set()
        duplicate_count = 0
        for line in lines[1:]:
            emoji = line.strip().split(',')[0]
            if emoji in unique_emojis:
                duplicate_count += 1
            unique_emojis.add(emoji)
            
        if duplicate_count:
            print(f"\n⚠️ Found {duplicate_count} duplicate emojis")
        else:
            print("\n✓ No duplicate emojis found")
            
        # Calculate average color to ensure variety
        hex_colors = [line.strip().split(',')[2] for line in lines[1:]]
        rgb_values = []
        for hex_color in hex_colors:
            try:
                r = int(hex_color[1:3], 16)
                g = int(hex_color[3:5], 16)
                b = int(hex_color[5:7], 16)
                rgb_values.append((r, g, b))
            except ValueError:
                continue
                
        if rgb_values:
            avg_r = sum(r for r,_,_ in rgb_values) / len(rgb_values)
            avg_g = sum(g for _,g,_ in rgb_values) / len(rgb_values)
            avg_b = sum(b for _,_,b in rgb_values) / len(rgb_values)
            
            # Check if colors are too similar (might indicate rendering issues)
            r_var = sum((r - avg_r) ** 2 for r,_,_ in rgb_values) / len(rgb_values)
            g_var = sum((g - avg_g) ** 2 for _,g,_ in rgb_values) / len(rgb_values)
            b_var = sum((b - avg_b) ** 2 for _,_,b in rgb_values) / len(rgb_values)
            
            if r_var < 100 and g_var < 100 and b_var < 100:
                print("\n⚠️ Warning: Low color variance - colors might be too similar")
            else:
                print("\n✓ Good color variance across emojis")
        
        print("\nValidation complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error validating file: {e}")
        return False

if __name__ == "__main__":
    # Get the directory of the script
    script_dir = Path(__file__).parent
    
    # Input and output file paths
    input_file = script_dir / 'emoji-test.txt'
    output_file = script_dir / 'emoji_data.csv'
    
    # Generate the data
    generate_emoji_data(input_file, output_file)
    
    # Validate the generated file
    validate_emoji_data(output_file)
