#!/usr/bin/env python3
"""
Recipe Collection Explorer - Application Launcher
Run this script to start the Recipe Collection Explorer GUI application
"""

import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run the recipe explorer
import recipe_explorer

if __name__ == "__main__":
    print("="*60)
    print("  RECIPE COLLECTION EXPLORER v2.0 - ENHANCED EDITION")
    print("="*60)
    print("\nStarting the Recipe Collection Explorer...")
    print("\n✨ NEW FEATURES in v2.0:")
    print("  🌐 Search and import recipes from the web!")
    print("  📋 Automatic recipe parsing from websites")
    print("  ✍️  Enhanced manual recipe entry")
    print("\nCore Features:")
    print("  • Browse 54 recipes from world cuisines")
    print("  • 31+ ingredients database")
    print("  • 27+ kitchen equipment reference")
    print("  • 11 world cuisines explored")
    print("  • Add your own recipes")
    print("  • Shopping list generator")
    print("  • Search and filter by cuisine, category, difficulty")
    print("  • Export recipes and shopping lists")
    print("\nLoading application...")
    print("="*60)
    print()
    
    recipe_explorer.main()
