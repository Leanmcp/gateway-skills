# Signing & TestFlight

## Account facts (fill in your own)

> **Update this file if any of these change** — a revoked API key, a new Mac, or
> a switch from Individual to Organization enrollment all land here. Everything
> below is reused verbatim on every new project; nothing needs re-deriving.

| | |
|---|---|
| Team ID | `<TEAM_ID>` |
| Enrolled as | Individual |
| Apple ID | <APPLE_ID_EMAIL> |
| API Key ID | `<KEY_ID>` |
| API Issuer ID | `<ISSUER_ID>` |
| Key file | `~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8` |

Already exported in `~/.zshrc`, which `upload_testflight.sh` reads:

```bash
export ASC_KEY_ID=<KEY_ID>
export ASC_ISSUER_ID=<ISSUER_ID>
export ASC_KEY_PATH=~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8
```

Set `DEVELOPMENT_TEAM = <TEAM_ID>` in the project's build settings and signing
is done — no Xcode UI needed.

### If the key ever needs replacing

https://appstoreconnect.apple.com/access/integrations/api → Team Keys → **+**,
role **App Manager**. **The .p8 downloads exactly once.** Then:

```bash
mkdir -p ~/.appstoreconnect/private_keys
mv ~/Downloads/AuthKey_*.p8 ~/.appstoreconnect/private_keys/
chmod 600 ~/.appstoreconnect/private_keys/AuthKey_*.p8
```

Update the three exports in `~/.zshrc` and the table above. Never commit a
`.p8` — it can upload builds to the account.

## Per-project, one time

1. Set `DEVELOPMENT_TEAM` and a unique `PRODUCT_BUNDLE_IDENTIFIER`.
2. Create the app record: https://appstoreconnect.apple.com/apps → **+** →
   **New App**. Bundle ID must match; **the App Store Name must be globally
   unique across the entire store** and is a separate namespace from the bundle
   ID. If the bundle ID isn't in the dropdown, open the project in Xcode and
   pick the Team once — that registers the App ID.
3. TestFlight → **Internal Testing** → create a group → add the Apple ID → turn
   on **Automatically distribute builds** so future uploads need no clicks.
   Internal testers skip Apple review entirely.

## Every upload after that

```bash
time ./workspace/upload_testflight.sh
```

Then `git add -A && git commit` — the script edits `CURRENT_PROJECT_VERSION` in
`project.pbxproj` in place.

## Failure modes

| Symptom | Cause |
|---|---|
| `Redundant Binary Upload` | Build number already used. The *previous* upload succeeded — check App Store Connect before re-archiving. |
| `App Name already being used` | App Store name is taken. Xcode tried to auto-create the record; create it manually with a unique name instead. |
| Team shows `(Personal Team)` | Free tier, cannot upload. Individual enrollment means the paid team has the **identical display name** minus the suffix — easy to miss. Setting `DEVELOPMENT_TEAM` bypasses the dropdown. |
| Paid team missing from dropdown | Stale cache. Xcode → Settings → Apple Accounts → Download Manual Profiles, then ⌘Q and reopen. |
| `Product → Archive` greyed out | Destination is a simulator. Needs **Any iOS Device (arm64)** — it's the toolbar pill next to the ▶︎ button, not a menu. |
| `Missing app icon` at upload | Archiving from Xcode does **not** run the icon script. Icons are gitignored, so fresh clones have none. |
| `no suitable application record` | Bundle ID ≠ the App Store Connect record. |

## Manual Xcode path

Only needed when the CLI fails and the cause is unclear.

Destination → **Any iOS Device (arm64)** → **Product → Archive** → Organizer →
**Validate App** (catches problems without uploading) → **Distribute App** →
**App Store Connect** → **Upload**.

Prefer **App Store Connect** over **TestFlight Internal Only**: the latter is
irreversible for that build and can never be promoted to external testers or the
store.
