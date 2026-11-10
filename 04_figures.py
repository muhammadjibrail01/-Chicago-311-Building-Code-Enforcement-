"""Step 4: figures. Fig. 1 rates by quartile and trigger; Fig. 2 Kaplan-Meier compliance curves; Fig. 3 year-by-year gradients."""
from common4 import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from statsmodels.duration.survfunc import SurvfuncRight
v = pd.read_pickle(W("viol.pkl")); desc = pd.read_csv(W("tabs", "quartile_desc.csv"), index_col="q"); C = jdict = jload(W("counts.json"))
plt.rcParams.update({"font.size": 9})
# Figure 1
fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=200); bottom = np.zeros(4)
cols = {"complaint": "#7A1F2B", "periodic": "#2F6690", "permit": "#A8A8A8"}
labels = {"complaint": "Complaint-driven", "periodic": "Routine (periodic)", "permit": "Permit-triggered"}
for c in ("complaint", "periodic", "permit"):
    ax.bar(["Q1\n(lowest)", "Q2", "Q3", "Q4\n(highest)"], desc[c].values, bottom=bottom, color=cols[c], label=labels[c], width=0.6); bottom += desc[c].values
ax.set_ylabel("Violations per 1,000 residents per year"); ax.set_xlabel("Tract hardship quartile"); ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.spines[["top", "right"]].set_visible(False); plt.tight_layout(); plt.savefig(W("figs", "fig1_rates.png")); plt.close()
# Figure 2
fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4), dpi=200, sharey=True); qcol = {"Q1": "#2F6690", "Q2": "#7FA7C9", "Q3": "#E0A458", "Q4": "#7A1F2B"}
for ax, (title, sel) in zip(axes, [("(a) All violations", None), ("(b) Complaint-driven only", "COMPLAINT")]):
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        s = v[(v.q == q) & (True if sel is None else (v.cat == sel))]; S = SurvfuncRight(s["time"].values, s["complied"].values)
        st, sp = np.asarray(S.surv_times), np.asarray(S.surv_prob); grid = np.linspace(1, 1825, 400); idx = np.searchsorted(st, grid, side="right") - 1
        ax.plot(grid / 365.25, 1 - np.where(idx >= 0, sp[np.clip(idx, 0, None)], 1.0), color=qcol[q], label=q, lw=1.6)
    ax.set_title(title, fontsize=9); ax.set_xlabel("Years since violation"); ax.spines[["top", "right"]].set_visible(False)
axes[0].set_ylabel("Cumulative share complied (Kaplan–Meier)"); axes[1].legend(frameon=False, fontsize=8, title="Hardship quartile", title_fontsize=8)
plt.tight_layout(); plt.savefig(W("figs", "fig2_compliance.png")); plt.close()
# Figure 3
yrs = list(range(2019, 2025)); fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=200)
for k, off in (("complaint", -0.12), ("periodic", 0.0), ("permit", 0.12)):
    irr = np.array([C[f"year{y}_{k}"]["hard_z"]["irr"] for y in yrs]); lo = np.array([C[f"year{y}_{k}"]["hard_z"]["lo"] for y in yrs]); hi = np.array([C[f"year{y}_{k}"]["hard_z"]["hi"] for y in yrs])
    ax.errorbar(np.array(yrs) + off, irr, yerr=[irr - lo, hi - irr], fmt="o", ms=4, capsize=2, color=cols[k], label=labels[k])
ax.axhline(1, color="black", lw=0.8, ls="--"); ax.set_ylabel("Incidence rate ratio per SD of hardship"); ax.set_xlabel("Year of violation")
ax.set_xticks(yrs); ax.legend(frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(W("figs", "fig3_years.png")); plt.close(); print("figures written")
