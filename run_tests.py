#!/usr/bin/env python3
"""
Test Runner Script

This script runs all tests for the XML RESTful API project.
It provides options to run different test suites and generate coverage reports.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_command(command, description):
    """Run a command and print the result"""
    print(f"\n{'='*60}")
    print(f" {description}")
    print(f"{'='*60}\n")

    result = subprocess.run(command, shell=True)
    return result.returncode == 0


def run_all_tests():
    """Run all tests"""
    print("\nRunning all tests...")
    return run_command(
        "pytest tests/ -v",
        "Running All Tests"
    )


def run_api_tests():
    """Run API tests only"""
    return run_command(
        "pytest tests/test_api.py -v",
        "Running API Tests"
    )


def run_utils_tests():
    """Run XML utilities tests only"""
    return run_command(
        "pytest tests/test_xml_utils.py -v",
        "Running XML Utilities Tests"
    )


def run_with_coverage():
    """Run tests with coverage report"""
    print("\nRunning tests with coverage...")

    # Run tests with coverage
    success = run_command(
        "pytest tests/ --cov=src --cov-report=term-missing --cov-report=html",
        "Running Tests with Coverage"
    )

    if success:
        print("\n✓ Coverage report generated in htmlcov/index.html")

    return success


def run_specific_test(test_name):
    """Run a specific test by name"""
    return run_command(
        f"pytest tests/ -k {test_name} -v",
        f"Running Test: {test_name}"
    )


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\nChecking dependencies...")

    try:
        import pytest
        import flask
        import lxml
        print("✓ All required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False


def lint_code():
    """Run linting on the source code"""
    print("\nRunning code linting...")

    # Check if flake8 is installed
    try:
        import flake8
        return run_command(
            "flake8 src/ tests/ --max-line-length=120 --exclude=__pycache__",
            "Code Linting with Flake8"
        )
    except ImportError:
        print("Flake8 not installed. Skipping linting.")
        print("Install with: pip install flake8")
        return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Run tests for XML RESTful API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py              # Run all tests
  python run_tests.py --api        # Run API tests only
  python run_tests.py --utils      # Run utilities tests only
  python run_tests.py --coverage   # Run with coverage report
  python run_tests.py -k test_name # Run specific test
  python run_tests.py --lint       # Run code linting
        """
    )

    parser.add_argument(
        "--api",
        action="store_true",
        help="Run API tests only"
    )

    parser.add_argument(
        "--utils",
        action="store_true",
        help="Run XML utilities tests only"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )

    parser.add_argument(
        "-k",
        "--test",
        type=str,
        help="Run specific test by name"
    )

    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run code linting"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests, coverage, and linting"
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print(" XML RESTful API - Test Runner")
    print("="*60)

    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)

    success = True

    # Run requested tests
    if args.test:
        success &= run_specific_test(args.test)
    elif args.api:
        success &= run_api_tests()
    elif args.utils:
        success &= run_utils_tests()
    elif args.coverage:
        success &= run_with_coverage()
    elif args.lint:
        success &= lint_code()
    elif args.all:
        success &= run_all_tests()
        success &= run_with_coverage()
        success &= lint_code()
    else:
        # Default: run all tests
        success &= run_all_tests()

    # Print summary
    print("\n" + "="*60)
    if success:
        print(" ✓ All tests passed successfully!")
    else:
        print(" ✗ Some tests failed!")
    print("="*60 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
