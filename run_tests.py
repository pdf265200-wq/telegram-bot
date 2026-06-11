#!/usr/bin/env python
"""
Test runner script
"""

import sys
import pytest
import os

def run_tests():
    """Run the test suite"""
    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Test arguments
    args = [
        'tests/',
        '-v',
        '--tb=short',
        '--strict-markers',
        '--disable-warnings',
        '-p', 'no:cacheprovider'
    ]
    
    # Add coverage if requested
    if '--cov' in sys.argv:
        args.extend([
            '--cov=bot',
            '--cov-report=html',
            '--cov-report=term-missing',
            '--cov-config=.coveragerc'
        ])
    
    # Run tests
    exit_code = pytest.main(args)
    sys.exit(exit_code)

if __name__ == '__main__':
    run_tests()
