#!/usr/bin/env python3
"""Script to fix common flake8 linting issues."""

import re
import sys
from pathlib import Path


def fix_boolean_comparisons(content):
    """Fix E712: comparison to True/False."""
    # Replace == True with is True
    content = re.sub(r'(\s+)==\s*True\b', r'\1is True', content)
    # Replace == False with is False
    content = re.sub(r'(\s+)==\s*False\b', r'\1is False', content)
    return content


def remove_unused_variables(filepath, content):
    """Comment out or remove unused variable assignments."""
    lines = content.split('\n')
    # This is complex - we'll handle specific cases manually
    return content


def main():
    # Fix boolean comparisons in test files
    test_files = [
        'tests/property/test_user_authentication.py',
        'tests/unit/test_authentication_edge_cases.py',
    ]
    
    for filepath in test_files:
        path = Path(filepath)
        if path.exists():
            content = path.read_text()
            original = content
            content = fix_boolean_comparisons(content)
            if content != original:
                path.write_text(content)
                print(f"Fixed boolean comparisons in {filepath}")


if __name__ == '__main__':
    main()
