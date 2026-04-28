# Bean Forge BV — universe context

## The company in one line

Bean Forge BV — Utrecht, NL — precision drum coffee roasters for specialty roasters worldwide. 25 people. Founded 1987. Third-generation family business. The hook: every machine is calibration-roasted by Chief Engineer Bram Visser before it ships.

## Tone & story rules

- **B2B industrial, documentary realism.** Not corporate-stock, not glossy. Monocle-magazine feel.
- **International cast, 25 people.** Deliberately diverse. When adding new people, maintain the balance.
- **Plausible, not real.** Customer/supplier names are invented — no Stumptown, no Siemens.
- **Exports 80%+.** Customers are specialty roasters, chains, and academia worldwide; suppliers concentrate in EU.

## Story canon

Full narrative in [story/company.md](story/company.md). Everything referenced by slug (`teun-boon`, `forge-studio`, …) — see sibling YAMLs.

## When editing this universe

- Edit the relevant YAML/MD file, not the generated Odoo records — the YAML is source of truth.
- Re-run population to reconcile (idempotent via slugs).
- Keep the cast balanced (headcount = 25, international mix).
- New customers: fit the specialty-coffee B2B story. If they don't, propose a story change first.

## Recommended Odoo apps

See [story/odoo-apps.yaml](story/odoo-apps.yaml). Core flow: Sales + CRM + Purchase + Inventory + Manufacturing + Accounting + HR. Story-driven additions: PLM (Hybrid R&D), Quality (Bram's calibration ritual), Field Service (Viktor's installs), Project + Timesheets (R&D + billable installs), Subscriptions (Forge Control SaaS), Maintenance (annual contracts).

## Image generation

Presets live in [images/flux-presets.yaml](images/flux-presets.yaml). Brand palette: warm neutrals, brushed stainless, brass, espresso brown. Generate via `scripts/generate_images.py --universe bean-forge …`.
