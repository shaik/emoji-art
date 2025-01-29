import pytest
import os
import json
from io import BytesIO
from PIL import Image
from app import app

@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def create_test_image():
    """Create a test image for testing."""
    img = Image.new('RGB', (100, 100), color='blue')
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

def test_process_image_endpoint(client):
    """Test the image processing endpoint."""
    img_io = create_test_image()
    data = {
        'image': (img_io, 'test.png'),
        'gridSize': '16',
        'aspectRatio': '1:1'
    }
    response = client.post('/process-image',
                         content_type='multipart/form-data',
                         data=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'grid' in result
    assert isinstance(result['grid'], list)
    assert len(result['grid']) > 0
    assert isinstance(result['grid'][0], list)

def test_invalid_image_format(client):
    """Test handling of invalid image format."""
    data = {
        'image': (BytesIO(b'not an image'), 'test.txt'),
        'gridSize': '16',
        'aspectRatio': '1:1'
    }
    response = client.post('/process-image',
                         content_type='multipart/form-data',
                         data=data)

    assert response.status_code == 500  # Server returns 500 for unprocessable images
    result = json.loads(response.data)
    assert result['status'] == 'error'
    assert 'message' in result

def test_missing_parameters(client):
    """Test handling of missing parameters."""
    # Test missing gridSize
    img_io = create_test_image()
    data = {
        'image': (img_io, 'test.png'),
        'aspectRatio': '1:1'
    }
    response = client.post('/process-image',
                         content_type='multipart/form-data',
                         data=data)

    assert response.status_code == 400  # Missing required parameter
    result = json.loads(response.data)
    assert result['status'] == 'error'
    assert 'message' in result

    # Test missing aspectRatio
    img_io = create_test_image()  # Create new image for second test
    data = {
        'image': (img_io, 'test.png'),
        'gridSize': '16'
    }
    response = client.post('/process-image',
                         content_type='multipart/form-data',
                         data=data)

    assert response.status_code == 400  # Missing required parameter
    result = json.loads(response.data)
    assert result['status'] == 'error'
    assert 'message' in result

def test_invalid_grid_size(client):
    """Test handling of invalid grid size."""
    img_io = create_test_image()
    data = {
        'image': (img_io, 'test.png'),
        'gridSize': '0',  # Invalid grid size
        'aspectRatio': '1:1'
    }
    response = client.post('/process-image',
                         content_type='multipart/form-data',
                         data=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['status'] == 'error'
    assert 'message' in result

def test_invalid_aspect_ratio(client):
    """Test handling of invalid aspect ratio."""
    img_io = create_test_image()
    data = {
        'image': (img_io, 'test.png'),
        'gridSize': '16',
        'aspectRatio': 'invalid'
    }
    response = client.post('/process-image',
                         content_type='multipart/form-data',
                         data=data)

    assert response.status_code == 200  # Falls back to default aspect ratio
    result = json.loads(response.data)
    assert 'grid' in result

def test_large_image_processing(client):
    """Test processing of large images."""
    large_img = Image.new('RGB', (2000, 2000), color='blue')
    img_io = BytesIO()
    large_img.save(img_io, 'PNG')
    img_io.seek(0)

    data = {
        'image': (img_io, 'large.png'),
        'gridSize': '16',
        'aspectRatio': '1:1'
    }
    response = client.post('/process-image',
                         content_type='multipart/form-data',
                         data=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'grid' in result
    assert isinstance(result['grid'], list)
    assert len(result['grid']) > 0

def test_different_aspect_ratios(client):
    """Test processing with different aspect ratios."""
    aspect_ratios = ['1:1', '16:9', '4:3']

    for ratio in aspect_ratios:
        img_io = create_test_image()
        data = {
            'image': (img_io, 'test.png'),
            'gridSize': '16',
            'aspectRatio': ratio
        }
        response = client.post('/process-image',
                             content_type='multipart/form-data',
                             data=data)

        assert response.status_code == 200
        result = json.loads(response.data)
        assert 'grid' in result
        assert isinstance(result['grid'], list)
        assert len(result['grid']) > 0

def test_different_grid_sizes(client):
    """Test processing with different grid sizes."""
    grid_sizes = ['8', '16', '32']

    for size in grid_sizes:
        img_io = create_test_image()
        data = {
            'image': (img_io, 'test.png'),
            'gridSize': size,
            'aspectRatio': '1:1'
        }
        response = client.post('/process-image',
                             content_type='multipart/form-data',
                             data=data)

        assert response.status_code == 200
        result = json.loads(response.data)
        assert 'grid' in result
        assert isinstance(result['grid'], list)
        assert len(result['grid']) > 0
