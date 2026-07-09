#!/usr/bin/env python3
"""Create read-only access tiers + a demo read-only user on a demo Odoo.

Universe-agnostic and idempotent. Safe to re-run against any demo universe's
Odoo (bean-forge, unicorn-inc, provisional-bureau, ...); it discovers that DB's
privileges and groups at runtime, so it carries no hard-coded ids.

What it does (see scripts/readonly-accounts.md for the why):

1. For each business app it adds a **"Read Only" option to that app's privilege
   dropdown** - a `res.groups` in the same privilege whose `ir.model.access`
   rows are the app's full User tier mirrored to read-only (perm_read only). The
   read-only group is also linked into the User tier's record rules so it sees
   the same rows.
2. Bundles every read-only group into one OCA base_user_role role
   **"Read Only (all apps)"** (`res.users.role`), so a whole read-only profile
   is one pick.
3. Optionally creates a plain internal **demo user** (`--demo-user`). Its API key
   is minted by hand in the Odoo wizard (behind an identity check we cannot
   script) and bound to the role there - see the runbook.

Read-only is plain Odoo: a group with only read ACLs and no write ACLs cannot
write, and permissions only ever add up, so a user in only read-only groups is
read-only. To lock an AI/API key tighter than its owning user, scope the key to
the role via odoo-mcp-pro-governance (`res.users.apikeys.x_role_id`).

Config (env or a local .env): ODOO_URL, ODOO_DB, ODOO_LOGIN, ODOO_API_KEY.

    python scripts/setup_readonly.py --dry-run     # show the plan, touch nothing
    python scripts/setup_readonly.py               # apply
    python scripts/setup_readonly.py --demo-user   # apply + create the demo user
"""

import argparse
import os
import ssl
import sys
import xmlrpc.client
from pathlib import Path

# Business privileges to give a read-only tier, mapped to the User group whose
# read access we mirror. Matched by NAME at runtime (ids differ per DB). The
# read source is the widest *User* tier (sees all records), never Administrator
# (which also carries config-model write ACLs we do not want to mirror).
APP_READ_SOURCES = {
    "Sales": "User: All Documents",
    "Purchase": "User",
    "Inventory": "User",
    "Manufacturing": "User",
    "Project": "User",
    "Timesheets": "User: all timesheets",
    "Employees": "Officer: Manage all employees",
    "Accounting": "Invoicing",
}

RO_GROUP_SUFFIX = "Read Only"
BASE_RO_GROUP = "Base / Read Only"
ROLE_NAME = "Read Only (all apps)"

# A key's max validity is the HIGHEST api_key_duration among its owner's groups
# (0 = 1 day). Give the read-only groups a long cap so a demo read-only key can
# be minted effectively-permanent (~100 years) without granting group_system.
KEY_DURATION_DAYS = 36500
DEMO_USER_LOGIN = "demo-readonly"
DEMO_USER_NAME = "Demo (read-only)"

# Never mirror read on these: credentials, tokens, session/2FA, key hashes.
# A demo read-only account must not be able to read them.
SECRET_MODELS = [
    "res.users.apikeys", "res.users.apikeys.description", "res.users.apikeys.show",
    "res.users.identitycheck", "change.password.own", "change.password.wizard",
    "auth_totp.device", "auth_totp.wizard", "auth.passkey.key", "auth.passkey.key.create",
    "res.device", "res.device.log", "iap.account", "iap.service",
    "payment.token", "payment.transaction", "payment.method",
    "account.payment.method", "account.payment.method.line",
    "account_edi_proxy_client.user", "ir.config_parameter",
]


def load_dotenv(path=".env"):
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


