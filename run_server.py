#!/usr/bin/env python3
"""Script to run the Dutch-o-matic web server."""

import os
import sys
import traceback

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from src.web.app import app
except Exception as e:
    print(f'ERROR: Failed to import app: {e}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        app.run(host=host, port=port, debug=False)
    except Exception as e:
        print(f'ERROR: Failed to start server: {e}', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
