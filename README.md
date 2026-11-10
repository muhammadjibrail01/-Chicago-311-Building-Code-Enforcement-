# Replication package: "Reactive Enforcement: Neighborhood Hardship, Inspection Triggers, and Compliance with Building Violations in Chicago, 2019–2024" (Paper 4)

**Tested end to end on 6 November 2026** in an empty folder (Python 3.12, Linux, 4 GB RAM, one CPU). All 8 steps ran in about 11 minutes (step 3, the Cox models and bootstrap, takes 10 of them). Every saved result file and all 8 manuscript tables were identical to the originals, the manuscript text was identical, and `07_audit.py` reported ALL CHECKS PASSED. Steps 6–8 were re-run after the final text edits. The run was repeated from an empty layout using only the default folder settings (`raw_data/` and `../paper1_replication/work/`); all 8 tables and the manuscript text were identical and the audit passed. It builds on Paper 1's package, which supplies the tract measures; run its steps 00 and 02 first.

## 1. Before you start
1. Run steps 00 and 02 of the Paper 1 replication package. They write `tract.csv` (the six-indicator tract hardship index for 789 analytic tracts) and unpack the tract boundary shapefile into Paper 1's work folder. They need only the ACS tract tables, the 2023 tract boundaries, the Historic Redlining Indicator, the HOLC map, Crimes, and Building Violations; they do not need the 311 requests. They also expect a community-area polygon file `ca.gpkg` from the main-paper package. If you do not have it, `python code/make_ca_gpkg.py Boundaries_-_Community_Areas.csv main_work` builds one from the Data Portal CSV.
2. Python 3.10+ (`pip install -r requirements.txt`) and, for step 8 only, Node.js 18+ with `npm install docx`.
3. Place the inputs below in the folders named in `config.py` (by default `raw_data/` and `../paper1_replication/work/` next to this package), or set the environment variables `RAW_DIR`, `P1_WORK` and `WORK_DIR`:

| Input | Where | Files |
|---|---|---|
| Building Violations (two extracts, 2019–2024) | Chicago Data Portal | `Building_Violations*.csv` in `RAW_DIR` |
| Census Data – Selected socioeconomic indicators in Chicago, 2008–2012 | Chicago Data Portal | `Census_Data_-_Selected_socioeconomic_indicators_in_Chicago__2008___2012*.csv` in `RAW_DIR` |
| Tract measures and tract shapefile | Paper 1 package, steps 00 and 02 | `tract.csv`, `data/tracts/cb_2023_17_tract_500k.shp` in `P1_WORK` |

## 2. Run
`python run_all.py` runs all steps in order (about 11 minutes; logs in `work/logs/`). Resume with `--from N`; run one step with `--only N`. Step 3 caches each model in `work/compliance.json`, so an interrupted run resumes where it stopped.

## 3. What each step produces
| Step | Script | Produces | In the paper |
|---|---|---|---|
| 01 | `01_build.py` | Violation-level file located in tracts; sample counts and data checks (`work/meta.json`) | §4, Table 1 |
| 02 | `02_counts.py` | Quartile rates; Poisson count models; trigger-difference test; robustness; year-by-year models (`work/counts.json`) | Tables 2–4, A2; §6.1–6.3, 6.6 |
| 03 | `03_compliance.py` | Kaplan–Meier estimates; eight Cox specifications including the proportional-hazards checks; bootstrapped decompositions (`work/compliance.json`) | Tables 5–7; §6.4–6.5 |
| 04 | `04_figures.py` | Figures 1–3 | Figures |
| 05 | `05_tables.py` | Every table, as markdown, from the saved results | Tables 1–7, A2 |
| 06 | `06_build_manuscript.py` | Resolves every `{{key:format}}` placeholder in your local `manuscript/template_part*.md` and inserts the tables (`manuscript/paper4.md`); an unresolved placeholder stops the build | All text |
| 07 | `07_audit.py` | Tests each claim in the text against the results; lists hand-typed numbers; checks structure. | — |
| 08 | `08_render_docx.py`, `render.js` | Word file, with docx-js | — |

## 4. Editing the manuscript
Prose lives in a local `manuscript/template_part*.md` directory (which you create). Numbers that come from the analysis are placeholders such as `{{c.main_complaint.hard_z.irr:f2}}`, so they cannot drift from the tables. After editing, run `python run_all.py --from 6`. If you change a specification, rerun from step 2 or 3 to regenerate `work/tabs/all_tables.json`.

## 5. Not done, and things to check
See `AUDIT_NOTES.md`: the characterizations of four policy reports and of Bartram (2019a) come from summaries and must be checked against the full texts; the "Special Task Force" bureau could not be matched to the unit studied by Golio et al. (2024); no Schoenfeld-residual tests or second-software cross-checks were run.
