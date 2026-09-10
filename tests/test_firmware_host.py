"""Compile and execute logic with fake Arduino functions, never hardware claims."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FirmwareHostTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("g++"), "g++ unavailable; not firmware validated")
    def test_compile_and_logic_with_host_stubs(self):
        with tempfile.TemporaryDirectory() as d:
            exe = str(Path(d) / "firmware_host")
            subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
                            "-I", str(ROOT / "tests/firmware_stubs"),
                            str(ROOT / "tests/firmware_host.cpp"), "-o", exe], check=True)
            subprocess.run([exe], check=True)
