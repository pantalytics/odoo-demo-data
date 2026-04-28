# Architecture

## Repo layout

```
odoo-demo-data/
├── CLAUDE.md, ARCHITECTURE.md, README.md, LICENSE
├── scripts/                         universe-agnostic tooling (--universe flag)
│   ├── populate.md
│   ├── generate_images.py
│   └── generate_odoo_product_images.py
└── universes/
    └── <slug>/                      one fictional company per folder
        ├── CLAUDE.md                story identity + tone for Claude
        ├── story/                   the data (YAML + company.md)
        ├── images/
        │   ├── flux-presets.yaml    brand style + per-type image presets
        │   └── generated/           FLUX output (kind/slug.jpg)
        └── scratch/                 (optional) ad-hoc inputs for tooling
```

All YAML schemas below are universe-agnostic — every universe uses the same files under its `story/` folder. What changes per universe is the content, brand voice, and image style.

## Design choices

**YAML over XML/CSV.** Demo data is meant to be read and edited by humans more than by Odoo's XML loader. YAML files are source-of-truth; they get translated into Odoo records at population time. This keeps the creative story decoupled from Odoo's framework.

**Narrative in Markdown, tabular data in YAML.** Each universe's `story/company.md` is the creative brief; everything else is structured so it can feed into MCP calls (or a future batch importer).

**Every record has a slug ID.** References use slugs (`teun-boon`, `forge-studio`) rather than positional IDs so files can be reordered, appended to, and cross-referenced without breaking links. Population maps slugs → Odoo IDs at runtime.

**Fully fictional.** No real trademarks, no real people, no actual customer data. This matters legally (IP, GDPR) and practically (demos don't age into "wait, that's wrong").

## File schemas

Paths shown are relative to a universe folder (e.g. `universes/bean-forge/`).

### `story/employees.yaml`

The `nationality` field is typically an ISO-3166 alpha-2 code (used to build a realistic headshot prompt), but a universe may use a free-form adjective like `Elven` or `Draconic` — the image generator passes non-ISO values through as-is.

```yaml
- id: teun-boon                 # slug, used as ref elsewhere
  name: Teun Boon
  nationality: NL               # ISO-3166 alpha-2, or a free-form adjective
  role: CEO
  department: Leadership
  manager: null                 # slug ref, or null for top of tree
  email: teun.boon@beanforge.com
  languages: [nl, en, de]
  bio: Third-generation family CEO. Believes roasters are instruments, not appliances.
```

### `story/products.yaml`

Each universe defines its own `category` values. The image generator maps `category` → image preset via the `product_category_presets:` block in `images/flux-presets.yaml`.

```yaml
- id: forge-studio
  name: Forge Studio 15kg
  line: Forge                   # product line grouping
  category: roaster             # universe-specific; see flux-presets.yaml
  uom: Units
  sale_price: 65000             # EUR
  cost_price: 24000
  description: |
    The workhorse 15kg drum roaster for small-to-medium specialty roasters.
    ...
```

### `story/customers.yaml`

```yaml
- id: northwind-roasters
  name: Northwind Roasters
  type: specialty_roaster       # specialty_roaster | chain | academia | foodco
  country: US
  city: Seattle
  segment: key_account          # key_account | mid_market | smb
  account_exec: james-obrien    # ref → employees.yaml
  notes: Bought 2× Studio in 2022. Evaluating Foundry for new facility.
```

### `story/suppliers.yaml`

```yaml
- id: milano-burner-works
  name: Milano Burner Works
  country: IT
  city: Milan
  category: burner              # burner | steel | electronics | packaging | ...
  notes: Sole supplier for Foundry gas burners.
```

### `story/boms.yaml`

Bills of materials. Multi-level allowed via `components` referencing other BOM ids or `product_ref`.

```yaml
- id: bom-forge-studio
  product_ref: forge-studio
  version: 1
  components:
    - product_ref: chassis-studio
      qty: 1
    - product_ref: drum-assembly-studio
      qty: 1
    - product_ref: burner-15kw
      qty: 1
    - product_ref: control-panel-v2
      qty: 1
```

### `story/crm-pipeline.yaml`

```yaml
- id: lead-northwind-foundry
  customer_ref: northwind-roasters
  title: Northwind — Foundry 60kg upgrade for Seattle roastery
  stage: proposition            # new | qualified | proposition | negotiation | won | lost
  amount: 180000
  expected_close: 2026-07-15
  salesperson: james-obrien
  narrative: |
    Customer outgrowing their two Studio 15kg units. Head roaster has asked for a
    side-by-side trial. Blocker: approval from parent group.
```

### `story/odoo-apps.yaml`

Recommended Odoo modules to install for the universe to function. Population scripts can install them in three passes (`core` → `recommended` → `nice_to_have`) by upgrading `ir.module.module` records. Module names are the technical names (`sale_management`, `industry_fsm`, …), not display labels.

```yaml
- module: sale_management
  category: core              # core | recommended | nice_to_have
  reason: Quotations and sales orders for machines.

- module: industry_fsm
  category: recommended
  reason: Worldwide on-site installations (billable field service).

- module: mass_mailing
  category: nice_to_have
  reason: Polaroid-campaign newsletters.
```

### `story/projects.yaml`

```yaml
- id: proj-ecuador-launch
  name: Ecuador single-origin Expeditions launch
  kind: internal                # internal | billable
  lead: priya-raghavan
  start: 2026-02-01
  end: 2026-06-30
  tasks:
    - title: Cocoa/bean origin qualification visit
      assignee: bram-visser
    - title: Marketing campaign kickoff
      assignee: chloe-martin
```

## Flow: YAML → Odoo

1. **Pick a universe** (e.g. `bean-forge`) — the rest of the flow operates within `universes/<slug>/`.
2. **Read the YAML files** in dependency order (see [scripts/populate.md](scripts/populate.md)).
3. **Create Odoo records** via MCP (`create_record` / `create_records`).
4. **Track slug → Odoo ID** in an in-memory dict for back-references (manager, account_exec, product_ref, etc.).
5. **Use `__import__.slug` external IDs** so reruns are idempotent — the same slug maps to the same Odoo record.

Order matters — employees before CRM (because CRM refs salespeople); products before BOMs; BOMs before sales orders; partners before anything that references them. The populate script enforces this order.

## Conventions

- **Slug format**: `kebab-case`, unique within its file
- **Dates**: ISO 8601 (`YYYY-MM-DD`), preferably relative to "now" for sales/CRM data (handled in population, not in YAML — YAML has absolute dates that get shifted if needed)
- **Amounts**: always EUR, whole numbers, no currency symbols
- **Nationality codes**: ISO-3166 alpha-2 uppercase
- **Language codes**: ISO-639-1 lowercase

## Out of scope

- No Python module packaging (this isn't an Odoo addon — it's source data)
- No automated re-population on DB create (that'd need a module; see [odoo-demo repo](https://github.com/pantalytics/odoo-demo) for that future evolution)
- No localization of the story itself (English only; the audience is global)
