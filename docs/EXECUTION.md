# Executed verification

Executed on October 15, 2026 in the user-supplied Git repository on Windows.

* Python 3.12.14; pandas 3.0.6; scikit-learn 1.9.1; matplotlib 3.11.2.
* Created a fresh `.venv` inside the actual destination repository using `tools/run.ps1 -Python <working Python executable>`, exactly the README's supported full-path alternative. The available bundled Python runtime was used because the system Python alias was not functional.
* Installed every pinned dependency. An initial network/DNS failure was resolved after network access was granted; installation and execution then completed with exit code 0.
* All **11 tests passed**. Full preparation, both forecasts, validation selection, final test, forecast demonstration and figure generation completed.
* Repeated the documented pipeline command with `--output .tmp/reproduction`. All **13 output files** were byte-identical, including metrics, predictions, decision, coverage and plots. This was a reproducibility check, not additional model tuning.
* Independently checked unique region/day keys, available features, nonmissing model inputs, 27 registry entries, 23 numeric forecasts, and missing forecasts for all excluded territories. Unknown actual-alert completeness remains missing for every region.
* Visually inspected all three generated figures; region labels, legends and date axes are readable.
* Checked local README/source-document links. Retained the existing repository license and ignore rules.

Machine-readable hashes and environment: [execution_record.json](execution_record.json).

Not executed or established: prospective live forecasting, guaranteed first-publication times, true alert completeness, cross-platform runs, or GitHub publication. Repository changes remain local and ready to review/commit. No API token is needed for this version.

## Second iteration: improved ML and dashboard

The updated README runner completed successfully with 15 tests, both experiments and dashboard export. A repeat of the improved pipeline produced 9 byte-identical files. All README/local documentation links checked here resolve. See [improved_execution.json](improved_execution.json), [model comparison](IMPROVEMENT.md) and [browser/deployment checks](DASHBOARD.md). The original execution record above remains a historical record, not the latest test count.

## Third iteration verification

See [V3_VERIFICATION.json](V3_VERIFICATION.json) and [status/blocks](V3_STATUS.md). Thirty-two Python tests passed; minimal-DOM checks covered 81 regional/period states. Independently recomputed 4,623 validation and 1,748 diagnostic windows. New browser layout, hosted publication and real Telegram delivery are not claimed as tested.

## Original checkout synchronization and current hosted verification — October 16

The prepared version was copied into the original user repository with an external backup and intact Git history. `tools/run.ps1` completed from that directory with exit code 0 and 32 tests. Node checked all 81 states; the bot's no-token Kyiv/three-day dry-run succeeded. Thirteen probability outputs and six public website files matched the verified delivery bytes. The `/site` ignore rule was corrected so the UI can be committed. See ORIGINAL_CHECKOUT_VERIFICATION.json.

The private Site was then updated successfully through the official source/package/deploy flow. Authenticated desktop interaction and visual map checks passed, with no console errors, after explicit owner sign-in approval. See DASHBOARD.md and SITE_V3_DEPLOYMENT.json. The original unavailable-access status has been superseded; live Telegram delivery, mobile UI QA and GitHub push remain unperformed.
