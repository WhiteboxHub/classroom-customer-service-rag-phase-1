"""
conftest.py
Shared pytest fixtures and configuration for all unit tests.

Adds the backend/ directory to sys.path so that 'app.*' imports resolve
without installing the package in editable mode first. This keeps the
test runner simple — just `pytest tests/` from the project root.
"""
import sys
import os

# Make 'app' importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
