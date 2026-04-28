#!/usr/bin/env python3
"""Generate product images from a JSON spec, one image per unique slug.

Input JSON schema (list):
    [{"slug": "...", "kind": "<preset>", "subject": "...", "product_ids": [..]}, ...]

Reuses style presets from universes/<u>/images/flux-presets.yaml and the BFL
helpers from scripts/generate_images.py. Outputs images to
universes/<u>/images/generated/<kind>/<slug>.jpg and updates its manifest.
Upload to Odoo is done separately (via MCP update_record) using product_ids.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from generate_images import (  # noqa: E402
    build_prompt,
    download,
    load_manifest,
    load_presets,
    poll,
    resolve_universe,
    save_manifest,
    submit,
)


def main() -> int:
    load_dotenv(ROOT / ".env")
    p = argparse.ArgumentParser()
    p.add_argument("--universe", required=True, help="Universe slug under universes/")
    p.add_argument("--input", required=True, help="Path to JSON job spec")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    api_key = os.environ.get("BFL_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: BFL_API_KEY not set", file=sys.stderr)
        return 2

    universe = resolve_universe(args.universe)
    presets = load_presets(universe.presets_file)
    jobs = json.loads(Path(args.input).read_text())
    manifest = load_manifest(universe.manifest)
    errors = 0
    print(f"Universe: {universe.name} — planned: {len(jobs)} image(s)")

    for j in jobs:
        slug, kind, subject = j["slug"], j["kind"], j["subject"]
        preset = presets["types"][kind]
        prompt = build_prompt(presets, kind, subject)
        out_path = universe.out_dir / kind / f"{slug}.jpg"
        key = f"{kind}/{slug}"

        if args.dry_run:
            print(f"[dry-run] {key}  ({preset['model']} {preset['width']}x{preset['height']})")
            continue

        if out_path.exists() and not args.force:
            print(f"[skip]    {key}")
            continue

        try:
            print(f"[submit]  {key}")
            resp = submit(api_key, preset["model"], prompt, preset["width"], preset["height"])
            polling_url = resp.get("polling_url")
            req_id = resp.get("id")
            if not polling_url:
                raise RuntimeError(f"no polling_url in response: {resp}")
            result = poll(api_key, polling_url)
            download(result["result"]["sample"], out_path)
            print(f"[save]    {key}")
            manifest[key] = {
                "slug": slug,
                "kind": kind,
                "path": str(out_path.relative_to(ROOT)),
                "model": preset["model"],
                "width": preset["width"],
                "height": preset["height"],
                "prompt": prompt,
                "bfl_id": req_id,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            save_manifest(manifest, universe.manifest)
        except Exception as exc:
            errors += 1
            print(f"[error]   {key}: {exc}", file=sys.stderr)

    print(f"\nDone. {len(jobs) - errors}/{len(jobs)} succeeded.")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
