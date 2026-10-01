"""Points the API's persistence snapshot at a fresh temp file for the whole
test session, so tests always start from the synthetic seed rather than
whatever a previous `pytest` run (or a dev server run) left on disk."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_tmp_dir = tempfile.mkdtemp(prefix="cassandre_cc_test_store_")
os.environ["CASSANDRE_CC_STORE_PATH"] = str(Path(_tmp_dir) / "store_snapshot.json")
