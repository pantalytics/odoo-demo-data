# Populating an Odoo DB from this data

This is a hand-driven workflow today. Claude Code reads the YAML files for a **chosen universe** and issues MCP calls via `mcp__claude_ai_Odoo_MCP__*`. Future work: a batch script.

## Pre-flight checks

1. **Choose the universe** to load (e.g. `bean-forge`, `unicorn-inc`, `provisional-bureau`). Every path below is relative to `universes/<slug>/`.
2. Confirm the target DB (Odoo.sh instance, local Docker, etc.) and that the Odoo MCP is pointed at it.
3. Install the apps the chosen universe needs — see `story/odoo-apps.yaml` for the per-universe list (typical core: `contacts`, `hr`, `crm`, `sale_management`, `account`; product universes add `purchase`, `stock`, `mrp`; services-led universes add `project`, `hr_timesheet`, `sale_subscription`).
4. For reruns, slugs in YAML map to `__import__.<slug>` external IDs — idempotent. Dropping + recreating the DB resets everything.

## Layer order (dependencies matter)

All paths assume you've chosen a universe slug `<u>` — read files from `universes/<u>/story/`.

1. **Company identity** — update `res.company` from `story/company.md` (name, country, currency, logo placeholder). Optionally create a second company for multi-company demo.
2. **Users + HR departments** — `story/employees.yaml`. Create `res.users` (for leadership + sales/marketing) and `hr.employee` for production/support. Managers set after all IDs known (two-pass).
3. **Departments + job positions** — from `department` field on employees.
4. **Suppliers + customers (`res.partner`)** — `story/suppliers.yaml` + `story/customers.yaml`. Set `supplier_rank`/`customer_rank` accordingly. Link account execs via `user_id`.
5. **Product categories + products** — `story/products.yaml`. Create categories first, then `product.template` records. Components referenced by BOMs are implicit — create them as internally-routed products.
6. **Bills of materials** — `story/boms.yaml` *(skip for services-only universes that ship no `boms.yaml`, e.g. `provisional-bureau`)*. Multi-level: create sub-assembly BOMs first, then top-level.
7. **CRM stages + pipeline** — `story/crm-pipeline.yaml`. Ensure standard stages exist; create leads with `stage_id`, `expected_revenue`, `date_deadline`, `user_id` (salesperson).
8. **Projects + tasks** — `story/projects.yaml`. `project.project` + `project.task`. Billable projects link to customer partner.
9. **Sales orders** *(not yet in YAML)* — generated on population, spread across last 180 days, tied to won leads. Mix of quotations + confirmed orders + delivered orders.
10. **Purchase orders** *(not yet in YAML)* — generated, tied to supplier + product components.
11. **Invoices** *(not yet in YAML)* — vendor bills + customer invoices, mix of paid/open/overdue.

## Idempotency convention

Every record uses an external ID of the form `pan_demo_data.<slug>`. On re-run, `import_records` / MCP finds existing records by external ID and updates in place rather than duplicating.

## Dates: fixed vs. relative

YAML holds absolute dates for narrative clarity. At population time, offset them so the pipeline always shows "recent" activity. Recommended:

- **anchor_now** = today
- **anchor_yaml** = YAML's reference date (e.g., `2026-04-24`)
- Shift all CRM / project / order dates by `anchor_now - anchor_yaml`.

This means: as long as the YAML is internally consistent, the demo always feels fresh.

## Images (FLUX via Black Forest Labs)

API key in `.env` as `BFL_API_KEY`. Docs: https://docs.bfl.ai/

Generation is driven by [`generate_images.py`](generate_images.py) with a `--universe` flag. Per-universe brand style and prompt templates live in `universes/<u>/images/flux-presets.yaml`; output lands in `universes/<u>/images/generated/<kind>/<slug>.jpg`.

**Conventions:**
- Use the **cheaper models** (`flux-dev`, `flux-schnell`) rather than `flux-pro-1.1` — quality is fine for demo headshots + product shots, cost is a fraction.
- **One image per request.** Don't batch; the API is per-item anyway and it keeps retries cheap.
- **Async flow** — the API is asynchronous:
  1. `POST /v1/<model>` with prompt → returns `{ id, polling_url }`
  2. Poll `polling_url` every 2-3s until `status == "Ready"` → download from `result.sample`
  3. Save to `universes/<u>/images/generated/<kind>/<slug>.jpg`, upload to Odoo via `image_1920` field
- Don't poll faster than ~2s — BFL rate-limits.

**Prompt templates:** per-universe, in `universes/<u>/images/flux-presets.yaml` under `templates:`. Brand voice and style are layered on top via the `brand:` and `types:` blocks in the same file.

Images get uploaded via `image_1920` on `res.users`, `hr.employee`, `product.template`, `res.company`.