class Odoo:
    def __init__(self, url, db, login, key, dry_run=False):
        self.db, self.login, self.key, self.dry = db, login, key, dry_run
        ctx = ssl.create_default_context()
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", context=ctx)
        self.uid = common.authenticate(db, login, key, {})
        if not self.uid:
            sys.exit(f"Authentication failed for {login} on {url}/{db}")
        self.models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", context=ctx)

    def call(self, model, method, args=None, kw=None):
        return self.models.execute_kw(
            self.db, self.uid, self.key, model, method, args or [], kw or {}
        )

    def search_read(self, model, domain, fields, **kw):
        return self.call(model, "search_read", [domain], {"fields": fields, **kw})

    def find_id(self, model, domain):
        r = self.call(model, "search", [domain], {"limit": 1})
        return r[0] if r else None

    def ensure(self, model, match_domain, values, label):
        """Idempotent upsert: update the record matching `match_domain`, else create."""
        rid = self.find_id(model, match_domain)
        if rid:
            if self.dry:
                print(f"    = {label}: exists (id {rid}), would update")
            else:
                self.call(model, "write", [[rid], values])
                print(f"    = {label}: updated (id {rid})")
            return rid
        if self.dry:
            print(f"    + {label}: would create")
            return None
        rid = self.call(model, "create", [values])
        print(f"    + {label}: created (id {rid})")
        return rid


def group_closure(odoo, gid):
    """The group plus every group it implies, transitively (its full ACL reach)."""
    g = odoo.call("res.groups", "read", [[gid]], {"fields": ["all_implied_ids"]})[0]
    return set(g["all_implied_ids"]) | {gid}


def read_model_ids(odoo, group_ids, exclude):
    """Model ids that `group_ids` can read, minus the excluded (secret) ones."""
    if not group_ids:
        return []
    acls = odoo.search_read(
        "ir.model.access",
        [["group_id", "in", list(group_ids)], ["perm_read", "=", True], ["active", "=", True]],
        ["model_id"],
    )
    return sorted({a["model_id"][0] for a in acls} - exclude)


def mirror_read_acls(odoo, ro_gid, model_ids, label):
    """Create a read-only ir.model.access on `ro_gid` for each model (idempotent,
    batched into one create call)."""
    existing = {
        a["model_id"][0]
        for a in odoo.search_read("ir.model.access", [["group_id", "=", ro_gid]], ["model_id"])
    }
    vals = [{
        "name": f"RO {label}: {mid}", "model_id": mid, "group_id": ro_gid,
        "perm_read": True, "perm_write": False, "perm_create": False, "perm_unlink": False,
    } for mid in model_ids if mid not in existing]
    if vals:
        odoo.call("ir.model.access", "create", [vals])
    print(f"      {len(model_ids)} read ACLs ({len(vals)} new)")


