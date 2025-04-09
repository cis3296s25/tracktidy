#!/usr/bin/env python
"""
TrackTidy Launcher Script
"""
import sys
import os

# Add the src directory to the path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

# Import and run the main function
from src.tracktidy.main import main

if __name__ == "__main__":
    main()
