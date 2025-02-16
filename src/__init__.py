# Version 3.0.0 of the bot included a reversion to the basics, and some new features (see changelog)
__version__ = "3.2.0"

# Assert that Python version >= 3.9, or else they receive the subscription error for type hints
import sys

if sys.version_info < (3, 9):
    raise Exception("Python version must be >= 3.9")
