# Claude Code Context

This repo is a **multi-universe** source-of-truth for fictional companies used to populate engaging demo data in Odoo databases. Each "universe" is a self-contained fictional company (identity, cast, product catalog, CRM pipeline, BOMs, imagery) that can be loaded into an Odoo DB via Claude Code + the Odoo MCP server.

## What this repo is

- A curated, versioned dataset (YAML + Markdown), **not** an Odoo module.
- One folder per universe under [universes/](universes/). Add a new folder to add a new fictional company.
- Shared, universe-agnostic tooling lives in [scripts/](scripts/). Scripts take a `--universe <slug>` flag.

## What this repo is NOT

- Not a Python package. No `__manifest__.py`, no `depends`.
- Not auto-loaded by Odoo. Data gets into Odoo via explicit MCP calls.
- Not localized. English only — the demo audience is global.

## Universes

| Slug | Vibe | Identity |
|---|---|---|
| [`bean-forge`](universes/bean-forge/) | B2B industrial, documentary realism | Dutch precision coffee-roaster manufacturer (Bean Forge BV). See [universes/bean-forge/CLAUDE.md](universes/bean-forge/CLAUDE.md). |
| [`unicorn-inc`](universes/unicorn-inc/) | Cheerful fantasy, joyful storybook | Cooperative of fabelwezens supplying real superpowers — pegasus wings, dragon fire, mammoth fur. See [universes/unicorn-inc/CLAUDE.md](universes/unicorn-inc/CLAUDE.md). |
| [`provisional-bureau`](universes/provisional-bureau/) | Boutique services, dry satirical edge | Amsterdam brand strategy & design studio (The Provisional Bureau). Project + retainer revenue, three loud founders, a cast that does the actual work. See [universes/provisional-bureau/CLAUDE.md](universes/provisional-bureau/CLAUDE.md). |

Each universe has its own `CLAUDE.md` with story rules and tone — read it before editing content in that universe.

## Working principles (repo-wide)

1. **Pick a universe first.** Every edit is inside one universe's folder. Don't mix.
2. **Story coherence > completeness.** Adding a new customer or product must fit the universe it's in. If it doesn't, propose a change to the story first.
3. **Plausible, not real.** No real companies, no real trademarks, no real people. All fiction.
4. **Idempotency via slugs.** Every record has a slug ID. MCP populations use `__import__.slug` external IDs so reruns don't duplicate.
5. **Dates are often relative.** Population code shifts dates so sales orders / CRM leads always look "recent" — don't hardcode recent dates into YAML unless explicitly intended.

## When populating an Odoo DB from this data

Follow [scripts/populate.md](scripts/populate.md) for layer order. The dependency chain matters: company → users → partners → products → BOMs → everything else.

Use `mcp__claude_ai_Odoo_MCP__*` tools. Prefer `create_records` (bulk) over `create_record` (single) when loading a file's worth of data. Always ask the user which universe to load before starting.

## Adding a new universe

1. `mkdir universes/<slug>/{story,images}` and add a short `CLAUDE.md` describing the identity, tone, and any universe-specific schema quirks.
2. Copy [universes/bean-forge/images/flux-presets.yaml](universes/bean-forge/images/flux-presets.yaml) as a starting point and rewrite for the new brand.
3. Fill in `story/company.md` (narrative) and the YAMLs (employees, products, customers, etc.) — same schemas as Bean Forge; see [ARCHITECTURE.md](ARCHITECTURE.md).
4. Test image generation with `python scripts/generate_images.py --universe <slug> logo --dry-run`.

## Schema reference

See [ARCHITECTURE.md](ARCHITECTURE.md) for per-file YAML schemas — they're the same across universes.
