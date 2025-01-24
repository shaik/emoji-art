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

    @app.route('/process-image', methods=['POST'])
    def process_image():
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
        
        # Validate aspect ratio
        aspect_ratio = request.form.get('aspectRatio')
        if not aspect_ratio or ':' not in aspect_ratio:
            return jsonify({'error': 'Invalid aspect ratio'}), 400
        
        try:
            # Check if file is an image
            try:
                img = Image.open(image)
            except Exception as e:
                app.logger.error(f'Invalid image format: {str(e)}')
                return jsonify({'error': 'Invalid image format'}), 400
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate dimensions based on aspect ratio
            width, height = map(int, aspect_ratio.split(':'))
            max_dimension = 800  # Maximum dimension
            
            if width > height:
                new_width = max_dimension
                new_height = int(max_dimension * (height / width))
            else:
                new_height = max_dimension
                new_width = int(max_dimension * (width / height))
            
            # Resize image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create grid
            grid_size = int(grid_size)
            cell_width = new_width // grid_size
            cell_height = new_height // grid_size
            
            grid = []
            for y in range(grid_size):
                row = []
                for x in range(grid_size):
                    # Get cell region
                    left = x * cell_width
                    top = y * cell_height
                    right = left + cell_width
                    bottom = top + cell_height
                    
                    # Get average color of cell
                    cell = img.crop((left, top, right, bottom))
                    pixels = list(cell.getdata())
                    avg_color = [
                        sum(p[0] for p in pixels) // len(pixels),
                        sum(p[1] for p in pixels) // len(pixels),
                        sum(p[2] for p in pixels) // len(pixels)
                    ]
                    
                    # Convert to hex
                    hex_color = '#{:02x}{:02x}{:02x}'.format(*avg_color)
                    
                    # Add to grid
                    row.append({
                        'color': hex_color,
                        'position': {'x': x, 'y': y}
                    })
                grid.append(row)
            
            return jsonify({
                'grid': grid,
                'dimensions': {
                    'width': new_width,
                    'height': new_height
                }
            })
        
        except Exception as e:
            app.logger.error(f'Error processing image: {str(e)}')
            return jsonify({'error': 'Error processing image'}), 500

    @app.route('/data/emoji_data.csv')
    def serve_emoji_data():
        try:
            return send_from_directory(os.path.join(os.path.dirname(__file__), 'data'), 'emoji_data..csv', mimetype='text/csv')
        except Exception as e:
            app.logger.error(f'Error serving emoji data: {str(e)}')
            return jsonify({'error': 'Error serving emoji data'}), 500

    # Load emoji data during app initialization
    load_emoji_data()

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
