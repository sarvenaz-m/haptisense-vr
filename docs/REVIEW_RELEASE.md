# Historical September 5 evidence review

This document describes the earlier local bench additions only. Its copy/commit
instructions are superseded by the v0.3 branch. Use [current methods](RESEARCH_METHODS.md)
and [current validation](VALIDATION_V03.md) for the complete version.
Historical CSV line endings were normalized from CRLF to LF when packaging
v0.3; numerical values were preserved.

Base: `13d65e03220be16da0c27b022c58749cc82272d4` / version 0.2.1.
No existing source files or public website have been rewritten in this delivery.

Additions to review and optionally copy into your repository:

- `src/haptisense/bench.py`
- `firmware/uno_erm_bench/uno_erm_bench.ino`
- `unity/Assets/HaptiSense/Scripts/BenchContactSweep.cs`
- `tests/test_bench.py`, `tests/test_firmware_host.py`, `tests/firmware_host.cpp`
- `tests/firmware_stubs/` (test doubles, never device firmware)
- `tools/reproduce_evidence.py`
- `docs/BENCH_VALIDATION.md`, `docs/REVIEW_RELEASE.md`
- `results/review_2026-09-05/` (explicitly computational)
- `UPSTREAM_SNAPSHOT.json`

Do not overwrite newer remote work. Clone fresh, copy this add-only set, inspect
the diff, run tests, then make a new branch/commit. Use the actual commit ID in
the application; no remote release URL has been fabricated in these documents.

```bash
git clone https://github.com/sarvenaz-m/haptisense-vr.git
cd haptisense-vr
git switch -c hiits949-evidence-review
# Copy the specific additions above using your file manager, preserving folders.
git status --short
git diff --check
python -m pip install -e .
python -m unittest discover -s tests -v
git add src/haptisense/bench.py firmware unity/Assets/HaptiSense/Scripts/BenchContactSweep.cs tests tools docs/BENCH_VALIDATION.md docs/REVIEW_RELEASE.md results/review_2026-09-05 UPSTREAM_SNAPSHOT.json
git diff --cached --stat
# Only after your review:
git commit -m "Add bench adapter candidate and reproducible computational evidence"
git push -u origin hiits949-evidence-review
```

Review/merge using your normal workflow; tag only a version you have actually
validated. Keep the base version unchanged until you decide release semantics.
Do not backdate commits or label local software tests as PHANTOM, VR headset,
physical actuator or participant validation. Passing tests cannot determine an
admissions score and does not establish experienced independent engineering.
