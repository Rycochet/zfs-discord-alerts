#!/bin/bash

# ZFS Discord Alerts - Test Runner
# This script runs the comprehensive test suite for main.py

echo "=========================================="
echo "ZFS Discord Alerts - Test Suite"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python Version: $PYTHON_VERSION"
echo ""

# Install test dependencies if needed
echo "Checking test dependencies..."
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Note: pyyaml not installed - YAML validation tests will be skipped"
fi
echo ""

# Run the tests
echo "Running test suite..."
echo "=========================================="
echo ""

python3 -m unittest test_main.py -v

TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed (exit code: $TEST_EXIT_CODE)"
fi
echo "=========================================="

exit $TEST_EXIT_CODE