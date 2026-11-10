"""Step 5: every manuscript table, written as markdown from the saved results (no hand transcription). Writes work/tabs/table_*.md."""
from common4 import *
M = jload(W("meta.json")); C = jload(W("counts.json")); K = jload(W("compliance.json")); D = pd.read_csv(W("tabs", "quartile_desc.csv"), index_col="q")
def f3(x): return f"{x:.3f}"
def f2(x): return f"{x:.2f}"
def pv(p): return "<0.001" if p < 0.001 else f"{p:.3f}"
def ci(r, d=3): return f"{r['lo']:.{d}f}–{r['hi']:.{d}f}"
def cell(r, d=2): return f"{r['irr']:.{d}f} ({r['lo']:.{d}f}–{r['hi']:.{d}f})"
def pct(x, d=1): return f"{100*x:.{d}f}%"
def n(x): return f"{int(round(x)):,}"
def table(header, rows, widths=None):
    widths = widths or [4] * len(header)
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["-" * w for w in widths]) + "|"]
    for r in rows: out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)
T = {}
# Table 1
cc, st = M["category_counts"], M["status_counts"]; tot = M["rows_in_analytic_tracts"]
rows = [["Building violation records, 2019–2024 (two extracts, no overlapping IDs)", n(M["rows_unique_ids"])],
        ["Without coordinates", n(M["no_coordinates"])], ["Coordinates outside the analytic tracts", n(M["with_coordinates_outside_analytic_tracts"])],
        ["Within the 789 analytic tracts", n(tot)], ["*Inspection category*", ""]]
for k, lab in (("COMPLAINT", "Complaint-driven"), ("PERIODIC", "Routine (periodic)"), ("PERMIT", "Permit-triggered")): rows.append([lab, f"{n(cc[k])} ({pct(cc[k]/tot)})"])
rows.append(["*Status at extraction (23 September 2026)*", ""])
for k, lab in (("COMPLIED", "Complied"), ("OPEN", "Open"), ("NO ENTRY", "No entry")): rows.append([lab, f"{n(st[k])} ({pct(st[k]/tot)})"])
rows.append(["*Violations by year*", ""]); rows.append(["2019 / 2020 / 2021", " / ".join(n(M["rows_by_year"][str(y)]) for y in (2019, 2020, 2021))])
rows.append(["2022 / 2023 / 2024", " / ".join(n(M["rows_by_year"][str(y)]) for y in (2022, 2023, 2024))])
rows.append(["Distinct inspection numbers (inspections that cited at least one violation)", n(M["distinct_inspections"])])
T["TABLE_1"] = table(["Step", "Records"], rows, [14, 6])
# Table 2 (two panels so that no column header wraps mid-word)
rowsA, rowsB = [], []
for q, lab in zip(["Q1", "Q2", "Q3", "Q4"], ["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"]):
    d = D.loc[q]
    rowsA.append([lab, f2(d.complaint), f2(d.periodic), f2(d.permit), f2(d.total), f2(d.inspections)])
    rowsB.append([lab, f2(d.viol_per_inspection), pct(d.complaint_share), pct(d.open_share)])
T["TABLE_2"] = ("*Panel A. Violations and inspections per 1,000 residents per year*\n\n"
                + table(["Quartile", "Complaint-driven", "Routine", "Permit-triggered", "All violations", "Inspections"], rowsA, [5, 5, 4, 5, 5, 5])
                + "\n\n*Panel B. Caseload composition and status*\n\n"
                + table(["Quartile", "Violations per inspection", "Complaint share of violations", "Open at extraction"], rowsB, [5, 5, 5, 5]))
# Table 3
rows = []
for k, lab, rk in (("complaint", "Complaint-driven violations", "race_complaint"), ("periodic", "Routine violations", "race_periodic"), ("permit", "Permit-triggered violations", "race_permit"),
                   ("total", "All violations", "race_total"), ("inspections", "Distinct inspections", None)):
    r = C[f"main_{k}"]["hard_z"]; extra = (f3(C[rk]["hard_z"]["irr"]), f3(C[rk]["black_z"]["irr"])) if rk else ("—", "—")
    rows.append([lab, f3(r["irr"]), ci(r), pv(r["p"]), extra[0], extra[1]])
T["TABLE_3"] = table(["Outcome", "IRR", "95% CI", "p", "Hardship IRR, % Black added", "% Black IRR"], rows, [10, 3, 4, 3, 4, 3])
# Table 4
spec = [("Main tract model (N = 789)", "main_{}"), ("Excluding elevator and boiler bureaus", "excl_elev_boiler_{}"), ("Excluding Special Task Force violations", "excl_stf_{}"), ("Adding % Black (secondary measure)", "race_{}")]
rows = []
for lab, key in spec:
    r = []
    for k in ("complaint", "periodic", "permit"): r.append(cell(C[key.format(k)]["hard_z"]))
    rows.append([lab] + r)
