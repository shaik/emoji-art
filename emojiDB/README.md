# Emoji Data Generator

This script generates a CSV file containing emoji data including the emoji character, its Unicode value, and average color.

## Requirements

- Python 3.8+
- Required packages listed in `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Simply run the script:

```bash
python generate_emoji_data.py
```

The script will:
1. Get a list of all valid Unicode emojis
2. Render each emoji using system fonts
3. Calculate the average color for each emoji
4. Generate a CSV file in the format:
   ```
   Emoji,ASCII Code,Hex Color
   🟩,129001,#37c136
   🟦,128998,#3b80f5
   ```

The output file will be created at `../static/data/emoji_data.csv`

## Notes

- The script requires a system font that supports emoji rendering
- Supported font paths:
  - macOS: `/System/Library/Fonts/Apple Color Emoji.ttc`
  - Linux: `/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf`
  - Windows: `C:\Windows\Fonts\seguiemj.ttf`
- The script will skip emojis that cannot be rendered
- Progress is displayed during generation
