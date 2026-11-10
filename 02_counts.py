"""Step 2: tract-level enforcement rates and Poisson count models (Tables 2-4, A2). Writes work/counts.json and work/tabs/*.csv."""
from common4 import *
v = pd.read_pickle(W("viol.pkl")); x = pd.read_pickle(W("tract.pkl"))
R = {}

def tract_counts(sub, years=6):
    c = sub.groupby(["GEOID", "cat"]).size().unstack(fill_value=0)
    c.columns = [k.lower() for k in c.columns]
    t = x.join(c, how="left")
    for k in ("complaint", "periodic", "permit"):
        if k not in t: t[k] = 0
        t[k] = t[k].fillna(0)
    t["off"] = np.log(t["pop"] * years)
    return t

# ---- main tract table: violations by trigger, distinct inspections, failed inspections
tt = tract_counts(v)
tt["total"] = tt[["complaint", "periodic", "permit"]].sum(axis=1)
insp = v.drop_duplicates("INSPECTION NUMBER")
tt["inspections"] = insp.groupby("GEOID").size().reindex(tt.index).fillna(0)
tt["failed"] = insp[insp["INSPECTION STATUS"] == "FAILED"].groupby("GEOID").size().reindex(tt.index).fillna(0)
tt["open"] = v[v["VIOLATION STATUS"] == "OPEN"].groupby("GEOID").size().reindex(tt.index).fillna(0)

# ---- quartile descriptives (Table 2)
g = tt.groupby("q", observed=True); P = g["pop"].sum() * 6
desc = pd.DataFrame({
    "tracts": g.size(),
    "complaint": 1000 * g["complaint"].sum() / P, "periodic": 1000 * g["periodic"].sum() / P, "permit": 1000 * g["permit"].sum() / P,
    "total": 1000 * g["total"].sum() / P, "inspections": 1000 * g["inspections"].sum() / P,
    "complaint_share": g["complaint"].sum() / g["total"].sum(), "failed_share": g["failed"].sum() / g["inspections"].sum(),
    "open_share": g["open"].sum() / g["total"].sum(), "viol_per_inspection": g["total"].sum() / g["inspections"].sum(),
    "violations": g["total"].sum(), "pop": g["pop"].sum()})
desc.to_csv(W("tabs", "quartile_desc.csv")); print(desc.round(3).to_string())
R["corr_hard_black"] = float(x[["hardship", "pct_black"]].corr().iloc[0, 1])
R["corr_hard_poverty"] = float(x[["hardship", "poverty"]].corr().iloc[0, 1])
R["pop_years"] = float(P.sum())

# ---- main Poisson models (Table 3) and with % Black added
for y in ["complaint", "periodic", "permit", "total", "inspections"]:
    R[f"main_{y}"] = pois_fit(tt, y, BASE)
for y in ["complaint", "periodic", "permit", "total"]:
    R[f"race_{y}"] = pois_fit(tt, y, BASE + ["black_z"])

# ---- formal test that the complaint gradient differs from the routine and permit gradients (stacked, fully interacted)
rows = []
for k in ("complaint", "periodic", "permit"):
    d = tt[[k, "off", "ca"] + BASE].rename(columns={k: "y"}).copy(); d["cat"] = k; rows.append(d)
L = pd.concat(rows, ignore_index=True)
for k in ("periodic", "permit"):
    L["is_" + k] = (L.cat == k).astype(float)
    for c in BASE: L[f"{c}_x_{k}"] = L[c] * L["is_" + k]
xc = BASE + ["is_periodic", "is_permit"] + [f"{c}_x_{k}" for k in ("periodic", "permit") for c in BASE]
stk = pois_fit(L, "y", xc)
R["diff_periodic_minus_complaint"] = stk["hard_z_x_periodic"]; R["diff_permit_minus_complaint"] = stk["hard_z_x_permit"]

# ---- robustness: excluding bureaus, Special Task Force
excl = {"excl_elev_boiler": v[~v.bureau.isin(["ELEVATOR", "BOILER"])], "excl_stf": v[v.bureau != "SPECIAL TASK FORCE"]}
for k, sub in excl.items():
    t2 = tract_counts(sub)
    for y in ["complaint", "periodic", "permit"]: R[f"{k}_{y}"] = pois_fit(t2, y, BASE)

# ---- community-area models with the official 2008-2012 Hardship Index (HC1 robust SEs, t(N-k))
ca = tt.groupby("ca").agg(pop=("pop", "sum"), complaint=("complaint", "sum"), periodic=("periodic", "sum"), permit=("permit", "sum")).reset_index()
cs = pd.read_csv(os.path.join(RAW_DIR, "Census_Data_-_Selected_socioeconomic_indicators_in_Chicago__2008___2012_20260923.csv"))
cs = cs.rename(columns={"Community Area Number": "ca", "HARDSHIP INDEX": "hard_off"})
ca = ca.merge(cs[["ca", "hard_off"]], on="ca"); ca["hard_off_z"] = zs(ca.hard_off.astype(float)); ca["off"] = np.log(ca["pop"] * 6)
R["n_ca"] = len(ca)
for y in ["complaint", "periodic", "permit"]:
    m = sm.GLM(ca[y].astype(float), sm.add_constant(ca[["hard_off_z"]]), family=sm.families.Poisson(), offset=ca["off"]).fit(cov_type="HC1")
    R[f"ca_{y}"] = summarize(m.params, m.bse, ["hard_off_z"], len(ca) - 2)["hard_off_z"]

# ---- year-by-year gradients (Table A2)
for yr in range(2019, 2025):
    t3 = tract_counts(v[v.year == yr], years=1)
    for y in ["complaint", "periodic", "permit"]:
        R[f"year{yr}_{y}"] = pois_fit(t3, y, BASE)
yc = v.groupby(["year", "cat"]).size().unstack(fill_value=0); yc.to_csv(W("tabs", "year_by_category.csv")); print(yc)

jdump(R, W("counts.json"))
for k in ("main_complaint", "main_periodic", "main_permit", "main_total", "main_inspections"):
    r = R[k]["hard_z"]; print(f"{k:22s} IRR {r['irr']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}] p={r['p']:.4f}")
for k in ("race_complaint", "race_periodic", "race_permit", "race_total"):
    r = R[k]["hard_z"]; b = R[k]["black_z"]; print(f"{k:22s} hard IRR {r['irr']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}] | black IRR {b['irr']:.3f}")
for k in ("diff_periodic_minus_complaint", "diff_permit_minus_complaint"):
    r = R[k]; print(f"{k}: b={r['b']:.3f} se={r['se']:.3f} p={r['p']:.2e}")
for k in R:
    if k.startswith(("excl_", "ca_", "year")) and isinstance(R[k], dict):
        r = R[k]["hard_z"] if "hard_z" in R[k] else R[k]
        print(f"{k:28s} IRR {r['irr']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}] p={r['p']:.4f}")
