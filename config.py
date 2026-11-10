"""Folder settings for the Paper 4 replication package. Edit them here or set the environment variables RAW_DIR, P1_WORK, WORK_DIR and OUT_DIR."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR  = os.environ.get("RAW_DIR",  os.path.join(HERE, "raw_data"))                                   # Chicago Data Portal downloads (Building_Violations*.csv, census CSVs)
P1_WORK  = os.environ.get("P1_WORK",  os.path.join(HERE, "..", "paper1_replication", "work"))           # work folder of the Paper 1 package: tract.csv and data/tracts/*.shp (run its steps 00 and 02 first)
WORK_DIR = os.environ.get("WORK_DIR", os.path.join(HERE, "work"))                                       # intermediate files and results
OUT_DIR  = os.environ.get("OUT_DIR",  os.path.join(HERE, "manuscript"))
for d in (WORK_DIR, os.path.join(WORK_DIR, "tabs"), os.path.join(WORK_DIR, "figs"), OUT_DIR):
    os.makedirs(d, exist_ok=True)
