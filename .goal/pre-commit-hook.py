#!/usr/bin/env python3
"""Goal pre-commit hook.

This script runs Goal's validation checks before commit.
"""

import sys
from pathlib import Path

# Add goal to Python path
goal_path = Path(__file__).parent.parent
sys.path.insert(0, str(goal_path))

from goal.hooks.manager import HooksManager

def main():
    """Run pre-commit validation."""
    manager = HooksManager()
    success = manager.run_validation()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
