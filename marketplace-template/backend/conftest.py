"""Pytest bootstrap: put the backend dir on sys.path so `tests/` can import the
top-level modules (main, config, data_source, ...) without a package install."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
