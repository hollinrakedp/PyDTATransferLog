import os
import sys

# Ensure src is on path for tests
ROOT = os.path.abspath(os.path.dirname(__file__))
SRC = os.path.abspath(os.path.join(ROOT, "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)
