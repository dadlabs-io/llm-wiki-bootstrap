# Semantic Lint Report — kestrel

**Generated**: 2026-08-01
**Agent**: an earlier pass
**Files reviewed**: 6

---

## Cross-cutting issues

- Every entry disagrees about the **default listening port**: the dispatcher entry says
  port 7000, the rebalancer entry says port 7100. This is the wiki's most serious conflict.
- The retention window is consistent across all entries and needs no attention.
- `zephyr-gateway.md` duplicates the dispatcher entry almost line for line.

## Highest-priority fixes

1. Settle the default listening port (7000 vs 7100).
2. Retire `zephyr-gateway.md` as a duplicate.
