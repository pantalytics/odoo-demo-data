# Unicorn Inc. — universe context

> **Status: skeleton.** Identity is sketched; cast, products, customers and imagery still to be written.

## The company in one line

**Unicorn Inc.** — a cheerful cooperative of fabelwezens trading in embodied superpowers and mythic materials: pegasus wings, bottled dragon fire, mammoth fur, phoenix feathers, kraken ink, basilisk-glance mirrors. The realm's go-to supplier when you need a *real* superpower, not a knock-off.

## Tone & story rules

- **Vrolijk, optimistic, kid-in-a-candy-store.** Bright, sun-on-rainbow energy. The opposite of Bean Forge's documentary-grey workshop.
- **Take it completely seriously.** Treat dragon-fire logistics, pegasus-wing fitting, mammoth-fur QC like a real industrial supply chain. The contrast between the absurd subject and the rigorous handling is the joke.
- **Cast = fabelwezens only — broadly defined.** Mix two flavors:
  1. **Classical fantasy creatures.** Unicorns, dragons, pegasi, phoenixes, mermaids, kitsune, fauns, gryphons, kelpies, sylphs, naiads, satyrs, dryads, djinn, centaurs, golems, brownies.
  2. **Fluffy mascot-style fabelwezens.** Magical reimaginings of real-world fluffy animals — Cloud Panda, Star Bear, Sprite Bunny, Twinkle Hedgehog, Rainbow Sloth, Sparkle Squirrel, Rosy Capybara, Honey Owlet, Glimmer Otter, etc. These are NOT just animals — they're fantasy beings with magical traits (cloud-fluff, galaxy-pelt, prism-quills) and full sentient personalities, on equal footing with the classical creatures.
  Mix mythologies and traditions — no single one dominates. No single species more than ~2 employees in the 25-person cast.
- **Plausible fantasy economics.** Every product has a real supply problem: pegasus wings need fitting, dragon fire is regulated, mammoth fur is seasonal, phoenix feathers self-immolate if mishandled. Lean into that for CRM-pipeline drama.
- **Currency: Sparkle (★).** Whole numbers in YAML, no symbol.
- **No real IP.** Invent names. No My Little Pony, no Pokémon, no Harry Potter, no Disney.

## Universe-specific schema notes

- `employees.yaml → nationality:` is a free-form **species adjective** like `Unicorn`, `Dragonkin`, `Pegasi`, `Kitsune` — not an ISO-3166 code. The image generator passes it through to the headshot prompt as-is.
- `products.yaml → category:` uses fantasy categories (e.g. `wings`, `firearm`, `fur`, `feather`, `ink`, `mirror`); map them to image presets in [images/flux-presets.yaml](images/flux-presets.yaml) under `product_category_presets:`.
- Dates are normal ISO dates. Population still shifts them for "recent" effect.

## Narrative canon

Full narrative will live in [story/company.md](story/company.md) (currently a stub). Once the identity is settled, fill in the usual YAMLs: `employees.yaml`, `products.yaml`, `customers.yaml`, `suppliers.yaml`, `boms.yaml`, `crm-pipeline.yaml`, `projects.yaml` — same schemas as Bean Forge.

## Recommended Odoo apps

See [story/odoo-apps.yaml](story/odoo-apps.yaml). Core flow: Sales + CRM + Purchase + Inventory + Manufacturing + Accounting + HR. Story-driven additions: Quality (regulated fire, fragile feathers), Field Service (wing-fitting, mirror-installation), Project + Timesheets (seasonal harvests), Maintenance (mirrors, ink presses).

## Image generation

Presets live in [images/flux-presets.yaml](images/flux-presets.yaml). Brand palette draft: rainbow prism, gold leaf, sky-blue, blossom-pink, sunlit cloud-white. Style: bright painterly storybook, joyful, glowing — not anime, not glossy CGI. Generate via `scripts/generate_images.py --universe unicorn-inc …`.
