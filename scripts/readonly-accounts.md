# Read-only accounts for a demo universe

Every demo universe (bean-forge, unicorn-inc, ...) benefits from a **read-only
account**: a login (and API key) that can read all the business data but change
nothing. It is what we point the hosted MCP demo connection at, and it is a
handy safety net for any "let a prospect poke around" session.

This is universe-agnostic Odoo access-rights work, not story data, so it lives
in `scripts/`, not under a universe folder. One script sets it up on any target
Odoo; one manual step (minting the key) finishes it.

## The idea (how Odoo read-only actually works)

Odoo checks four layers per action: groups -> access rights (`ir.model.access`)
-> record rules (`ir.rule`) -> field access. Permissions **only add up** - you
cannot subtract a right by adding a group. So "read-only" means: put the user in
groups that grant only read, and in **no** group that grants write.

We build that as a first-class, per-app tier:

1. For each business app (Sales, Purchase, Inventory, Manufacturing, Project,
   Timesheets, Employees, Accounting) we add a **"Read Only" option to that app's
   privilege dropdown** - a group whose ACLs are the app's full *User* tier
   mirrored to read-only, linked into the same record rules so it sees the same
   rows. In Settings > Users the app dropdown then reads: No / **Read Only** /
   User / Administrator.
2. All those read-only groups are bundled into one OCA base_user_role role,
   **"Read Only (all apps)"**, so a whole read-only profile is one pick.

Full background: the vault note *"The definitive guide to access rights in
Odoo"*.

## Setup (reproducible)

```bash
# from the repo root, against the universe's Odoo (admin creds)
export ODOO_URL=https://bean-forge.cloudpepper.site
export ODOO_DB=bean-forge
export ODOO_LOGIN=admin              # or any Administrator user
export ODOO_API_KEY=sk_...           # that user's API key (admin)

python scripts/setup_readonly.py --dry-run   # preview, writes nothing
python scripts/setup_readonly.py             # create groups + role
python scripts/setup_readonly.py --demo-user # also create the demo user
```

The script is **idempotent** - safe to re-run; it updates in place and never
duplicates. It discovers the DB's privileges and groups at runtime, so the same
command works on every universe (an app the universe hasn't installed is
skipped with a note).

## Minting the key (the one manual step)

An Odoo API key is created behind an identity check that cannot be scripted, and
its secret is shown only once. So:

1. Log in as the demo user (`demo-readonly`, give it a password first as admin),
   or as any admin.
2. Preferences > **Account Security** > **New API Key**.
3. Pick **Role = "Read Only (all apps)"**, then a duration.
   - A key's max validity is the **highest** `api_key_duration` among its
     owner's groups (0 means 1 day). The setup script sets the read-only groups
     to a ~100-year cap, so pick **Duration = "Custom Date"** and a far-future
     date (e.g. 2050) - effectively permanent, **no admin rights needed**.
   - The literal **"Persistent Key"** (never-expires) option is view-gated to
     Administrators (group_system) and is not shown to a plain user; the far
     Custom Date is the non-admin equivalent.
4. Copy the key. That is your `DEMO_ODOO_API_KEY`.

Verify it end to end:

```bash
python - <<'PY'
import xmlrpc.client, ssl
URL, DB, LOGIN, KEY = "https://bean-forge.cloudpepper.site", "bean-forge", "<owner-login>", "<new-key>"
c = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", context=ssl.create_default_context())
uid = c.authenticate(DB, LOGIN, KEY, {})
m = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", context=ssl.create_default_context())
print("read leads:", m.execute_kw(DB, uid, KEY, "crm.lead", "search_count", [[]]))      # should work
try:
    m.execute_kw(DB, uid, KEY, "res.partner", "create", [{"name": "x"}]); print("WRITE SUCCEEDED - not read-only!")
except Exception: print("write blocked - read-only OK")
PY
```

## Wiring the hosted demo connection (admin SaaS)

Once you have a permanent, read-only key, set these on the admin server and
deploy; the demo escape-hatch button then appears on `/admin/setup`:

```
DEMO_ODOO_URL=https://bean-forge.cloudpepper.site
DEMO_ODOO_API_KEY=<the read-only key>
DEMO_ODOO_DB=bean-forge        # required: bean-forge has list_db=False
DEMO_ODOO_LOGIN=<owner-login>
```

## Notes / gotchas

- **base.group_user still writes a little.** A demo user that is a normal
  internal user also carries Role/User, which can write a few self/framework
  models (own preferences, discuss). To lock an API key strictly to the
  read-only groups only, scope the key to the role via
  odoo-mcp-pro-governance (`x_role_id`) - the module narrows the key's effective
  groups to the role, dropping group_user.
- **Assigning the role to the *user* (not the key)** makes base_user_role reset
  that user's groups to only the role's groups, which strips group_user and
  turns the user "external" (portal). Fine for an API-only demo connection, but
  an external user can't open the backend to mint a key - so mint the key first,
  or mint it as admin and rely on the role for read-only.
- **Long-lived keys without admin.** The literal "Persistent Key" option needs
  group_system, but the read-only groups carry a ~100-year `api_key_duration`
  cap (set by the script), so a plain read-only user can mint an
  effectively-permanent key via **Custom Date**. You cannot edit a key's expiry
  after creation (API keys are immutable) - re-mint if you need to change it.
