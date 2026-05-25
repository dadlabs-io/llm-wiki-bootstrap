---
name: wiki-verify
description: Verify a wiki entry — flip its truth-status from unverified → verified via sidecar update, recording who certified, when, and (optionally) what evidence. Enforces the icarus invariant that entries CANNOT self-certify on initial write. Use when the user says "verify this entry", "wiki-verify", "/wiki-verify", "mark X as verified".
---

> **🛠️ Public-facing skill.** Invoked by the user (or by an automated process like Aardvark-style PoC validation) when an entry's claims have been confirmed against evidence.

# /wiki-verify

First-class verify primitive per [icarus-integration-plan.md §5](../topic-template/wiki/best-practices/framework/icarus-integration-plan.md). Sets `verified: verified` on an entry's sidecar, recording who certified and when.

## Usage

```
/wiki-verify <slug> --topic <topic> [options]
/wiki-verify wiki/active/foo-2026.md --topic agentic-design
/wiki-verify foo-2026 --topic agentic-design --by tool --evidence "Aardvark sandbox-verified 3 PoCs"

# Mirror back into entry frontmatter (default off — sidecar is the truth):
/wiki-verify <slug> --topic <topic> --mirror

# Dry-run:
/wiki-verify <slug> --topic <topic> --dry-run
```

## Why this exists

icarus's invariant: `verified: verified` cannot be set on initial write. The reason is structural — an entry cannot be both author and certifier of its own claims. The verify step is **decoupled** so the act of certification is auditable (who, when, on what basis).

This means:
- New entries from `/wiki-update` start as `verified: unverified` (or no field, treated as unverified).
- A separate `/wiki-verify` invocation is the ONLY way to flip an entry to `verified: verified`.
- The lint script (`wiki-lint-mechanical.py --strict`) rejects entries whose initial frontmatter claims `verified: verified` — caught at CI.
- The sidecar pattern (memory-signals doc §2) means the verify event doesn't dirty the entry file by default — keeps git history clean for telemetry-class writes.

## Hard rules

1. **`--by` is required for non-human verification.** Default is `human` (editorial signoff). Pass `--by agent` for LLM judge verification, `--by tool` for sandbox/test/static-analyzer verification (Aardvark-style).
2. **Cannot directly verify `contradicted` or `rolled_back` entries.** Script exits 1 with an explanation. If you want to restore an entry that's been contradicted/rolled-back, the path is: review the conflict → write a new revising entry → verify the new entry. Not "force-verify the broken one."
3. **Already-verified entries are a no-op.** Script exits 0 with `status: no-op-already-verified`. Don't re-verify; it's idempotent.
4. **Default keeps frontmatter clean.** Sidecar holds the authoritative `verified` value; frontmatter mirror is off by default to avoid git noise. Pass `--mirror` only when you specifically want the frontmatter field to be in sync (e.g., for downstream tools that can't read the sidecar).

## What You Must Do When Invoked

### Step 1 — Resolve target + check current state

Run the script with `--dry-run` first if you want to preview, otherwise go straight to execute. The script will refuse with explicit messages on:
- Slug not found
- Slug ambiguous (matches multiple entries) — disambiguation list printed
- Entry is `contradicted` or `rolled_back` (use the alternate-path workflow)
- Entry is already `verified` (no-op, idempotent success)

### Step 2 — Run the verify

```bash
python bootstrap/workflows/llm-wiki/scripts/wiki-verify.py "<slug>" \
    --topic "<topic>" \
    --by "<human|agent|tool>" \
    [--evidence "<one-line description>"] \
    [--mirror] \
    [--dry-run]
```

### Step 3 — Report the JSON summary to the user

The script emits a JSON summary on stdout:

```json
{
  "status": "verified",
  "target": "wiki/active/foo-2026.md",
  "verified_by": "human",
  "verified_at": "2026-05-25T...",
  "evidence": "Re-checked against arxiv 2502.12110 §4.2",
  "frontmatter_mirrored": false,
  "sidecar": "_signals/foo-2026.json"
}
```

Show the user: target, verified_by, verified_at, evidence, sidecar path. If `frontmatter_mirrored: true`, also note that the entry file was edited.

### Step 4 — Post-verify hygiene

If the entry's frontmatter was mirrored (`--mirror`), re-run the integration scripts so the change propagates to backlinks/INDEX/MAP:

```bash
python bootstrap/workflows/llm-wiki/scripts/wiki-reciprocate-backlinks.py --topic <topic> --vault <vault>
```

(If only the sidecar was touched, no integration-script re-run needed — sidecars aren't indexed by those scripts.)

### Step 5 — Commit

One commit per verification. Message format:

```
wiki: verify <entry-slug> (by=<who>)

[Evidence: <one-line description, if provided>]

Sidecar updated: verified=verified, verified_at=<iso>, verified_by=<who>.
[Frontmatter mirrored: yes/no]
```

## Evidence-by-role conventions

- **`--by human`** + `--evidence "<one line>"`: editorial signoff. Evidence is the human's note about what they checked.
- **`--by agent`** + `--evidence "<one line>"`: LLM judge or automated review. Evidence should cite the model + the verification prompt template version.
- **`--by tool`** + `--evidence "<one line>"`: sandbox / test / static-analyzer signal. Evidence should cite the tool + the artifact (e.g., "Aardvark sandbox-verified PoCs for CVE-2024-XXXX, run id abc123").

## Pairs with /wiki-rollback

The verify step is the OTHER half of the truth-status lifecycle. Without verified ancestors, `/wiki-rollback` always refuses (no anchor to restore to). The expected pattern:

1. Entry ingested as `verified: unverified` (default)
2. Human or tool verifies → `verified: verified` via this skill
3. Later, a newer entry revises the verified one. Newer is also `unverified` initially.
4. If the newer one turns out wrong, `/wiki-rollback <newer>` walks back to the verified ancestor.

Without step 2, step 4 fails.

## Don't

- Don't mass-verify everything in a wiki without per-entry evidence — verification is an intentional editorial act, not a batch metadata pass.
- Don't pass `--mirror` by default — keep frontmatter clean unless a downstream tool requires the field.
- Don't try to "force-verify" a contradicted or rolled-back entry — the alternative-path workflow (review → new revising entry → verify new) exists for a reason.
- Don't skip `--evidence` for tier-1 / tier-2 entries — those are the entries most likely to be cited from /wiki-rollback decisions later; provenance matters.

## Related

- [icarus-integration-plan.md §5](../topic-template/wiki/best-practices/framework/icarus-integration-plan.md)
- [memory-signals-sidecar-vs-frontmatter-pattern.md](../topic-template/wiki/best-practices/framework/memory-signals-sidecar-vs-frontmatter-pattern.md) — sidecar truth-status block this writes
- [wiki-rollback SKILL.md](../wiki-rollback/SKILL.md) — the other half of the lifecycle
- [wiki-frontmatter-best-practices.md](../topic-template/wiki/best-practices/framework/wiki-frontmatter-best-practices.md) — the optional `verified:` field
