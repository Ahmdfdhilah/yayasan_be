"""Simple seeding script runner."""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.seed_users import main

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed.py [up|down]")
        print("  up   - Create seeding data")
        print("  down - Clear all data")
        sys.exit(1)
    
    action = sys.argv[1]
    if action not in ['up', 'down']:
        print("Invalid action. Use 'up' or 'down'")
        sys.exit(1)
    
    # Pass argument to the main script
    sys.argv = ['seed_users.py', action]
    
    if action == 'down':
        print("Clearing database data...")
    else:
        print("Running database seeding...")
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)