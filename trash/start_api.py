#!/usr/bin/env python3
"""
API Startup Script

This script starts the XML RESTful API server with proper configuration.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the src directory to the Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")

    missing_deps = []

    try:
        import flask
    except ImportError:
        missing_deps.append('flask')

    try:
        import lxml
    except ImportError:
        missing_deps.append('lxml')

    try:
        import flask_cors
    except ImportError:
        missing_deps.append('flask-cors')

    if missing_deps:
        print(f"\n✗ Missing dependencies: {', '.join(missing_deps)}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False

    print("✓ All dependencies are installed")
    return True


def ensure_directories():
    """Ensure required directories exist"""
    data_dir = PROJECT_ROOT / 'data'
    xml_dir = data_dir / 'xml_files'
    xslt_dir = data_dir / 'xslt_files'

    for directory in [data_dir, xml_dir, xslt_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    print("✓ Data directories ready")


def main():
    """Main function to start the API server"""
    parser = argparse.ArgumentParser(
        description="Start the XML RESTful API server"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode"
    )

    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode (disables debug)"
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print(" XML RESTful API - Server Startup")
    print("="*60 + "\n")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Ensure directories exist
    ensure_directories()

    # Import the app
    try:
        from app import app
    except ImportError as e:
        print(f"\n✗ Error importing app: {e}")
        sys.exit(1)

    # Configure the app
    if args.production:
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        print("✓ Running in production mode")
    else:
        app.config['DEBUG'] = args.debug or True
        print(f"✓ Debug mode: {'enabled' if app.config['DEBUG'] else 'disabled'}")

    # Print startup information
    print(f"\n✓ Starting server on http://{args.host}:{args.port}")
    print(f"✓ API endpoints available at http://{args.host}:{args.port}/api")
    print("\nPress CTRL+C to stop the server\n")

    # Print some useful endpoints
    print("Key endpoints:")
    print(f"  - Health check: http://{args.host}:{args.port}/api/health")
    print(f"  - Upload XML:   http://{args.host}:{args.port}/api/xml/upload")
    print(f"  - List files:   http://{args.host}:{args.port}/api/xml")
    print("\nFor full documentation, see docs/API_DOCUMENTATION.md")
    print("\n" + "-"*60 + "\n")

    # Start the server
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=app.config['DEBUG']
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped gracefully")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
