# Doubt log — 242-dcc-test-tidy

no non-trivial decision — steps 1-5 restructure two test files onto one harness and add one check; no assertion was loosened (each re-freeze carries its reason). One judgment: every check of the old suite now builds its own Machine, so the suite installs the hooks 18 times instead of once (slower, but no check depends on another).