def link_record_rules(odoo, src_gid, ro_gid):
    """Add the read-only group to the source group's record rules (never removes),
    so the read-only group sees the same rows."""
    rules = odoo.search_read("ir.rule", [["groups", "in", [src_gid]]], ["id", "groups"])
    linked = 0
    for r in rules:
        if ro_gid not in r["groups"]:
            odoo.call("ir.rule", "write", [[r["id"]], {"groups": [[4, ro_gid]]}])
            linked += 1
    if rules:
        print(f"      {len(rules)} record rules ({linked} newly linked)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="show the plan, write nothing")
    ap.add_argument("--demo-user", action="store_true", help="also create the demo read-only user")
    args = ap.parse_args()

    load_dotenv()
    url = os.environ.get("ODOO_URL")
    db = os.environ.get("ODOO_DB")
    login = os.environ.get("ODOO_LOGIN")
    key = os.environ.get("ODOO_API_KEY")
    if not all([url, db, login, key]):
        sys.exit("Set ODOO_URL, ODOO_DB, ODOO_LOGIN, ODOO_API_KEY (env or .env).")

    odoo = Odoo(url, db, login, key, dry_run=args.dry_run)
    print(f"Connected to {url} / {db} as uid {odoo.uid}{'  [DRY RUN]' if args.dry_run else ''}\n")

    # Resolve the secret denylist to model ids once.
    secret_ids = {
        m["id"] for m in odoo.search_read("ir.model", [["model", "in", SECRET_MODELS]], ["id"])
    }

    # Base read-only group: everything an Internal User (base.group_user) can
    # read - the reference + framework models every app leans on - minus
    # secrets. Standalone (no privilege); it exists to complete the role so a
    # key scoped strictly to the role can still resolve related fields.
    base_uid = odoo.call("ir.model.data", "check_object_reference", ["base", "group_user"])[1]
    base_closure = group_closure(odoo, base_uid)
    print("  Base (Internal User read surface):")
    base_ro = odoo.ensure(
        "res.groups", [["name", "=", RO_GROUP_SUFFIX], ["privilege_id", "=", False], ["comment", "like", "base-ro"]],
        {"name": RO_GROUP_SUFFIX, "comment": "base-ro (demo read-only, all Internal-User reads)",
         "api_key_duration": KEY_DURATION_DAYS},
        f"group '{BASE_RO_GROUP}'",
    )
    ro_group_ids = []
    if base_ro:
        mirror_read_acls(odoo, base_ro, read_model_ids(odoo, base_closure, secret_ids), "Base")
        ro_group_ids.append(base_ro)

    # Per-app read-only groups: the app's User tier read surface MINUS the base
    # surface (the app-specific delta), attached to that app's privilege so
    # "Read Only" shows up as an option in the app dropdown.
    for priv_name, read_src in APP_READ_SOURCES.items():
        pid = odoo.find_id("res.groups.privilege", [["name", "=", priv_name]])
        if not pid:
            print(f"  ! privilege '{priv_name}' not installed, skipping")
            continue
        priv = odoo.search_read(
            "res.groups.privilege", [["id", "=", pid]], ["id", "name", "group_ids"]
        )[0]
        src = next(
            (g for g in odoo.call("res.groups", "read", [priv["group_ids"]], {"fields": ["id", "name"]})
             if g["name"] == read_src), None,
        )
        print(f"  {priv_name}:")
        if not src:
            print(f"    ! read-source group '{read_src}' not found, skipping")
            continue
        ro = odoo.ensure(
            "res.groups", [["name", "=", RO_GROUP_SUFFIX], ["privilege_id", "=", priv["id"]]],
            {"name": RO_GROUP_SUFFIX, "privilege_id": priv["id"], "api_key_duration": KEY_DURATION_DAYS},
            f"group '{priv_name} / {RO_GROUP_SUFFIX}'",
        )
        if odoo.dry or not ro:
            continue
        app_ids = group_closure(odoo, src["id"]) - base_closure
        mirror_read_acls(odoo, ro, read_model_ids(odoo, app_ids, secret_ids), priv_name)
        link_record_rules(odoo, src["id"], ro)
        ro_group_ids.append(ro)

    # Bundle every read-only group into one OCA base_user_role role.
    print(f"\n  Role '{ROLE_NAME}':")
    role_id = odoo.ensure(
        "res.users.role",
        [["name", "=", ROLE_NAME]],
        {"name": ROLE_NAME, "implied_ids": [[6, 0, ro_group_ids]]} if ro_group_ids else {"name": ROLE_NAME},
        f"role '{ROLE_NAME}'",
    )

    if args.demo_user:
        print(f"\n  Demo user '{DEMO_USER_LOGIN}':")
        # Plain internal user (keeps backend access so its API key can be minted
        # in the wizard). Bind the role to the KEY there, not to the user.
        odoo.ensure(
            "res.users",
            [["login", "=", DEMO_USER_LOGIN]],
            {"name": DEMO_USER_NAME, "login": DEMO_USER_LOGIN},
            f"user '{DEMO_USER_LOGIN}'",
        )

    print("\nDone." + ("" if not args.dry_run else "  (dry run - nothing written)"))
    print("Next: mint the key in Odoo (Preferences > New API Key > Role "
          f"'{ROLE_NAME}'); it can't be scripted (identity check). See "
          "scripts/readonly-accounts.md.")


if __name__ == "__main__":
    main()
