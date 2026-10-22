#!/usr/bin/env bash
# Section 3.2: full import into the EMPTY default database "neo4j". Stop Neo4j first. Run from the project root.
set -e
IMPORT="$(pwd)/import_tmp"
"${NEO4J_HOME}/bin/neo4j-admin" database import full neo4j \
  --overwrite-destination \
  --id-type=integer \
  --nodes=Customer="$IMPORT/customers.csv" \
  --nodes=Account="$IMPORT/accounts.csv" \
  --nodes=Device="$IMPORT/devices.csv" \
  --relationships=OWNS="$IMPORT/owns.csv" \
  --relationships=USED_DEVICE="$IMPORT/account_devices.csv" \
  --relationships=TRANSFER="$IMPORT/transfers.csv"
