# Claude Code Context

This repo is the source-of-truth for **Bean Forge BV**, a fictional B2B coffee roaster manufacturer used to populate engaging demo data in Odoo databases.

## What this repo is

- A curated, versioned dataset (YAML + Markdown), **not** an Odoo module.
- The content here is consumed by Claude Code + the Odoo MCP server to populate a live Odoo DB with a coherent, story-driven demo.
- Every person, customer, and supplier is fictional. No real trademarks.

## What this repo is NOT

- Not a Python package. No `__manifest__.py`, no `depends`.
- Not auto-loaded by Odoo. Data gets into Odoo via explicit MCP calls.
- Not localized. English only — the demo audience is global.

## Working principles

1. **Story coherence > completeness.** Adding a new customer or product must fit the Bean Forge universe. If it doesn't, propose a change to the story first.
2. **Plausible, not real.** Customer names, supplier names, product names must be invented. No real companies (no Stumptown, no Whole Foods, no Siemens, etc.).
3. **International by design.** The 25-person cast is deliberately diverse. When adding new people, maintain that balance.
4. **Idempotency via slugs.** Every record has a slug ID. MCP populations use `__import__.slug` external IDs so reruns don't duplicate.
5. **Dates are often relative.** Population code shifts dates so sales orders / CRM leads always look "recent" — don't hardcode recent dates into YAML unless explicitly intended.

## When populating an Odoo DB from this data

Follow [scripts/populate.md](scripts/populate.md) for layer order. The dependency chain matters: company → users → partners → products → BOMs → everything else.

Use `mcp__claude_ai_Odoo_MCP__*` tools. Prefer `create_records` (bulk) over `create_record` (single) when loading a file's worth of data.

## When editing the story

- Edit the relevant YAML/MD file, not the generated Odoo records directly — the YAML is the source of truth.
- Re-run population to reconcile (idempotent via slugs).
- Keep the cast balanced (headcount = 25, international mix).

## Schema reference

See [ARCHITECTURE.md](ARCHITECTURE.md) for per-file YAML schemas.

## The company in one line

Bean Forge BV — Utrecht, NL — precision drum coffee roasters for specialty roasters worldwide. 25 people. Founded 1987. Third-generation family business. The hook: every machine is calibration-roasted by Chief Engineer Bram Visser before it ships.
