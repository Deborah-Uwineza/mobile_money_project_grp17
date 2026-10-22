@echo off
rem Section 3.2: full import into the EMPTY default database "neo4j". Stop Neo4j first.
rem   1) set NEO4J_HOME=C:\path\to\neo4j-community-x.y.z
rem   2) neo4j stop            (or stop the Windows service)
rem   3) python prepare_import.py
rem   4) neo4j\import_full.bat   (run from the project root)
set IMPORT=%CD%\import_tmp
"%NEO4J_HOME%\bin\neo4j-admin.bat" database import full neo4j ^
  --overwrite-destination ^
  --id-type=integer ^
  --nodes=Customer="%IMPORT%\customers.csv" ^
  --nodes=Account="%IMPORT%\accounts.csv" ^
  --nodes=Device="%IMPORT%\devices.csv" ^
  --relationships=OWNS="%IMPORT%\owns.csv" ^
  --relationships=USED_DEVICE="%IMPORT%\account_devices.csv" ^
  --relationships=TRANSFER="%IMPORT%\transfers.csv"
