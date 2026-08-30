import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliExecutionTests(unittest.TestCase):
    def test_cli_exits_gracefully_without_stdin(self):
        source = ROOT / "examples" / "hello.han"

        proc = subprocess.run(
            [sys.executable, str(ROOT / "main.py"), str(source), "--실행"],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=10,
        )

        self.assertEqual(proc.returncode, 0)
        self.assertTrue(proc.stdout == "\n" or proc.stdout == "")


if __name__ == "__main__":
    unittest.main()
