"""Setup Python path for F-Ops modules"""

import sys
import os

# Add parent directory to path for importing mcp_packs and knowledge_base
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)