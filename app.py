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
        return render_template('index.html', build_info=build_info)

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
        """
        Get emojis with optional filtering by name and color.
        Query parameters:
        - name: Filter emojis by name (case-insensitive substring match)
        - color: Filter emojis by closest color match (hex format: #RRGGBB)
        """
        name_filter = request.args.get('name', '').lower()
        color_filter = request.args.get('color', '')
        
        app.logger.info(f'/get-emojis accessed with parameters: name={name_filter}, color={color_filter}')
        
        try:
            # Start with all emojis
            filtered_emojis = app.emoji_db
            
            # Apply name filter if provided
            if name_filter:
                filtered_emojis = [
                    emoji for emoji in filtered_emojis
                    if name_filter in emoji['name'].lower()
                ]
            
            # Apply color filter if provided
            if color_filter:
                # Validate color format
                if not color_filter.startswith('#') or len(color_filter) != 7:
                    app.logger.error(f"Invalid color format: {color_filter}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid color format. Use #RRGGBB format.'
                    }), 400
                
                # Calculate color distances and sort by closest match
                try:
                    emoji_distances = [
                        (emoji, color_distance(color_filter, emoji['color']))
                        for emoji in filtered_emojis
                    ]
                    # Filter out None distances (invalid colors) and sort by distance
                    valid_distances = [
                        (emoji, dist) for emoji, dist in emoji_distances
                        if dist is not None
                    ]
                    if valid_distances:
                        filtered_emojis = [
                            emoji for emoji, _ in sorted(valid_distances, key=lambda x: x[1])
                        ]
                    else:
                        app.logger.error("No valid color matches found")
                        filtered_emojis = []
                except Exception as e:
                    app.logger.error(f"Error calculating color distances: {e}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Error processing color filter'
                    }), 400
            
            # Log results
            result_count = len(filtered_emojis)
            if result_count == 0:
                app.logger.warning(
                    f"No matching emojis found for filters: name={name_filter}, color={color_filter}"
                )
            else:
                app.logger.info(f"Found {result_count} matching emojis")
                
            if app.debug:
                app.logger.debug(f"Filtered emojis: {filtered_emojis}")
            
            return jsonify({
                'status': 'success',
                'data': filtered_emojis
            })
            
        except Exception as e:
            app.logger.error(f"Error processing request: {e}")
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500

    def process_image(image_path: str, grid_size: int = 32) -> List[List[Dict[str, str]]]:
        """Process the image and return a grid of emoji data."""
        try:
            # Open and process image
            with Image.open(image_path) as img:
                # Resize image to grid size while maintaining aspect ratio
                img.thumbnail((grid_size, grid_size))
                width, height = img.size
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create grid
                grid = []
                for y in range(height):
                    row = []
                    for x in range(width):
                        # Get pixel color
                        r, g, b = img.getpixel((x, y))
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
    def process_image_endpoint():
        """Process uploaded image and return grid data."""
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image = request.files['image']
        if not image.filename:
            return jsonify({'error': 'No image selected'}), 400
        
        # Validate grid size
        grid_size = request.form.get('gridSize')
        if not grid_size or not grid_size.isdigit() or int(grid_size) <= 0:
            return jsonify({'error': 'Invalid grid size'}), 400
        
        try:
            # Save image to file
            filename = secure_filename(image.filename)
            timestamp = str(int(time.time()))
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(file_path)
            
            # Process image
            grid = process_image(file_path, int(grid_size))
            
            return jsonify({
                'grid': grid
            })
        
        except Exception as e:
            app.logger.error(f'Error processing image: {str(e)}')
            return jsonify({'error': 'Error processing image'}), 500

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
