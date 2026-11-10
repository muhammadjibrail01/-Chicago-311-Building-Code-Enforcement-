"""Optional helper. Paper 1's step 00 expects a community-area polygon file (ca.gpkg) from the main-paper package. If you do not have it,
this builds an equivalent from the Chicago Data Portal file 'Boundaries - Community Areas' (CSV export). Set MAIN_WORK for Paper 1 to OUT."""
import os, sys, pandas as pd, geopandas as gpd
from shapely import wkt
SRC = sys.argv[1] if len(sys.argv) > 1 else "Boundaries_-_Community_Areas.csv"; OUT = sys.argv[2] if len(sys.argv) > 2 else "main_work"
os.makedirs(OUT, exist_ok=True); b = pd.read_csv(SRC)
g = gpd.GeoDataFrame({"ca": b["AREA_NUMBE"].astype(int), "name": b["COMMUNITY"]}, geometry=b["the_geom"].apply(wkt.loads), crs="EPSG:4326")
g.to_file(os.path.join(OUT, "ca.gpkg"), driver="GPKG"); print("community areas written:", len(g))
