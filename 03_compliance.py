"""Step 3: compliance (Kaplan-Meier, Cox models with a proportional-hazards check) and the standardization of the compliance gap
(Tables 5-7). Writes work/compliance.json and work/tabs/*.csv."""
import time as _time
from common4 import *
from statsmodels.duration.hazard_regression import PHReg
from statsmodels.duration.survfunc import SurvfuncRight
T0 = _time.time()
def log(msg): print(f"[{_time.time()-T0:6.0f}s] {msg}", flush=True)

v = pd.read_pickle(W("viol.pkl")); R = jload(W("compliance.json")) if os.path.exists(W("compliance.json")) else {}
v["periodic"] = (v.cat == "PERIODIC").astype(float); v["permit"] = (v.cat == "PERMIT").astype(float)
YD = [f"y{y}" for y in range(2020, 2025)]
for y in range(2020, 2025): v[f"y{y}"] = (v.year == y).astype(float)
top_b = v.bureau.value_counts().index[:5].tolist(); R["top5_bureaus"] = top_b
BD = []
for b in top_b:
    c = "b_" + "".join(ch if ch.isalnum() else "_" for ch in b); v[c] = (v.bureau == b).astype(float); BD.append(c)

def km_at(time, event, horizon=365):
    """Kaplan-Meier share complied by `horizon` days (integer-day times; censored at t count as at risk at t)."""
    t = np.minimum(np.asarray(time).astype(int), horizon + 1); e = np.asarray(event).astype(int)
    d = np.bincount(t[e == 1], minlength=horizon + 2)[:horizon + 1]; c = np.bincount(t[e == 0], minlength=horizon + 2)[:horizon + 1]
    n = len(t) - np.concatenate([[0], np.cumsum(d + c)[:-1]])
    hz = np.where(n > 0, d / np.maximum(n, 1), 0.0)
    return 1 - np.prod(1 - hz[1:horizon + 1])

# ---- Kaplan-Meier by quartile and category (Table 5), checked against statsmodels
rows = []
for cat in CATS + ["ALL"]:
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        s = v[(v.q == q) & ((v.cat == cat) | (cat == "ALL"))]
        S = SurvfuncRight(s["time"].values, s["complied"].values); st, sp = np.asarray(S.surv_times), np.asarray(S.surv_prob)
        i = np.searchsorted(st, 365, side="right") - 1; sm365 = 1 - (sp[i] if i >= 0 else 1.0)
        mine = km_at(s["time"].values, s["complied"].values); assert abs(sm365 - mine) < 1e-9, (cat, q, sm365, mine)
        med = float(st[np.argmax(sp <= 0.5)]) if (sp <= 0.5).any() else None
        rows.append(dict(cat=cat, q=q, n=len(s), raw_complied=float(s.complied.mean()), km365=float(mine), km_median_days=med))
km = pd.DataFrame(rows); km.to_csv(W("tabs", "km_by_q_cat.csv"), index=False); R["km"] = rows; log("KM done (custom estimator matches statsmodels)")
print(km.round(3).to_string(index=False))

# ---- Cox models (hazard of compliance; HR > 1 = faster); SEs clustered by community area; t(G-1) intervals
def cox(df, covs, strata=None, entry=None, time=None, status=None, label=""):
    covs = [c for c in covs if df[c].astype(float).std() > 0]      # drop dummies that are constant within the subset
    mod = PHReg(df["time"].values if time is None else time, df[covs].astype(float).values,
                status=df["complied"].values if status is None else status, entry=entry, strata=strata)
    res = mod.fit(groups=df["ca"].values)
    G = df["ca"].nunique(); out = summarize(dict(zip(covs, res.params)), dict(zip(covs, res.bse)), covs, G - 1)
    out["_n"] = int(len(df)); out["_events"] = int((df["complied"].values if status is None else status).sum()); out["_G"] = int(G)
    log(f"Cox {label}: hardship HR {out['hard_z']['irr']:.3f} [{out['hard_z']['lo']:.3f}, {out['hard_z']['hi']:.3f}] n={out['_n']:,} events={out['_events']:,}")
    return out
catcode = v.cat.map({"COMPLAINT": 0, "PERIODIC": 1, "PERMIT": 2}).values
def run(key, fn):
    if key in R: log(f"cached: {key}"); return
    R[key] = fn(); jdump(R, W("compliance.json"))
