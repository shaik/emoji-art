import os
import logging
import json

def test_index_route(client):
    """Test that the index route returns 200 and contains welcome message."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Transform your images into emoji masterpieces' in response.data

def test_config_values(app):
    """Test that config values are set correctly."""
    assert app.config['DEBUG'] is True
    assert app.config['PORT'] == 5000
    assert app.config['HOST'] == '127.0.0.1'
    assert 'SECRET_KEY' in app.config

def test_404_page(client):
    """Test that non-existent routes return 404."""
    response = client.get('/non-existent-page')
    assert response.status_code == 404

def test_static_files_exist():
    """Test that required static files exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert os.path.exists(os.path.join(base_dir, 'static', 'css', 'styles.css'))
    assert os.path.exists(os.path.join(base_dir, 'static', 'js', 'main.js'))

def test_static_files_served(client):
    """Test that static files are properly served."""
    css_response = client.get('/static/css/styles.css')
    assert css_response.status_code == 200
    assert css_response.content_type == 'text/css; charset=utf-8'

    js_response = client.get('/static/js/main.js')
    assert js_response.status_code == 200
    assert js_response.content_type == 'application/javascript; charset=utf-8'

def test_logging_configuration(app):
    """Test that logging is properly configured."""
    assert app.logger.level == logging.INFO or app.logger.level == logging.DEBUG
    
    # Check if log directory exists when not in debug mode
    if not app.debug:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(base_dir, 'logs')
        assert os.path.exists(log_dir)

def test_required_files_exist():
    """Test that all required project files exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_files = [
        'README.md',
        '.env.example',
        '.gitignore',
        'requirements.txt',
        'app.py',
        'config/config.py',
        'templates/index.html'
    ]
    
    for file_path in required_files:
        assert os.path.exists(os.path.join(base_dir, file_path))

def test_build_info_in_template(client):
    """Test that build info is displayed in the template."""
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode()
    
    # Check for build number element
    assert 'class="build-number"' in html
    assert 'Build #' in html
    
    # Check for build date
    assert 'class="build-date"' in html
    assert 'Last updated:' in html

def test_build_info_increments(client):
    """Test that build info increments correctly."""
    # Get initial build number
    response = client.get('/')
    html = response.data.decode()
    
    # Extract build number from the build-number span
    import re
    build_pattern = r'class="build-number">(\d+)'
    match = re.search(build_pattern, html)
    assert match is not None, f"Build number not found in HTML. Pattern: {build_pattern}"
    initial_build = int(match.group(1))
    
    # Increment build
    from utils.build_manager import BuildManager
    BuildManager.increment_build()
    
    # Check new build number
    response = client.get('/')
    html = response.data.decode()
    new_build = int(re.search(build_pattern, html).group(1))
    assert new_build == initial_build + 1

def test_get_emojis_no_filter(client):
    """Test getting all emojis without filters."""
    response = client.get('/get-emojis')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'data' in result
    assert isinstance(result['data'], list)

def test_get_emojis_name_filter(client):
    """Test filtering emojis by name."""
    response = client.get('/get-emojis?name=smile')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'data' in result
    assert isinstance(result['data'], list)

def test_get_emojis_color_filter(client):
    """Test filtering emojis by color."""
    response = client.get('/get-emojis?color=#FF0000')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'data' in result
    assert isinstance(result['data'], list)

def test_get_emojis_invalid_color(client):
    """Test handling invalid color format."""
    response = client.get('/get-emojis?color=invalid')
    assert response.status_code == 400
    result = json.loads(response.data)
    assert 'status' in result
    assert result['status'] == 'error'

def test_get_emojis_combined_filters(client):
    """Test combining name and color filters."""
    response = client.get('/get-emojis?name=heart&color=#FF0000')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'data' in result
    assert isinstance(result['data'], list)

def test_get_emojis_no_matches(client):
    """Test response when no emojis match the filters."""
    response = client.get('/get-emojis?name=nonexistent')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'data' in result
    assert isinstance(result['data'], list)
    assert len(result['data']) == 0
