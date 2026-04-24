# odoo-demo-data

Source-of-truth for **Bean Forge BV** — a fictional B2B manufacturer used to populate engaging, representative demo data in Odoo databases.

The story, cast, product catalog, customer roster, CRM pipeline, BOMs and projects live here as versioned YAML/Markdown. When we want a fresh Odoo demo DB, we replay this content via MCP against a target Odoo instance.

## Why this exists

- **Engagement** — prospects should recognize real manufacturing workflows in a story that's memorable, not "Company XYZ / Product A / Partner 1"
- **Reproducibility** — any dropped DB can be repopulated from this repo
- **Iterable** — the story can evolve in git, with diffs and history
- **Legally clean** — every person, customer, and supplier is fictional. No real trademarks.

## Repo layout

```
odoo-demo-data/
├── README.md               you are here
├── ARCHITECTURE.md         schema + conventions + how data flows to Odoo
├── CLAUDE.md               project context for Claude Code
├── LICENSE                 MIT
├── story/                  the data
│   ├── company.md          company identity + narrative hook
│   ├── employees.yaml      25-person cast
│   ├── products.yaml       product lines + pricing
│   ├── customers.yaml      B2B customer roster (fictional)
│   ├── suppliers.yaml      vendor list (fictional)
│   ├── boms.yaml           bills of materials
│   ├── crm-pipeline.yaml   leads across all stages
│   └── projects.yaml       internal + billable projects
├── images/                 logos, headshots, product shots (generated or curated)
└── scripts/
    └── populate.md         order + notes for populating Odoo via MCP
```

## Using this to populate an Odoo DB

Today: hand-driven via Claude Code + the Odoo MCP server. See [scripts/populate.md](scripts/populate.md) for the layer order.

Future: a batch script that reads all YAML files and issues MCP calls in sequence.

## The company in one line

**Bean Forge BV** — Utrecht-based manufacturer of precision drum coffee roasters for specialty roasters worldwide. Founded 1987. 25 employees. Exports 80%+. Third-generation family ownership. *"If Bram hasn't tasted the first roast, it doesn't ship."*

Full narrative: [story/company.md](story/company.md).

## License

MIT — see [LICENSE](LICENSE). All content is fictional. Use freely for demos, training, screenshots, tutorials.
