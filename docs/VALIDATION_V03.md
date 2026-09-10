# Validation record · v0.3

Executed locally on 10 September 2026: Python 3.12.14, Linux x86_64, Node.js and
host g++. **56 tests passed, no failures or skips.** Raw output is retained in
[`tests.txt`](../results/v0.3/tests.txt).

Coverage includes analytical equilibrium force, exponential memory decay,
approach damping, friction direction, no-contact reset, invalid-input reset,
force/slew bounds, immutable exports, identifiable versus rank-deficient designs,
and held-out synthetic parameter recovery. Python/JavaScript parity compares
every output field for three models and two protocols at independently varied
parameters, with absolute tolerance 1e-9.

Default controlled-run metrics are in
[`comparison.json`](../results/v0.3/comparison.json). The parameter-recovery
self-check, including all training and held-out points, is in
[`identification.json`](../results/v0.3/identification.json).

Browser interaction and responsive-layout checks are configured in
[`browser_smoke.cjs`](../tools/browser_smoke.cjs). Local browser preview was
unavailable. The GitHub integration returned HTTP 403 when asked to create the
feature branch, so GitHub Actions execution and screenshot inspection are pending.
Do not interpret configured browser checks as already passed.

No remote branch, commit, pull request, tag or Pages deployment was created by
this delivery. The proposed code is supplied as a source bundle and an applicable
Git patch against the public v0.2.1 baseline.

The validation scope excludes Unity Editor, tracked XR, physical devices,
AVR deployment and participant experiments.
