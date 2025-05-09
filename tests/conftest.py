import pytest
from unittest.mock import MagicMock
import os
import sys

# Menambahkan root directory ke Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_db():
    """Fixture untuk mock database"""
    return MagicMock()

@pytest.fixture
def mock_response():
    """Fixture untuk mock response"""
    return MagicMock() 