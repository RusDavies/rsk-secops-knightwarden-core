from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import knightwarden


class PackageImportTest(unittest.TestCase):
    def test_version_is_available(self) -> None:
        self.assertEqual(knightwarden.__version__, "0.1.0")


if __name__ == "__main__":
    unittest.main()
