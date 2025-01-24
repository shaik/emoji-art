import os

class Config:
    DEBUG = True
    SECRET_KEY = 'your-secret-key-here'  # Change this in production
    PORT = 5000
    HOST = '127.0.0.1'

    # CSV Configuration
    EMOJI_CSV_PATH = os.path.join('data', 'emoji_data.csv')
    EMOJI_CSV_HEADERS = ['Emoji', 'ASCII Code', 'Hex Color']
    
    # Color validation
    HEX_COLOR_PATTERN = r'^#[0-9A-Fa-f]{6}$'
