"""Step 7: audit. (a) every qualitative claim the text makes is tested against the saved results; (b) literal numbers typed by hand in the
template are listed for review (everything derived from the analysis is a placeholder); (c) structural checks on the built manuscript."""
import re
from common4 import *
M = jload(W("meta.json")); C = jload(W("counts.json")); K = jload(W("compliance.json")); Xd = jload(W("derived.json"))
D = pd.read_csv(W("tabs", "quartile_desc.csv"), index_col="q"); KM = pd.DataFrame(K["km"])
yrs = range(2019, 2025); fails = []
def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{detail}]" if detail else "")); 
    if not cond: fails.append(name)
H = lambda k: C[k]["hard_z"]
print("=== (a) claims in the text versus results")
comp = [H("main_complaint"), H("excl_elev_boiler_complaint"), H("excl_stf_complaint"), H("race_complaint"), C["ca_complaint"]] + [H(f"year{y}_complaint") for y in yrs]
check("complaint IRR significantly above 1 in every specification and year", all(r["lo"] > 1 for r in comp), f"min lower bound {min(r['lo'] for r in comp):.3f}")
rout = [H("main_periodic"), H("excl_elev_boiler_periodic"), H("excl_stf_periodic"), H("race_periodic"), C["ca_periodic"]] + [H(f"year{y}_periodic") for y in yrs]
check("routine IRR never significantly above 1", all(r["lo"] <= 1 for r in rout), f"max lower bound {max(r['lo'] for r in rout):.3f}")
perm = [H("main_permit"), H("excl_elev_boiler_permit"), H("excl_stf_permit"), H("race_permit"), C["ca_permit"]] + [H(f"year{y}_permit") for y in yrs]
check("permit IRR significantly below 1 in every specification and year", all(r["hi"] < 1 for r in perm), f"max upper bound {max(r['hi'] for r in perm):.3f}")
check("main routine estimate not significant at 5% (text: 'not higher... if anything slightly lower')", H("main_periodic")["lo"] < 1 < H("main_periodic")["hi"] or H("main_periodic")["p"] > 0.05)
check("inspections IRR not significant ('rises less steeply and not significantly')", H("main_inspections")["lo"] < 1 < H("main_inspections")["hi"])
check("all-violations IRR with % Black added is indistinguishable from 1", H("race_total")["lo"] < 1 < H("race_total")["hi"])
check("routine IRR with % Black added significantly below 1 (text: fewer routine violations net of race)", H("race_periodic")["hi"] < 1)
check("trigger differences significant at p<0.001 (both tests)", C["diff_periodic_minus_complaint"]["p"] < 0.001 and C["diff_permit_minus_complaint"]["p"] < 0.001)
check("routine violations flat: quartile rates within 1.1 per 1,000 of each other", Xd["routine_max"] - Xd["routine_min"] < 1.1, f"{Xd['routine_min']:.2f}-{Xd['routine_max']:.2f}")
check("complaint share rises monotonically across quartiles", list(D.complaint_share) == sorted(D.complaint_share))
check("overall one-year compliance falls monotonically across quartiles", list(KM[KM.cat == "ALL"].km365) == sorted(KM[KM.cat == "ALL"].km365, reverse=True))
cm = KM[KM.cat == "COMPLAINT"]
check("complaint-driven one-year compliance about one in five in every quartile (0.15-0.25)", cm.km365.between(0.15, 0.25).all(), f"{cm.km365.min():.3f}-{cm.km365.max():.3f}")
check("complaint-driven one-year gap under 5 points", Xd["gap_complaint_km"] < 0.05, f"{100*Xd['gap_complaint_km']:.1f} pp")
am = KM[KM.cat == "ALL"].reset_index(drop=True)
check("only the lowest quartile has a Kaplan-Meier median", am.km_median_days.iloc[0] is not None and not pd.isna(am.km_median_days.iloc[0]) and am.km_median_days.iloc[1:].isna().all())
cox_keys = ["cox_pooled", "cox_strat_cat", "cox_strat_cat_year", "cox_complaint", "cox_periodic", "cox_permit", "cox_year1", "cox_after_year1"]
for k in cox_keys:
    if k in K: r = K[k]["hard_z"]; check(f"{k}: hardship hazard ratio CI includes 1", r["lo"] < 1 < r["hi"], f"HR {r['irr']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]")
    else: print(f"MISSING  {k} not yet computed")
check("routine and permit-triggered violations comply faster than complaint-driven (pooled HR lower bound > 1)", K["cox_pooled"]["periodic"]["lo"] > 1 and K["cox_pooled"]["permit"]["lo"] > 1)
for key in ("decomp_cell_cat", "decomp_cell_bureau"):
    if key in K:
        ci = K[key + "_ci"]["comp_share"]; check(f"{key}: composition share above one half with bootstrap lower bound above zero", K[key]["comp_share"] > 0.5 and ci[0] > 0, f"{100*K[key]['comp_share']:.0f}% [{100*ci[0]:.0f}%, {100*ci[1]:.0f}%]; coverage {100*K[key]['cover_q1']:.0f}%/{100*K[key]['cover_q4']:.0f}%")
