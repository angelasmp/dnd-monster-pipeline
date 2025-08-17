#!/bin/bash
# Run unit tests for D&D Monster Pipeline

echo "🧪 Running D&D Monster Pipeline Unit Tests"
echo "==========================================="
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "📋 Running all tests..."
echo ""

# Run tests with verbose output
pytest tests/ -v --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed successfully!"
    echo ""
    echo "📊 Test Coverage:"
    echo "  • Models validation (Pydantic)"
    echo "  • API client functionality"
    echo "  • Task functions"
    echo "  • Integration tests"
    echo "  • Error handling"
else
    echo ""
    echo "❌ Some tests failed. Check output above."
    exit 1
fi

echo ""
echo "🎯 Unit tests complete!"
