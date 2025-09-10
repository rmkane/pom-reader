#!/bin/bash
# Install development dependencies for POM Reader

set -e

echo "Installing POM Reader in development mode..."

# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

echo "Installation complete!"
echo ""
echo "You can now:"
echo "  - Run tests: pytest"
echo "  - Run the example: python example.py"
echo "  - Use the CLI: pom-reader analyze resources/pom.xml"
echo "  - Format code: black src/ tests/"
echo "  - Type check: mypy src/"