run("cox_pooled", lambda: cox(v, BASE + ["periodic", "permit"] + YD + BD, label="pooled"))
run("cox_strat_cat", lambda: cox(v, BASE + YD + BD, strata=catcode, label="stratified by category"))
run("cox_strat_cat_year", lambda: cox(v, BASE + BD, strata=(catcode * 10 + (v.year.values - 2019)), label="stratified by category x year"))
for cat in CATS:
    run(f"cox_{cat.lower()}", lambda cat=cat: cox(v[v.cat == cat], BASE + YD + BD, label=f"{cat} only"))
# proportional-hazards check: hardship hazard ratio in the first year versus after the first year (episode split at 365 days)
tA = np.minimum(v["time"].values, 365.0); eA = ((v.complied.values == 1) & (v["time"].values <= 365)).astype(int)
run("cox_year1", lambda: cox(v, BASE + ["periodic", "permit"] + YD + BD, time=tA, status=eA, label="first year"))
late = v[v["time"] > 365]
run("cox_after_year1", lambda: cox(late, BASE + ["periodic", "permit"] + YD + BD, entry=np.full(len(late), 365.0), label="after first year"))

# ---- standardization of the one-year compliance gap, Q1 vs Q4, with bootstrap CIs (resampling community areas within quartile)
v["cell_cat"] = v.cat; v["cell_bureau"] = v.cat + "|" + v.bureau.where(v.bureau.isin(v.bureau.value_counts().index[:8]), "OTHER")
def decompose(d, cell, min_n=50):
    n = {}; r = {}
    for q in ("Q1", "Q4"):
        s = d[d.q == q]
        for c, sub in s.groupby(cell):
            n[(c, q)] = len(sub); r[(c, q)] = km_at(sub["time"].values, sub["complied"].values)
    cells = sorted({c for c, _ in n}); ok = [c for c in cells if n.get((c, "Q1"), 0) >= min_n and n.get((c, "Q4"), 0) >= min_n]
    if not ok: return None
    n1 = np.array([n[(c, "Q1")] for c in ok], float); n4 = np.array([n[(c, "Q4")] for c in ok], float)
    r1 = np.array([r[(c, "Q1")] for c in ok]); r4 = np.array([r[(c, "Q4")] for c in ok])
    w1, w4 = n1 / n1.sum(), n4 / n4.sum(); R11, R41, R44 = (w1 * r1).sum(), (w1 * r4).sum(), (w4 * r4).sum()
    return dict(cells=len(ok), cover_q1=n1.sum() / (d.q == "Q1").sum(), cover_q4=n4.sum() / (d.q == "Q4").sum(),
                R11=R11, R41=R41, R44=R44, gap=R11 - R44, within=R11 - R41, comp=R41 - R44, comp_share=(R41 - R44) / (R11 - R44))
rng = np.random.default_rng(20261105); B = 500
for cell in ("cell_cat", "cell_bureau"):
    est = decompose(v, cell); R[f"decomp_{cell}"] = est
    sub = v[v.q.isin(["Q1", "Q4"])]; groups = {q: {c: g.index.values for c, g in sub[sub.q == q].groupby("ca")} for q in ("Q1", "Q4")}
    boot = []
    for b in range(B):
        parts = []
        for q in ("Q1", "Q4"):
            cas = list(groups[q]); draw = rng.choice(len(cas), len(cas), replace=True)
            parts.append(np.concatenate([groups[q][cas[i]] for i in draw]))
        dd = sub.loc[np.concatenate(parts)]; e = decompose(dd, cell)
        if e: boot.append((e["gap"], e["within"], e["comp"], e["comp_share"]))
    boot = np.array(boot); R[f"decomp_{cell}_ci"] = {k: [float(np.percentile(boot[:, i], 2.5)), float(np.percentile(boot[:, i], 97.5))]
                                                  for i, k in enumerate(["gap", "within", "comp", "comp_share"])}
    R[f"decomp_{cell}_B"] = int(len(boot))
    log(f"decomposition {cell}: " + json.dumps({k: (round(val, 4) if isinstance(val, float) else val) for k, val in est.items()}))
    log(f"   bootstrap 95% CI: {json.dumps({k: [round(a, 4) for a in val] for k, val in R[f'decomp_{cell}_ci'].items()})}")
jdump(R, W("compliance.json")); log("done")
