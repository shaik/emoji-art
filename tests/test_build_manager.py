import pytest
import os
import json
from utils.build_manager import BuildManager
from datetime import datetime

@pytest.fixture
def temp_build_file(tmp_path):
    """Create a temporary build file for testing."""
    build_file = tmp_path / "build.json"
    original_build_file = BuildManager.BUILD_FILE
    BuildManager.BUILD_FILE = str(build_file)
    
    yield build_file
    
    # Restore original build file path
    BuildManager.BUILD_FILE = original_build_file

def test_get_build_info_new_file(temp_build_file):
    """Test getting build info when file doesn't exist."""
    build_info = BuildManager.get_build_info()
    assert build_info["build_number"] == 1
    assert "last_updated" in build_info

def test_get_build_info_existing_file(temp_build_file):
    """Test getting build info from existing file."""
    test_data = {
        "build_number": 42,
        "last_updated": "2025-01-24T11:48:37+02:00"
    }
    with open(temp_build_file, 'w') as f:
        json.dump(test_data, f)
    
    build_info = BuildManager.get_build_info()
    assert build_info["build_number"] == 42
    assert build_info["last_updated"] == "2025-01-24T11:48:37+02:00"

def test_increment_build(temp_build_file):
    """Test incrementing build number."""
    # Initial build info
    initial_info = BuildManager.get_build_info()
    initial_number = initial_info["build_number"]
    
    # Increment build
    new_info = BuildManager.increment_build()
    assert new_info["build_number"] == initial_number + 1
    
    # Verify file was updated
    with open(temp_build_file, 'r') as f:
        saved_info = json.load(f)
    assert saved_info["build_number"] == initial_number + 1

def test_get_build_info_invalid_file(temp_build_file):
    """Test getting build info when file is invalid."""
    # Write invalid JSON
    with open(temp_build_file, 'w') as f:
        f.write("invalid json")
    
    build_info = BuildManager.get_build_info()
    assert build_info["build_number"] == 1
    assert "last_updated" in build_info

def test_multiple_increments(temp_build_file):
    """Test multiple build increments."""
    initial_info = BuildManager.get_build_info()
    initial_number = initial_info["build_number"]
    
    # Increment multiple times
    for i in range(3):
        new_info = BuildManager.increment_build()
        assert new_info["build_number"] == initial_number + i + 1
        
    # Verify final state
    final_info = BuildManager.get_build_info()
    assert final_info["build_number"] == initial_number + 3
