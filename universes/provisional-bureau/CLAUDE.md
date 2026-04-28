# The Provisional Bureau — universe context

## The company in one line

The Provisional Bureau — Amsterdam, NL — boutique brand strategy & design studio for established brands that want to reinvent themselves. 12 people. Founded 2021. Three founder-partners with too-large egos and a quietly competent team that does the actual work.

## Tone & story rules

- **Documentary realism with a dry satirical edge.** Earnest creatives doing genuinely good work, surrounded by the small absurdities of agency life. Not slapstick — the joke lands because the surface is plausible.
- **Boutique, not big.** 12 people, retainer-led, picky about clients. Not a global network. Definitely "we don't do logos, we do legacies"-energy on the website, while internally everyone rolls their eyes at it.
- **Plausible, not real.** No real brands as clients. Some clients are deliberately absurd (Mustardcouch, Carnivore Assurance Group) — these are Multilul-style easter eggs. Most clients are plausible scale-ups, NGOs, museums, hospitality groups.
- **Amsterdam-based, English-speaking.** All comms in English. The cast is international; the founders are mostly Dutch. Mostly EU clients, some US, some UK.

## Story canon

Full narrative in [story/company.md](story/company.md). Everything referenced by slug (`hugo-maartens`, `mustardcouch`, …) — see sibling YAMLs.

## The Multilul / Jiskefet layer (subtle, not loud)

A handful of details reward viewers who recognize the reference. Don't overdo it; if every customer is absurd the universe tips into Unicorn-Inc territory.

- **Mustardcouch** — legacy lifestyle/furniture brand; flagship rebrand engagement. Tagline candidate floated in the deck: *"Sit. Spread."*
- **Carnivore Assurance Group** — meat insurance. RFP currently in CRM.
- **Drive-Thru Farewells** — drive-thru funeral home scaling internationally.
- **Margot Bakker** — Studio Manager, actually runs the place. The three founders refer to her in internal Slack as "the front desk" because they never quite remember her name. She is the most competent person in the building.
- **Hugo, Sam, Indra** — three founder-partners. Loud in meetings, quoted Dieter Rams in last week's all-hands without prompting, take credit for the team's work, are not actually bad at their jobs.

## Odoo coverage this universe is built to demo

- **Project + Timesheets** — billable rebrand engagements with milestones and timesheets.
- **Subscriptions** — monthly brand-stewardship retainers.
- **Sales / CRM** — pitch pipeline (won, lost, in-flight).
- **Helpdesk** — tickets from clients on live brand systems we steward.
- **HR + Expenses** — small team, lots of pitch travel, freelance contractors.
- **Purchase** — freelancers, print shops, photo studios, hosting partners.

## When editing this universe

- Edit the relevant YAML/MD file, not the generated Odoo records — the YAML is source of truth.
- Re-run population to reconcile (idempotent via slugs).
- Keep the cast at ~12. International mix, mostly Dutch founders.
- New customers: should be plausible OR a deliberate Multilul-style absurdity. If neither, propose a story change first.
- Keep the satirical layer subtle. Three or four absurd clients max; the rest plausible.

## Recommended Odoo apps

See [story/odoo-apps.yaml](story/odoo-apps.yaml). Services-led — **no** Manufacturing, Inventory, Quality, Field Service, POS, or eCommerce. Core: Sales + CRM + Project + Timesheets + Subscriptions + Accounting + HR + Purchase. Story-driven additions: Helpdesk (stewardship-client tickets), Expenses, Documents, Sign.

## Image generation

Presets live in [images/flux-presets.yaml](images/flux-presets.yaml).

**Visual direction is deliberately at odds with the brand voice.** The studio's website *copy* is editorial-restrained ("we don't do logos, we do legacies"); the studio's *visuals* are unapologetic late-1980s Dutch advertising-agency pastiche — Jiskefet-Multilul-energy. Mustard yellow, chestnut brown, gold trim, fake-mahogany boardrooms, harsh on-camera flash, oversized plastic eyeglasses, perms, shoulder-padded blazers, beige CRT computers, brown carpet, fluorescent ceiling tubes. VHS-still aesthetic. The tension between the high-minded copy and the loud retro visuals **is the joke** — keep both poles intact.

Generate via `scripts/generate_images.py --universe provisional-bureau …`.
