from flask import Flask, render_template, request, jsonify, send_from_directory
from config.config import Config
import logging
from logging.handlers import RotatingFileHandler
import os
from werkzeug.utils import secure_filename
import time
from utils.csv_parser import parse_emoji_csv, CSVValidationError
from utils.build_manager import BuildManager
from utils.color_utils import color_distance
from PIL import Image
from typing import List, Dict
import re

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Global variable to store emoji data
    app.emoji_db = []

    # Configure upload settings
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB limit

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Configure logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/emojiart.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('EmojiArt startup')

    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def load_emoji_data():
        """Load emoji data from CSV file."""
        try:
            app.logger.info(f"Loading emoji data from {Config.EMOJI_CSV_PATH}")
            app.emoji_db = parse_emoji_csv()
            app.logger.info(f"Successfully loaded {len(app.emoji_db)} emoji entries")
        except (FileNotFoundError, CSVValidationError) as e:
            app.logger.error(f"Failed to load emoji data: {str(e)}")
            app.emoji_db = []  # Initialize with empty list on error
        except Exception as e:
            app.logger.error(f"Unexpected error loading emoji data: {str(e)}")
            app.emoji_db = []

    @app.route('/')
    def index():
        build_info = BuildManager.get_build_info()
        app.logger.info('Homepage accessed')
        app.logger.info(f'Build info: {build_info}')
        return render_template('index.html', build_info=build_info, default_width=Config.DEFAULT_WIDTH)

    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            app.logger.warning('No file part in request')
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            app.logger.warning('No selected file')
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            app.logger.warning(f'Invalid file type: {file.filename}')
            return jsonify({'error': 'Invalid file type. Allowed types: png, jpg, jpeg'}), 400
        
        try:
            if file and allowed_file(file.filename):
                # Secure the filename and add timestamp
                filename = secure_filename(file.filename)
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                app.logger.info(f'File uploaded successfully: {filename}')
                return jsonify({
                    'message': 'File uploaded successfully',
                    'filename': filename
                }), 200
                
        except Exception as e:
            app.logger.error(f'Error uploading file: {str(e)}')
            return jsonify({'error': 'Error uploading file'}), 500

    @app.route('/emojis', methods=['GET'])
    def get_emojis():
        """Return the list of loaded emojis."""
        return jsonify(app.emoji_db)

    @app.route('/get-emojis')
    def get_emojis_filtered():
        """Get emojis based on name and color filters."""
        name = request.args.get('name', '')
        color = request.args.get('color', '')

        try:
            filtered_emojis = app.emoji_db
            if name:
                filtered_emojis = [e for e in filtered_emojis if name.lower() in e['Emoji'].lower()]
            if color:
                if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid color format. Use #RRGGBB format.'
                    }), 400
                filtered_emojis = [e for e in filtered_emojis if color_distance(e['Hex Color'], color) < 100]

            return jsonify({
                'status': 'success',
                'data': filtered_emojis
            })
        except Exception as e:
            app.logger.error(f'Error processing request: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500

    def parse_aspect_ratio(ratio_str):
        """Parse aspect ratio string in format 'width:height' to float."""
        try:
            if ':' in ratio_str:
                width, height = map(float, ratio_str.split(':'))
                return width / height
            return float(ratio_str)
        except (ValueError, ZeroDivisionError):
            raise ValueError('Invalid aspect ratio format. Use width:height (e.g., 16:9) or decimal (e.g., 1.78)')

    def process_image_to_grid(image, grid_size, aspect_ratio_str):
        """Process the image and return a grid of emoji data."""
        try:
            # Parse aspect ratio
            try:
                aspect_ratio = parse_aspect_ratio(aspect_ratio_str)
            except ValueError:
                app.logger.warning(f'Invalid aspect ratio {aspect_ratio_str}, using 1:1')
                aspect_ratio = 1.0

            # Resize image to grid size while maintaining aspect ratio
            width, height = image.size
            if width / height > aspect_ratio:
                new_width = int(height * aspect_ratio)
                new_height = height
            else:
                new_width = width
                new_height = int(width / aspect_ratio)
            
            image = image.resize((grid_size, int(grid_size / aspect_ratio)))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Create grid
            grid = []
            for y in range(image.height):
                row = []
                for x in range(image.width):
                    # Get pixel color
                    r, g, b = image.getpixel((x, y))
                    pixel_color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # Find closest emoji
                    closest_emoji = None
                    min_distance = float('inf')
                    
                    for emoji_data in app.emoji_db:
                        emoji_color = emoji_data['Hex Color']
                        distance = color_distance(pixel_color, emoji_color)
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_emoji = emoji_data
                    
                    if closest_emoji:
                        row.append({
                            'emoji': closest_emoji['Emoji'],
                            'color': closest_emoji['Hex Color']
                        })
                    else:
                        # Fallback emoji if no match found
                        row.append({
                            'emoji': '⬜',
                            'color': '#FFFFFF'
                        })
                
                grid.append(row)
            
            return grid
            
        except Exception as e:
            app.logger.error(f"Error processing image: {str(e)}")
            raise

    @app.route('/process-image', methods=['POST'])
    def process_image():
        """Process uploaded image and convert to emoji art."""
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided'
            }), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No selected file'
            }), 400

        # Validate required parameters
        grid_size = request.form.get('gridSize')
        aspect_ratio = request.form.get('aspectRatio')
        
        if not grid_size:
            return jsonify({
                'status': 'error',
                'message': 'gridSize parameter is required'
            }), 400
        
        if not aspect_ratio:
            return jsonify({
                'status': 'error',
                'message': 'aspectRatio parameter is required'
            }), 400

        try:
            grid_size = int(grid_size)
            if grid_size <= 0:
                return jsonify({
                    'status': 'error',
                    'message': 'Grid size must be positive'
                }), 400
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid grid size format'
            }), 400

        try:
            # Process the image
            image = Image.open(file)
            processed_grid = process_image_to_grid(image, grid_size, aspect_ratio)
            
            return jsonify({
                'status': 'success',
                'grid': processed_grid
            })
        except ValueError as e:
            app.logger.error(f'Error processing image: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        except Exception as e:
            app.logger.error(f'Error processing image: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': 'Error processing image'
            }), 500

    @app.route('/data/emoji_data.csv')
    def serve_emoji_data():
        try:
            return send_from_directory(os.path.join(os.path.dirname(__file__), 'data'), 'emoji_data.csv', mimetype='text/csv')
        except Exception as e:
            app.logger.error(f'Error serving emoji data: {str(e)}')
            return jsonify({'error': 'Error serving emoji data'}), 500

    # Load emoji data during app initialization
    load_emoji_data()

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Load emoji data when the app starts
    app.emoji_db = parse_emoji_csv()
    # Run the app on all network interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)
