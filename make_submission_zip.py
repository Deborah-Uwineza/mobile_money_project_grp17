"""Build the submission ZIP (code, SQL, Cypher, docs, results, plans). Excludes CSVs, import copies and caches."""
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
skip_dirs = {"data", "import_tmp", "__pycache__", ".git", ".venv"}
out = root.parent / "mobile_money_submission.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and not (set(rel.parts) & skip_dirs) and p.suffix != ".zip":
            z.write(p, Path("mobile_money_project") / rel)
print("Wrote", out)
