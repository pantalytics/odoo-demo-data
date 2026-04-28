#!/usr/bin/env python3
"""Generate demo imagery for a chosen universe via Black Forest Labs' FLUX API.

Reads style presets from universes/<u>/images/flux-presets.yaml and subject data
from universes/<u>/story/*.yaml, submits one request per item to BFL, polls until
ready, and downloads to universes/<u>/images/generated/<kind>/<slug>.jpg.

Usage:
    python scripts/generate_images.py --universe bean-forge logo
    python scripts/generate_images.py --universe bean-forge headshots [--only teun-boon]
    python scripts/generate_images.py --universe bean-forge products  [--only forge-studio]
    python scripts/generate_images.py --universe bean-forge factory   [--count 3]
    python scripts/generate_images.py --universe bean-forge all
    python scripts/generate_images.py --universe <u> <kind> --dry-run

Env: BFL_API_KEY from .env.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

BFL_BASE = "https://api.bfl.ai/v1"
POLL_INTERVAL_S = 2.0
POLL_TIMEOUT_S = 180.0

# Fallback ISO-3166 alpha-2 → adjective map, used when employees.yaml has
# a two-letter `nationality` code. Universes with non-ISO values (e.g. a
# fantasy universe using "Elven") bypass this via the passthrough rule
# in `nationality_adj()`.
NATIONALITY_ADJ = {
    "NL": "Dutch", "IT": "Italian", "GB": "British", "IN": "Indian",
    "GH": "Ghanaian", "SE": "Swedish", "TR": "Turkish", "PT": "Portuguese",
    "IL": "Israeli", "JP": "Japanese", "MX": "Mexican", "NG": "Nigerian",
    "FR": "French", "CL": "Chilean", "PL": "Polish", "SI": "Slovenian",
    "EG": "Egyptian", "ES": "Spanish", "IE": "Irish", "KR": "Korean",
    "HR": "Croatian", "MA": "Moroccan", "US": "American", "DE": "German",
    "BE": "Belgian", "CN": "Chinese",
}


@dataclass
class Universe:
    name: str
    root: Path
    story: Path
    presets_file: Path
    out_dir: Path
    manifest: Path


def resolve_universe(name: str) -> Universe:
    root = ROOT / "universes" / name
    if not root.is_dir():
        available = sorted(p.name for p in (ROOT / "universes").iterdir() if p.is_dir())
        raise SystemExit(f"Universe {name!r} not found. Available: {', '.join(available) or '(none)'}")
    out_dir = root / "images" / "generated"
    return Universe(
        name=name,
        root=root,
        story=root / "story",
        presets_file=root / "images" / "flux-presets.yaml",
        out_dir=out_dir,
        manifest=out_dir / "manifest.yaml",
    )


def nationality_adj(value: str | None) -> str:
    if not value:
        return "international"
    # Two-letter ISO code → look up, else fall through
    if len(value) == 2 and value.isupper():
        return NATIONALITY_ADJ.get(value, value)
    # Universe provided a literal adjective ("Elven", "Draconic") — use as-is
    return value


@dataclass
class Job:
    slug: str
    kind: str           # preset key (headshot, product_roaster, logo, ...)
    subject: str        # per-item descriptive text (templates.<kind> formatted)


def load_presets(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return yaml.safe_load(f)


def load_yaml(path: Path) -> list[dict[str, Any]]:
    with path.open() as f:
        return yaml.safe_load(f)


def product_category_map(presets: dict) -> dict[str, str]:
    """Read `product_category_presets` from presets file, mapping a story
    product category → preset key. Each universe defines its own categories."""
    mapping = presets.get("product_category_presets")
    if not mapping:
        raise SystemExit(
            "flux-presets.yaml is missing `product_category_presets:` — "
            "each universe must declare how its product categories map to image presets."
        )
    return mapping


def build_prompt(presets: dict, kind: str, subject: str) -> str:
    brand = presets["brand"]
    preset = presets["types"][kind]
    # Per-preset overrides let logos/UI-assets opt out of the photographic brand coda.
    preamble = preset.get("preamble", brand["preamble"]).strip()
    coda = preset.get("coda", brand["coda"]).strip()
    include_brand_meta = preset.get("include_brand_meta", True)
    parts = [
        preamble,
        subject.strip(),
        preset["style"].strip(),
        coda,
    ]
    if include_brand_meta:
        parts += [
            f"Palette: {brand['palette'].strip()}.",
            f"Mood: {brand['mood'].strip()}.",
        ]
    return " ".join(p for p in parts if p)


def render_subject(presets: dict, kind: str, vars: dict[str, Any]) -> str:
    template = presets["templates"][kind].strip()
    safe_vars = {k: ("" if v is None else v) for k, v in vars.items()}
    return template.format(**safe_vars)


def submit(api_key: str, model: str, prompt: str, width: int, height: int) -> dict:
    url = f"{BFL_BASE}/{model}"
    payload = {"prompt": prompt, "width": width, "height": height}
    r = requests.post(
        url,
        headers={"x-key": api_key, "Content-Type": "application/json", "accept": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def poll(api_key: str, polling_url: str) -> dict:
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_S)
        r = requests.get(polling_url, headers={"x-key": api_key, "accept": "application/json"}, timeout=30)
        r.raise_for_status()
        data = r.json()
        status = data.get("status")
        if status == "Ready":
            return data
        if status in {"Error", "Failed", "Content Moderated", "Request Moderated"}:
            raise RuntimeError(f"BFL job failed: {status} — {data}")
        # Pending / Task not found (eventual consistency) → keep polling
    raise TimeoutError(f"BFL job did not become Ready within {POLL_TIMEOUT_S}s")


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 15):
                f.write(chunk)


def load_manifest(manifest_path: Path) -> dict:
    if manifest_path.exists():
        with manifest_path.open() as f:
            return yaml.safe_load(f) or {}
    return {}


def save_manifest(manifest: dict, manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w") as f:
        yaml.safe_dump(manifest, f, sort_keys=True, allow_unicode=True)


def run_job(universe: Universe, presets: dict, job: Job, api_key: str, manifest: dict, dry_run: bool, force: bool) -> None:
    preset = presets["types"][job.kind]
    prompt = build_prompt(presets, job.kind, job.subject)
    out_path = universe.out_dir / job.kind / f"{job.slug}.jpg"
    key = f"{job.kind}/{job.slug}"

    if dry_run:
        print(f"[dry-run] {key}  ({preset['model']} {preset['width']}x{preset['height']})")
        print(f"          {prompt}\n")
        return

    if out_path.exists() and not force:
        print(f"[skip]    {key}  (exists; --force to regenerate)")
        return

    print(f"[submit]  {key}  ({preset['model']} {preset['width']}x{preset['height']})")
    resp = submit(api_key, preset["model"], prompt, preset["width"], preset["height"])
    req_id = resp.get("id")
    polling_url = resp.get("polling_url")
    if not polling_url:
        raise RuntimeError(f"No polling_url in response: {resp}")

    print(f"[poll]    {key}  id={req_id}")
    result = poll(api_key, polling_url)
    sample_url = result["result"]["sample"]

    print(f"[save]    {key}  -> {out_path.relative_to(ROOT)}")
    download(sample_url, out_path)

    manifest[key] = {
        "slug": job.slug,
        "kind": job.kind,
        "path": str(out_path.relative_to(ROOT)),
        "model": preset["model"],
        "width": preset["width"],
        "height": preset["height"],
        "prompt": prompt,
        "bfl_id": req_id,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    save_manifest(manifest, universe.manifest)


# ────────────────────────────────────────────────────────────────
# Job builders
# ────────────────────────────────────────────────────────────────

def jobs_logo(universe: Universe, presets: dict) -> list[Job]:
    out = []
    for kind in ("logo", "logo_alt_horizontal"):
        if kind not in presets.get("types", {}):
            continue
        subject = render_subject(presets, kind, {})
        out.append(Job(slug=universe.name, kind=kind, subject=subject))
    return out


def jobs_headshots(universe: Universe, presets: dict, only: set[str] | None) -> list[Job]:
    path = universe.story / "employees.yaml"
    if not path.exists():
        print(f"[skip]    headshots — no {path.relative_to(ROOT)} yet")
        return []
    employees = load_yaml(path)
    out = []
    for e in employees:
        if only and e["id"] not in only:
            continue
        vars = {
            "name": e["name"],
            "role": e["role"],
            "nationality_adj": nationality_adj(e.get("nationality", "")),
            "bio_hint": e.get("bio", ""),
            "age_hint": "",
            "gender_hint": "",
        }
        out.append(Job(slug=e["id"], kind="headshot", subject=render_subject(presets, "headshot", vars)))
    return out


def jobs_products(universe: Universe, presets: dict, only: set[str] | None) -> list[Job]:
    path = universe.story / "products.yaml"
    if not path.exists():
        print(f"[skip]    products — no {path.relative_to(ROOT)} yet")
        return []
    products = load_yaml(path)
    category_map = product_category_map(presets)
    out = []
    for p in products:
        if only and p["id"] not in only:
            continue
        kind = category_map.get(p["category"])
        if not kind:
            continue  # categories with no preset (e.g. services) are skipped
        capacity_kg = ""
        # Rough extraction of capacity from name ("15kg", "60kg", "1kg")
        for token in p["name"].replace("kg", " kg").split():
            if token.isdigit():
                capacity_kg = token
                break
        vars = {
            "name": p["name"],
            "description": (p.get("description") or "").strip().replace("\n", " "),
            "capacity_kg": capacity_kg,
        }
        out.append(Job(slug=p["id"], kind=kind, subject=render_subject(presets, kind, vars)))
    return out


def jobs_factory(universe: Universe, presets: dict, count: int) -> list[Job]:
    out = []
    for i in range(1, count + 1):
        subject = render_subject(presets, "factory_scene", {})
        out.append(Job(slug=f"workshop-{i:02d}", kind="factory_scene", subject=subject))
    return out


def jobs_customers(universe: Universe, presets: dict, only: set[str] | None) -> list[Job]:
    path = universe.story / "customers.yaml"
    if not path.exists():
        print(f"[skip]    customers — no {path.relative_to(ROOT)} yet")
        return []
    customers = load_yaml(path)
    out = []
    for c in customers:
        if only and c["id"] not in only:
            continue
        vars = {"name": c["name"], "city": c.get("city", ""), "country": c.get("country", "")}
        out.append(Job(slug=c["id"], kind="customer_placeholder", subject=render_subject(presets, "customer_placeholder", vars)))
    return out


# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────

def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Generate demo imagery for a universe via FLUX")
    parser.add_argument("--universe", required=True, help="Universe slug under universes/")
    parser.add_argument("kind", choices=["logo", "headshots", "products", "factory", "customers", "all"])
    parser.add_argument("--only", help="Comma-separated slugs to include (skip the rest)")
    parser.add_argument("--count", type=int, default=3, help="For 'factory' only: how many scenes")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts, don't call API")
    parser.add_argument("--force", action="store_true", help="Regenerate even if output exists")
    args = parser.parse_args()

    api_key = os.environ.get("BFL_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: BFL_API_KEY not set (check .env)", file=sys.stderr)
        return 2

    universe = resolve_universe(args.universe)
    presets = load_presets(universe.presets_file)
    only = set(args.only.split(",")) if args.only else None

    jobs: list[Job] = []
    if args.kind in ("logo", "all"):
        jobs += jobs_logo(universe, presets)
    if args.kind in ("headshots", "all"):
        jobs += jobs_headshots(universe, presets, only)
    if args.kind in ("products", "all"):
        jobs += jobs_products(universe, presets, only)
    if args.kind == "factory":
        jobs += jobs_factory(universe, presets, args.count)
    if args.kind == "customers":
        jobs += jobs_customers(universe, presets, only)

    if not jobs:
        print("No jobs matched your selection.")
        return 1

    print(f"Universe: {universe.name} — planned: {len(jobs)} image(s)")
    manifest = load_manifest(universe.manifest)
    errors = 0
    for job in jobs:
        try:
            run_job(universe, presets, job, api_key, manifest, dry_run=args.dry_run, force=args.force)
        except Exception as exc:
            errors += 1
            print(f"[error]   {job.kind}/{job.slug}: {exc}", file=sys.stderr)

    print(f"\nDone. {len(jobs) - errors}/{len(jobs)} succeeded.")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
