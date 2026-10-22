"""Confirm mobile_money_generator.py is byte-for-byte the supplied file."""
import hashlib
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
actual = hashlib.sha256((root / "mobile_money_generator.py").read_bytes()).hexdigest()
expected = (root / "generator.sha256").read_text().split()[0]
print("expected:", expected)
print("actual  :", actual)
print("generator UNCHANGED" if actual == expected else "generator CHANGED - restore the supplied file!")
sys.exit(0 if actual == expected else 1)