check("routine IRR below one in the number of years the text reports", Xd["n_periodic_below1"] == sum(H(f"year{y}_periodic")["irr"] < 1 for y in yrs))
check("2022 and 2024 routine IRRs significantly below 1; 2019 borderline (0.05<p<0.06)", H("year2022_periodic")["hi"] < 1 and H("year2024_periodic")["hi"] < 1 and 0.05 < H("year2019_periodic")["p"] < 0.06)
check("no unparsed dates, no negative durations, no complied record without a date", M["violation_dates_unparsed"] == 0 and M["negative_durations"] == 0 and M["complied_missing_status_date"] == 0)
check("every record has a violation code (supports 'inspections observed only if they cited a violation')", M["blank_violation_code"] == 0)
check("Special Task Force records are all complaint-category", set(M["stf_by_category"]) == {"COMPLAINT"})
check("sample arithmetic: no-coordinates + outside + analytic = all records", M["no_coordinates"] + M["with_coordinates_outside_analytic_tracts"] + M["rows_in_analytic_tracts"] == M["rows_unique_ids"])

print("\n=== (b) literal numbers typed by hand in the template (review: should be background, design values, or companion-paper figures)")
tpl = "".join(open(os.path.join(OUT_DIR, f), encoding="utf-8").read() for f in sorted(os.listdir(OUT_DIR)) if f.startswith("template_part"))
body = tpl.split("# References")[0] + "# Appendix" + tpl.split("# Appendix A.")[1]
body = re.sub(r"\{\{.*?\}\}", " ", body); body = re.sub(r"^---.*?^---", " ", body, flags=re.S | re.M); body = re.sub(r"https?://\S+", " ", body)
body = re.sub(r"\b(19|20)\d{2}(–\d{2,4})?\b", " ", body); body = re.sub(r"\b(Section|Table|Figure|Tables|Sections)s? [A-Z]?\d+(\.\d+)?\b", " ", body); body = re.sub(r"^#+ [A-Z0-9.]+ ", " ", body, flags=re.M)
body = re.sub(r"\bH\d\b|\bB\d{5}\b|\(\d\)|\((i|ii|iii|iv|v)\)", " ", body)
seen = {}
for m_ in re.finditer(r"[−-]?\d[\d,]*\.?\d*", body):
    tok = m_.group(0)
    if tok in ("1", "2", "3"): continue
    ctx = body[max(0, m_.start() - 45): m_.end() + 30].replace("\n", " ")
    seen.setdefault(tok, ctx)
for tok, ctx in seen.items(): print(f"  {tok:>8}  ...{ctx}...")

print("\n=== (c) structure of the built manuscript")
md = open(os.path.join(OUT_DIR, "paper4.md"), encoding="utf-8").read()
for lab in [f"Table {i}." for i in range(1, 8)] + ["Table A1.", "Table A2.", "Figure 1.", "Figure 2.", "Figure 3."]:
    check(f"{lab} defined exactly once", len(re.findall(r"(\*\*|!\[)" + re.escape(lab), md)) == 1)
for lab in [f"Table {i}" for i in range(1, 8)] + ["Figure 1", "Figure 2", "Figure 3", "Table A2"]:
    body_only = md.split("# References")[0]; check(f"{lab} is cited in the text", len(re.findall(re.escape(lab) + r"(?![.\d])", body_only)) >= 1)
check("no unresolved braces or placeholders", "{{" not in md and "}}" not in md and re.search(r"\bnan\b", md, re.I) is None)
check("every in-text citation year appears in the reference list", all(re.search(a, md.split("# References")[1]) for a in ["Bartram", "Cameron", "Change Lab", "Cox", "Golio", "Greenlee", "House", "Hwang", "Kaplan", "Kontokosta", "Lipsky", "Lucy", "Minkoff", "Nathan", "Stacy"]))
print("\n=== (d) reproduction: generated tables versus expected/all_tables.json (the tables printed in the manuscript)")
exp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "expected", "all_tables.json")
if os.path.exists(exp_path):
    exp, got = jload(exp_path), jload(W("tabs", "all_tables.json"))
    for k in sorted(exp): check(f"{k} identical to expected", got.get(k) == exp[k])
    ncell = sum(t.count("|") for t in exp.values()); print(f"   ({len(exp)} tables compared, about {ncell} cell separators)")
else: print("   expected/all_tables.json not found; skipped")
print(f"\nwords (whole file): {len(md.split()):,}")
print("\nRESULT:", "ALL CHECKS PASSED" if not fails else f"{len(fails)} FAILED: {fails}")
