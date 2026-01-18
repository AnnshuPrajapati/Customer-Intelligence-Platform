#!/usr/bin/env python3
"""
Customer Intelligence Platform - Demo Mode
Runs the complete platform with mock AI responses (no API key required!)
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Run the platform in demo mode."""
    # Force mock mode
    os.environ["MOCK_MODE"] = "true"

    print("🚀 Customer Intelligence Platform - DEMO MODE")
    print("=" * 50)
    print("🎭 Running with realistic mock AI responses")
    print("💡 This demonstrates the full workflow for FREE!")
    print("📊 You'll see: Data Collection → Sentiment → Patterns → Opportunities → Strategy")
    print("=" * 50)
    print()

    # Import and run main
    from src.main import main as run_main

    # Run with default parameters
    sys.argv = ["demo.py", "--company", "TechCorp", "--product", "CloudFlow SaaS"]

    return run_main()

if __name__ == "__main__":
    exit(main())