rows.append(["Community areas, official 2008–12 index (N = 77)"] + [cell(C[f"ca_{k}"]) for k in ("complaint", "periodic", "permit")])
T["TABLE_4"] = table(["Specification", "Complaint-driven", "Routine", "Permit-triggered"], rows, [10, 5, 5, 5])
# Table 5
km = pd.DataFrame(K["km"]); g = lambda cat, q, c: km[(km.cat == cat) & (km.q == q)][c].iloc[0]
rows = []
for q, lab in zip(["Q1", "Q2", "Q3", "Q4"], ["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"]):
    rows.append([lab, pct(g("ALL", q, "raw_complied")), pct(g("ALL", q, "km365")), pct(g("COMPLAINT", q, "raw_complied")), pct(g("COMPLAINT", q, "km365")), pct(g("PERIODIC", q, "km365")), pct(g("PERMIT", q, "km365"))])
T["TABLE_5"] = table(["Quartile", "All: raw complied", "All: one-year KM", "Complaint-driven: raw complied", "Complaint-driven: one-year KM", "Routine: one-year KM", "Permit: one-year KM"], rows, [4, 4, 4, 4, 4, 4, 4])
# Table 6
def crow(lab, key, cov="hard_z"):
    r = K[key][cov]; return [lab, f3(r["irr"]), ci(r), pv(r["p"]), n(K[key]["_n"]), n(K[key]["_events"])]
rows = [crow("Hardship, pooled model with category indicators", "cox_pooled"), crow("Hardship, stratified by inspection category", "cox_strat_cat"),
        crow("Hardship, stratified by category and violation year", "cox_strat_cat_year"), crow("Hardship, complaint-driven violations only", "cox_complaint"),
        crow("Hardship, routine violations only", "cox_periodic"), crow("Hardship, permit-triggered violations only", "cox_permit"),
        crow("Hardship, first year after violation", "cox_year1"), crow("Hardship, after the first year", "cox_after_year1"),
        crow("Routine vs. complaint-driven (pooled model)", "cox_pooled", "periodic"), crow("Permit-triggered vs. complaint-driven (pooled model)", "cox_pooled", "permit")]
T["TABLE_6"] = table(["Specification", "HR", "95% CI", "p", "N", "Events"], rows, [12, 3, 5, 3, 4, 4])
# Table 7
a, b = K["decomp_cell_cat"], K["decomp_cell_bureau"]; ca_, cb_ = K["decomp_cell_cat_ci"], K["decomp_cell_bureau_ci"]
pp = lambda x: f"{100*x:.1f}"
def pc(rr): return f"[{100*rr[0]:.0f}%, {100*rr[1]:.0f}%]"
def pr(rr): return f"[{100*rr[0]:.1f}, {100*rr[1]:.1f}]".replace("[-", "[−")
rows = [["Number of cells in common support", a["cells"], b["cells"]],
        ["Share of lowest / highest quartile violations covered", f"{pct(a['cover_q1'])} / {pct(a['cover_q4'])}", f"{pct(b['cover_q1'])} / {pct(b['cover_q4'])}"],
        ["Lowest quartile, own mix (percent complied within one year)", pp(a["R11"]), pp(b["R11"])], ["Highest quartile's rates at the lowest quartile's mix", pp(a["R41"]), pp(b["R41"])],
        ["Highest quartile, own mix", pp(a["R44"]), pp(b["R44"])],
        ["Gap (percentage points) [95% bootstrap interval]", f"{pp(a['gap'])} {pr(ca_['gap'])}", f"{pp(b['gap'])} {pr(cb_['gap'])}"],
        ["Composition effect (percentage points) [interval]", f"{pp(a['comp'])} {pr(ca_['comp'])}", f"{pp(b['comp'])} {pr(cb_['comp'])}"],
        ["Within-cell effect (percentage points) [interval]", f"{pp(a['within'])} {pr(ca_['within'])}", f"{pp(b['within'])} {pr(cb_['within'])}"],
        ["Composition share of gap [interval]", f"{pct(a['comp_share'],0)} {pc(ca_['comp_share'])}", f"{pct(b['comp_share'],0)} {pc(cb_['comp_share'])}"]]
T["TABLE_7"] = table(["Component", "Cells: inspection category", "Cells: category × bureau"], rows, [12, 6, 6])
# Table A2
rows = [[str(y)] + [cell(C[f"year{y}_{k}"]["hard_z"]) for k in ("complaint", "periodic", "permit")] for y in range(2019, 2025)]
T["TABLE_A2"] = table(["Year of violation", "Complaint-driven", "Routine", "Permit-triggered"], rows, [4, 5, 5, 5])
for k, t in T.items(): open(W("tabs", f"{k.lower()}.md"), "w", encoding="utf-8").write(t + "\n")
jdump(T, W("tabs", "all_tables.json")); print("tables written:", ", ".join(T))
