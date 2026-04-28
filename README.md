# odoo-demo-data

Source-of-truth for **fictional companies** used to populate engaging, representative demo data in Odoo databases. Each company lives in its own folder under [`universes/`](universes/) — pick one, load it into an Odoo DB, tell a story.

The cast, product catalog, customer roster, CRM pipeline, BOMs, and projects live here as versioned YAML/Markdown. When we want a fresh Odoo demo DB, we replay a chosen universe's content via MCP against a target Odoo instance.

## Why this exists

- **Engagement** — prospects should recognize real workflows in a memorable story, not "Company XYZ / Product A / Partner 1"
- **Reproducibility** — any dropped DB can be repopulated from this repo
- **Iterable** — stories evolve in git, with diffs and history
- **Legally clean** — every person, customer, and supplier is fictional. No real trademarks.
- **Multi-vibe** — different audiences want different moods; one repo, many universes.

## Universes

| Slug | In one line |
|---|---|
| [`bean-forge`](universes/bean-forge/) | Bean Forge BV — Utrecht-based precision coffee-roaster manufacturer. Documentary-realism B2B industrial vibe. |
| [`unicorn-inc`](universes/unicorn-inc/) | (WIP) Unicorn Inc. — cheerful cooperative of fabelwezens supplying real superpowers (pegasus wings, dragon fire, mammoth fur, …). |

Each universe folder has its own `CLAUDE.md` (identity + tone) and the same YAML schemas (see [ARCHITECTURE.md](ARCHITECTURE.md)).

## Repo layout

```
odoo-demo-data/
├── README.md               you are here
├── ARCHITECTURE.md         schema + conventions + how data flows to Odoo
├── CLAUDE.md               repo-wide project context for Claude Code
├── LICENSE                 MIT
├── scripts/                universe-agnostic tooling (--universe flag)
│   ├── populate.md         order + notes for populating Odoo via MCP
│   ├── generate_images.py  FLUX image generation
│   └── generate_odoo_product_images.py
└── universes/
    └── <slug>/
        ├── CLAUDE.md       story identity for this universe
        ├── story/          company.md + YAMLs
        ├── images/         flux-presets.yaml + generated/
        └── scratch/        (optional) ad-hoc inputs
```

## Using this to populate an Odoo DB

Today: hand-driven via Claude Code + the Odoo MCP server. See [scripts/populate.md](scripts/populate.md) for the layer order. Decide **which universe** first.

Future: a batch script that reads all YAML files of a given universe and issues MCP calls in sequence.

## Generating imagery

```
python scripts/generate_images.py --universe bean-forge logo
python scripts/generate_images.py --universe bean-forge headshots --only teun-boon
python scripts/generate_images.py --universe bean-forge all --dry-run
```

Requires `BFL_API_KEY` in `.env`. See [scripts/populate.md](scripts/populate.md#images-flux-via-black-forest-labs) for the image workflow.

## Adding a new universe

1. Create `universes/<slug>/{story,images}/` and an `CLAUDE.md` describing tone and identity.
2. Copy `universes/bean-forge/images/flux-presets.yaml` as a starting point and rewrite the brand block + presets.
3. Fill in `story/company.md` and the YAMLs — schemas live in [ARCHITECTURE.md](ARCHITECTURE.md).

## License

MIT — see [LICENSE](LICENSE). All content is fictional. Use freely for demos, training, screenshots, tutorials.
