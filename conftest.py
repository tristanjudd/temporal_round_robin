# Ensures repo-root modules (approval_profiles, encoding, etc.) are
# importable from tests regardless of where pytest is invoked from.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
