# Populating an Odoo DB from this data

This is a hand-driven workflow today. Claude Code reads the YAML files and issues MCP calls via `mcp__claude_ai_Odoo_MCP__*`. Future work: a batch script.

## Pre-flight checks

1. Confirm the target DB (Odoo.sh instance, local Docker, etc.) and that the Odoo MCP is pointed at it.
2. Confirm the apps that will receive data are installed: `contacts`, `hr`, `crm`, `sale_management`, `purchase`, `stock`, `mrp`, `project`, `account`.
3. For reruns, slugs in YAML map to `__import__.<slug>` external IDs — idempotent. Dropping + recreating the DB resets everything.

## Layer order (dependencies matter)

1. **Company identity** — update `res.company` (name, country, currency, logo placeholder). Optionally create a second company for multi-company demo.
2. **Users + HR departments** — [`employees.yaml`](../story/employees.yaml). Create `res.users` (for leadership + sales/marketing) and `hr.employee` for production/support. Managers set after all IDs known (two-pass).
3. **Departments + job positions** — from `department` field on employees.
4. **Suppliers + customers (`res.partner`)** — [`suppliers.yaml`](../story/suppliers.yaml) + [`customers.yaml`](../story/customers.yaml). Set `supplier_rank`/`customer_rank` accordingly. Link account execs via `user_id`.
5. **Product categories + products** — [`products.yaml`](../story/products.yaml). Create categories first (Forge / Accessories / Spares / Services), then `product.template` records. Components referenced by BOMs (`chassis-studio`, `drum-assembly-studio`, etc.) are implicit — create them as internally-routed products.
6. **Bills of materials** — [`boms.yaml`](../story/boms.yaml). Multi-level: create sub-assembly BOMs first, then top-level.
7. **CRM stages + pipeline** — [`crm-pipeline.yaml`](../story/crm-pipeline.yaml). Ensure standard stages exist; create leads with `stage_id`, `expected_revenue`, `date_deadline`, `user_id` (salesperson).
8. **Projects + tasks** — [`projects.yaml`](../story/projects.yaml). `project.project` + `project.task`. Billable projects link to customer partner.
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

## Images

Not yet generated. When we have a FLUX API key (or similar):
- Employees: headshots from the cast, prompt includes nationality + role + "professional headshot, warm friendly, workshop setting in background"
- Products: four roaster types, stainless steel workshop aesthetic
- Company logo: Bean Forge wordmark + anvil/bean hybrid mark

Images get uploaded via `image_1920` on `res.users`, `hr.employee`, `product.template`, `res.company`.
