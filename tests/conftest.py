"""
Configuration file for pytest.
"""

import sys
import os

# Add the project root to Python path so we can import our modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import pytest

@pytest.fixture(scope="session")
def project_root_dir():
    """Provide the project root directory path."""
    return project_root
