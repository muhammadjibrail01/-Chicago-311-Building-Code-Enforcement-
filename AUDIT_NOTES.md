# Audit notes: "Reactive Enforcement: Neighborhood Hardship, Inspection Triggers, and Compliance with Building Violations in Chicago, 2019–2024"

## Checks performed

| Check | Method | Result |
|---|---|---|
| Claims in the text | `code/07_audit.py` tests each qualitative claim in the text against the saved results (for example, "never significantly above one", "composition share above one half") | 31 of 31 pass |
| Numbers in the text | Every number derived from the analysis is a placeholder resolved from the saved results when the manuscript is built; a placeholder that cannot be resolved stops the build | 0 unresolved |
| Hand-typed numbers | Listed by `07_audit.py`. They are source-data definitions (ages, scales), design values (the 50-violation cell minimum, the 365-day horizon, 500 bootstrap replications), and figures quoted from the companion manuscripts (47 percent; −0.210 and −0.206) | Reviewed |
| Tables | All tables are generated from the saved results (`05_tables.py`) and compared by `07_audit.py` with `expected/all_tables.json` | Identical |
| Source data | 343,671 violation records with no overlapping IDs; all dates parse; no negative durations; every complied violation has a status date; every record has a violation code; records without coordinates, records outside the analytic tracts, and analytic records add up to all records | Pass |
| Tract sample | 789 analytic tracts and 342,757 violations located in Chicago tracts, the same counts as step 02 of the Paper 1 package | Match |
| Kaplan–Meier estimator | The estimator used in the bootstrap equals the statsmodels estimator (`SurvfuncRight`) for all 16 quartile × category groups | Equal to 1e-9 |
| Reproduction | The whole package was run from an empty folder; every saved result file, all eight tables and the manuscript text were identical to the original run; a second run from an empty layout using only the default folder settings gave identical tables and manuscript text and the same audit result | Identical |
| Word file | Rendered with docx-js and checked against an Office Open XML schema validator; checked page by page in a PDF rendering | 16 pages, valid |

## Limits of the verification

* **Sources.** Authors, titles, and years of House (2021), Stacy et al. (2018), Greenlee et al. (2024), Bartram (2019a, 2019b), Golio et al. (2024), and Hwang and Sampson (2014) were confirmed through publisher or index pages. Statements attributed to House (2021) follow the Furman Center's published summary of the brief; statements attributed to Stacy et al. (2018), Greenlee et al. (2024), and Change Lab Solutions (2022) follow excerpts and summaries of those reports. The full reports were not read.
* **"Special Task Force" bureau.** Whether it is the same unit as the Strategic Task Force inspections studied by Golio et al. (2024) could not be confirmed. The text says so, and results are reported with and without those records.
* **Second-software check.** The count and Cox models were not cross-validated against a second package.
* **Proportional hazards.** Checked by stratification, by category-specific models, and by a one-year episode split. Schoenfeld-residual tests were not run.
* **Spatial dependence.** Addressed only by clustering at the community-area level.
* **Companion-paper figures.** The numbers quoted from the main manuscript (47 percent; −0.210; −0.206) were not re-derived here.
* **Enforcement outputs.** Violation counts are outputs of enforcement activity. The extract contains only violations, so inspections that found nothing are not observed.
