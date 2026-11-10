"""Step 1: violation-level analysis file. Reads the Building Violations extracts, assigns each record to a 2020-vintage census tract
(point in polygon), keeps the 789 analytic tracts built by Paper 1's step 02, and writes work/viol.pkl, work/tract.pkl, work/meta.json."""
from common4 import *
import geopandas as gpd

files = sorted(glob.glob(os.path.join(RAW_DIR, "Building_Violations*.csv")))
raw = pd.concat([pd.read_csv(f, usecols=USECOLS, dtype=str, keep_default_na=False) for f in files], ignore_index=True)
meta = {"files": [os.path.basename(f) for f in files], "rows_raw": len(raw)}
v = raw.drop_duplicates("ID").copy()
meta["rows_unique_ids"] = len(v)
v["vdate"] = pd.to_datetime(v["VIOLATION DATE"], format="%m/%d/%Y", errors="coerce")
v["sdate"] = pd.to_datetime(v["VIOLATION STATUS DATE"], format="%m/%d/%Y", errors="coerce")
v["lat"] = pd.to_numeric(v["LATITUDE"], errors="coerce"); v["lon"] = pd.to_numeric(v["LONGITUDE"], errors="coerce")
meta["violation_dates_unparsed"] = int(v.vdate.isna().sum())
meta["blank_violation_code"] = int((v["VIOLATION CODE"] == "").sum())
meta["rows_by_year_all"] = {int(k): int(n) for k, n in v.vdate.dt.year.value_counts().sort_index().items()}
ok = v.lat.notna() & v.lon.notna()
meta["no_coordinates"] = int((~ok).sum())

t = gpd.read_file(os.path.join(P1_WORK, "data", "tracts", "cb_2023_17_tract_500k.shp"))[["GEOID", "geometry"]].to_crs(4326)
pts = gpd.GeoDataFrame(v.loc[ok, ["ID"]].copy(), geometry=gpd.points_from_xy(v.loc[ok, "lon"], v.loc[ok, "lat"]), crs=4326)
j = gpd.sjoin(pts, t, predicate="within", how="left")[["ID", "GEOID"]].drop_duplicates("ID")
v = v.merge(j, on="ID", how="left")

x = pd.read_csv(os.path.join(P1_WORK, "tract.csv"), dtype={"GEOID": str}, index_col="GEOID")
meta["chicago_tracts"] = len(x)
x = x[x["analytic"].astype(bool)].copy()
meta["analytic_tracts"] = len(x)
x["hard_z"] = zs(x.hardship); x["yb_z"] = zs(x.year_built); x["own_z"] = zs(x.own)
x["ldens_z"] = zs(np.log(x.density.clip(lower=1))); x["black_z"] = zs(x.pct_black)
x["q"] = pd.qcut(x["hardship"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
v = v[v.GEOID.isin(x.index)].copy()
meta["rows_in_analytic_tracts"] = len(v)
meta["with_coordinates_outside_analytic_tracts"] = meta["rows_unique_ids"] - meta["no_coordinates"] - len(v)

v = v.join(x[["ca", "hardship", "hard_z", "yb_z", "own_z", "ldens_z", "black_z", "q"]], on="GEOID")
v["cat"] = v["INSPECTION CATEGORY"]; v["bureau"] = v["DEPARTMENT BUREAU"]
v["complied"] = (v["VIOLATION STATUS"] == "COMPLIED").astype(int)
v["end"] = v["sdate"].where(v["complied"].eq(1), EXTRACT)
v["days"] = (v["end"] - v["vdate"]).dt.days
v["time"] = v["days"].clip(lower=1).astype(float)
v["year"] = v.vdate.dt.year
meta["complied_missing_status_date"] = int(((v.complied == 1) & v.sdate.isna()).sum())
meta["negative_durations"] = int((v.days < 0).sum())
meta["status_counts"] = v["VIOLATION STATUS"].value_counts().to_dict()
meta["category_counts"] = v["cat"].value_counts().to_dict()
meta["rows_by_year"] = {int(k): int(n) for k, n in v.year.value_counts().sort_index().items()}
meta["bureau_counts"] = v["bureau"].value_counts().head(12).to_dict()
meta["stf_rows"] = int((v.bureau == "SPECIAL TASK FORCE").sum())
meta["stf_by_category"] = v[v.bureau == "SPECIAL TASK FORCE"]["cat"].value_counts().to_dict()
meta["periodic_by_bureau"] = v[v.cat == "PERIODIC"]["bureau"].value_counts().head(6).to_dict()
meta["distinct_inspections"] = int(v["INSPECTION NUMBER"].nunique())
meta["inspection_status_by_violation_status"] = pd.crosstab(v["INSPECTION STATUS"], v["VIOLATION STATUS"]).to_dict()

keep = ["ID", "GEOID", "ca", "q", "hardship", "hard_z", "yb_z", "own_z", "ldens_z", "black_z", "cat", "bureau", "INSPECTION NUMBER",
        "INSPECTION STATUS", "VIOLATION STATUS", "vdate", "year", "complied", "time"]
v[keep].to_pickle(W("viol.pkl")); x.to_pickle(W("tract.pkl")); jdump(meta, W("meta.json"))
print(json.dumps({k: meta[k] for k in meta if k not in ("inspection_status_by_violation_status",)}, indent=1, cls=Enc))
