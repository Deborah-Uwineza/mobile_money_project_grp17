"""Central settings. Override with environment variables; never commit real passwords."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("MM_DATA_DIR", ROOT / "data"))          # source CSVs (kept local)
IMPORT_DIR = Path(os.environ.get("MM_IMPORT_DIR", ROOT / "import_tmp"))  # temporary Neo4j import copies
RESULTS_DIR = Path(os.environ.get("MM_RESULTS_DIR", ROOT / "results"))

# PostgreSQL (psycopg connection string). Replace CHANGE_ME or set MM_PG_DSN.
PG_DSN = os.environ.get(
    "MM_PG_DSN",
    "host=localhost port=5432 dbname=mobile_money user=postgres password=CHANGE_ME",
)

# Neo4j Community, default database "neo4j".
NEO4J_URI = os.environ.get("MM_NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("MM_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("MM_NEO4J_PASSWORD", "CHANGE_ME")
NEO4J_DB = "neo4j"

# Optional: Neo4j installation / data folder, used only to report store sizes.
NEO4J_HOME = os.environ.get("NEO4J_HOME", "")

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
