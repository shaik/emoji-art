import os
import pytest
from io import BytesIO
from PIL import Image
from werkzeug.exceptions import RequestEntityTooLarge

def create_test_image(size=(100, 100)):
    """Create a test image for upload testing."""
    file = BytesIO()
    image = Image.new('RGB', size, color='red')
    image.save(file, 'png')
    file.seek(0)
    return file

def test_upload_route_exists(client):
    """Test that upload route exists and accepts POST requests."""
    response = client.post('/upload')
    assert response.status_code != 404, "Upload route should exist"

def test_upload_no_file(client):
    """Test upload endpoint with no file."""
    response = client.post('/upload')
    assert response.status_code == 400
    assert b'No file part' in response.data

def test_upload_empty_file(client):
    """Test upload endpoint with empty file."""
    data = {'file': (BytesIO(), '')}
    response = client.post('/upload', data=data)
    assert response.status_code == 400
    assert b'No selected file' in response.data

def test_upload_invalid_file_type(client):
    """Test upload endpoint with invalid file type."""
    data = {
        'file': (BytesIO(b'not an image'), 'test.txt')
    }
    response = client.post('/upload', data=data)
    assert response.status_code == 400
    assert b'Invalid file type' in response.data

def test_upload_valid_file(client, tmp_path):
    """Test upload endpoint with valid file."""
    # Create a test image
    test_file = create_test_image()
    data = {
        'file': (test_file, 'test.png')
    }
    
    response = client.post('/upload', data=data)
    assert response.status_code == 200
    assert b'File uploaded successfully' in response.data

def test_upload_large_file(client):
    """Test upload endpoint with file larger than 10MB."""
    # Create a large file (>10MB)
    large_file = BytesIO(b'0' * (10 * 1024 * 1024 + 1))
    data = {
        'file': (large_file, 'large.png')
    }
    
    response = client.post('/upload', data=data)
    assert response.status_code == 413  # Request Entity Too Large

@pytest.fixture
def cleanup_uploads():
    """Fixture to clean up uploaded files after tests."""
    yield
    upload_dir = 'uploads'
    if os.path.exists(upload_dir):
        for file in os.listdir(upload_dir):
            os.remove(os.path.join(upload_dir, file))
        os.rmdir(upload_dir)
