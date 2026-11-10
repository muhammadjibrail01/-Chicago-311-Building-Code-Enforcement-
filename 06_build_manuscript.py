"""Step 6: assemble the manuscript markdown (Word rendering is step 8). Every {{key:fmt}} placeholder in manuscript/template_part*.md is resolved from the saved results,
every {{TABLE_n}} is replaced by the generated table, A placeholder that cannot be resolved stops the build."""
import re, shutil, subprocess
from common4 import *
M = jload(W("meta.json")); C = jload(W("counts.json")); K = jload(W("compliance.json")); X = pd.read_pickle(W("tract.pkl"))
D = pd.read_csv(W("tabs", "quartile_desc.csv"), index_col="q").to_dict(orient="index")
KMdf = pd.DataFrame(K["km"]); KM = {c: {q: KMdf[(KMdf.cat == c) & (KMdf.q == q)].iloc[0].to_dict() for q in ("Q1", "Q2", "Q3", "Q4")} for c in KMdf.cat.unique()}
T = jload(W("tabs", "all_tables.json"))
yrs = range(2019, 2025); tot = M["rows_in_analytic_tracts"]
Xd = {
 "later_year_min": min(M["rows_by_year"][str(y)] for y in range(2021, 2025)), "later_year_max": max(M["rows_by_year"][str(y)] for y in range(2021, 2025)),
 "cat_share_complaint": M["category_counts"]["COMPLAINT"] / tot, "cat_share_periodic": M["category_counts"]["PERIODIC"] / tot, "cat_share_permit": M["category_counts"]["PERMIT"] / tot,
 "dropped_tracts": M["chicago_tracts"] - M["analytic_tracts"], "hard_mean": float(X.hardship.mean()), "hard_sd": float(X.hardship.std()),
 "pc_corr": float(X[["hardship", "hardship_pc"]].corr().iloc[0, 1]), "open_share": M["status_counts"]["OPEN"] / tot, "G_minus_1": C["main_complaint"]["_G"] - 1,
 "complaint_fold": D["Q4"]["complaint"] / D["Q1"]["complaint"], "routine_min": min(D[q]["periodic"] for q in D), "routine_max": max(D[q]["periodic"] for q in D),
 "diff_cp_b": -C["diff_periodic_minus_complaint"]["b"], "diff_cp_se": C["diff_periodic_minus_complaint"]["se"], "diff_cp_p": C["diff_periodic_minus_complaint"]["p"],
 "diff_cm_b": -C["diff_permit_minus_complaint"]["b"], "diff_cm_se": C["diff_permit_minus_complaint"]["se"], "diff_cm_p": C["diff_permit_minus_complaint"]["p"],
 "ca_df": C["n_ca"] - 2,
 "cmin": min(C[f"year{y}_complaint"]["hard_z"]["irr"] for y in yrs), "cmax": max(C[f"year{y}_complaint"]["hard_z"]["irr"] for y in yrs),
 "pmin": min(C[f"year{y}_permit"]["hard_z"]["irr"] for y in yrs), "pmax": max(C[f"year{y}_permit"]["hard_z"]["irr"] for y in yrs),
 "n_periodic_below1": sum(C[f"year{y}_periodic"]["hard_z"]["irr"] < 1 for y in yrs),
 "gap_all_km": KM["ALL"]["Q1"]["km365"] - KM["ALL"]["Q4"]["km365"], "gap_complaint_km": KM["COMPLAINT"]["Q1"]["km365"] - KM["COMPLAINT"]["Q4"]["km365"],
 "gap_all_raw": KM["ALL"]["Q1"]["raw_complied"] - KM["ALL"]["Q4"]["raw_complied"],
 "complaint_raw_min": min(KM["COMPLAINT"][q]["raw_complied"] for q in KM["COMPLAINT"]), "complaint_raw_max": max(KM["COMPLAINT"][q]["raw_complied"] for q in KM["COMPLAINT"]),
}
if "decomp_cell_cat" in K:
    Xd["gap_pp_cat"] = 100 * K["decomp_cell_cat"]["gap"]; Xd["comp_pp_cat"] = 100 * K["decomp_cell_cat"]["comp"]
NS = {"m": M, "c": C, "k": K, "d": D, "km": KM, "x": Xd}
def get(path):
    cur = NS
    for part in path.split("."): cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
def fmt(v, f):
    out = _fmt(v, f); return out.replace("-", "−") if out[:1] == "-" else out
def _fmt(v, f):
    if f == "w": return WORDS[int(round(v))]
    if f == "i": return f"{int(round(v)):,}"
    if f in ("f1", "f2", "f3"): return f"{v:.{int(f[1])}f}"
    if f in ("p0", "p1"): return f"{100 * v:.{int(f[1])}f}"
    if f == "u0": return f"{100 * (v - 1):.0f}"
    if f == "pv": return "p < 0.001" if v < 0.001 else f"p = {v:.3f}"
    raise ValueError("unknown format " + f)
text = "".join(open(os.path.join(OUT_DIR, p), encoding="utf-8").read() for p in sorted(os.listdir(OUT_DIR)) if p.startswith("template_part") and p.endswith(".md"))
text = re.sub(r"\{\{(TABLE_[A-Z0-9]+)\}\}", lambda m_: T[m_.group(1)], text)
def sub(m_):
    try: return fmt(get(m_.group(1)), m_.group(2))
    except Exception as e: raise SystemExit(f"cannot resolve placeholder {m_.group(0)}: {e!r}")
text = re.sub(r"\{\{([A-Za-z0-9_.]+):([a-z0-9]+)\}\}", sub, text)
assert "{{" not in text and "}}" not in text, "unresolved placeholder"
for f in ("fig1_rates.png", "fig2_compliance.png", "fig3_years.png"): shutil.copy(W("figs", f), os.path.join(OUT_DIR, f))
open(os.path.join(OUT_DIR, "paper4.md"), "w", encoding="utf-8").write(text)
jdump(Xd, W("derived.json")); print("built manuscript:", len(text.split()), "words")
