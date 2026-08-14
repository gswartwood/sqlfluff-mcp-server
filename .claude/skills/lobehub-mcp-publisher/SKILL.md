---
name: lobehub-mcp-publisher
description: Publish and manage MCP plugin (MCP server) listings on the LobeHub Marketplace using the lhm CLI (@lobehub/market-cli). Covers logging in via browser OIDC, connecting GitHub for ownership verification, publishing a new listing from your GitHub repository, claiming an existing plugin, authoring the lhm.plugin.json manifest, updating versions, and verifying the listing. Use when a user wants to publish, update, release, claim, unpublish, or delete an MCP plugin or MCP server on lobehub.com or market.lobehub.com.
---

<!-- verified-against: @lobehub/market-cli@next; last-synced: 2026-08-05 -->

# Publish MCP Plugins to LobeHub Market

Publish, version, and manage MCP plugin listings on the LobeHub Marketplace via the `lhm` CLI.

- **Marketplace**: [lobehub.com/mcp](https://lobehub.com/mcp)
- **CLI package**: `@lobehub/market-cli` (npm, requires Node.js >= 22)

> **Important:** Always use the CLI commands below. Do NOT make raw HTTP/API requests — authentication uses OIDC PKCE with automatic token refresh, which the CLI handles for you.

## Skill Files

| File                           | URL                                                                |
| ------------------------------ | ------------------------------------------------------------------ |
| **SKILL.md** (this file)       | `https://market.lobehub.com/s/publish-mcp`                         |
| **references/manifest.md**     | `https://market.lobehub.com/s/publish-mcp/references/manifest`     |
| **references/lhm-commands.md** | `https://market.lobehub.com/s/publish-mcp/references/lhm-commands` |

Fetching the first URL returns this file with all references appended — one request gets everything.

**Install locally** with the CLI (`--agent` targets a specific agent: `claude-code`, `open-claw`, `codex`, `cursor`):

```bash
npx -y @lobehub/market-cli skills install lobehub-mcp-publisher --agent claude-code
```

Or with curl. The path below is the project-local Claude Code directory, matching the CLI's `--agent claude-code` target — swap in `./.agents/skills` (Codex), `./.cursor/skills` (Cursor), or `~/.claude/skills` for a user-global install:

```bash
SKILL_DIR=./.claude/skills/lobehub-mcp-publisher # project-local, same as the CLI default
mkdir -p "$SKILL_DIR/references"
curl -s https://market.lobehub.com/s/publish-mcp > "$SKILL_DIR/SKILL.md"
curl -s https://market.lobehub.com/s/publish-mcp/references/manifest > "$SKILL_DIR/references/manifest.md"
curl -s https://market.lobehub.com/s/publish-mcp/references/lhm-commands > "$SKILL_DIR/references/lhm-commands.md"
```

**Or just read them from the URLs above!**

## Critical Rules

1. **Use `lhm plugin publish <repo-url> [--dir ...]` for a new listing and `lhm plugin update [--dir ...]` for an existing listing.** Both commands require the same local `lhm.plugin.json`, including the owner-declared `identifier`, `name`, and `version`. Publish creates the listing immediately, returns its identifier/version, and starts asynchronous repository enrichment. You must own the repo or have push access. If not, **stop** and use the **Submit MCP** button at [lobehub.com/mcp](https://lobehub.com/mcp).
2. **Two commands require a human with a browser**: `lhm login` and `lhm github connect`. Never try to automate or bypass them — see [Interactive Steps](#interactive-steps-human-in-the-loop) below.
3. **Never read, print, or copy the credential files** in `~/.lobehub-market/`. They contain access and refresh tokens. Use `lhm auth status --output json` to inspect auth state instead.
4. **M2M credentials cannot publish.** `lhm register` and the `MARKET_CLIENT_ID` / `MARKET_CLIENT_SECRET` environment variables are an agent-identity channel for search, ratings, and comments (they are what the read-only `lhm mcp ...` commands authenticate with) — they have no publish permission. There is no token-only, non-interactive publish path; do not look for one.
5. Run commands as `npx -y @lobehub/market-cli ...`. `lhm` below is shorthand for the same binary (available after `npm install -g @lobehub/market-cli`).

## Prerequisites

- Node.js >= 22
- A LobeHub account (sign up at [market.lobehub.com](https://market.lobehub.com))
- A GitHub account that owns the plugin's source repository or has push access to it

## Workflow Overview

```bash
# 0. Probe current state (safe, read-only)
npx -y @lobehub/market-cli auth status --output json
npx -y @lobehub/market-cli github status

# 1. Log in (browser, human required) — skip if user.status is "authenticated" or "token expired"
npx -y @lobehub/market-cli login

# 2. Connect GitHub (browser, human required) — skip if already connected
npx -y @lobehub/market-cli github connect

# 3. Check ownership — is the plugin in your list?
npx -y @lobehub/market-cli plugin list --output json
#    Listed in the marketplace but not in your list? Claim it:
npx -y @lobehub/market-cli plugin claim joshuayoes-ios-simulator-mcp
# 4. Generate lhm.plugin.json from a running MCP server, then review/edit the owner declaration
#    For a stdio server (the command runs with --dir as its working directory):
npx -y @lobehub/market-cli plugin init --stdio "node dist/index.js" --dir /home/user/projects/my-mcp
#    Or for a running Streamable HTTP server:
npx -y @lobehub/market-cli plugin init --url https://example.com/mcp --dir /home/user/projects/my-mcp
#    (same "version" = update that version in place; new "version" = new release)
#    Not in the marketplace? Publish its owner declaration, then enrich from the repo:
npx -y @lobehub/market-cli plugin publish https://github.com/joshuayoes/ios-simulator-mcp --dir /home/user/projects/my-mcp

# 5. Update the existing listing (always pass --dir as an absolute path)
npx -y @lobehub/market-cli plugin update --dir /home/user/projects/my-mcp

# 6. Verify
npx -y @lobehub/market-cli plugin list --output json
#    Optional public check — `mcp ...` commands need the M2M identity from `lhm register` (Critical Rule 4)
npx -y @lobehub/market-cli mcp view joshuayoes-ios-simulator-mcp --output json
```

Notes on step 0: on a machine with no credentials at all, `auth status` exits with code 1 and prints `No credentials found...` — treat that as "not logged in", not as a failure. A `user.status` of `"token expired"` is usually fine: every command refreshes the token automatically; only re-login when a command actually fails with `Session expired`.

## Interactive Steps (Human-in-the-Loop)

`lhm login` and `lhm github connect` open a browser and block until the flow completes (login waits up to 5 minutes for the OAuth callback; github connect polls for up to 5 minutes).

Protocol for agents:

1. Probe first (`auth status --output json`, `github status`) — skip the interactive step entirely if already authenticated/connected.
2. Run the command in the foreground and immediately relay the fallback URL it prints (`If your browser does not open, visit: ...`) to the user, asking them to complete the authorization in their browser.
3. Wait for the command to exit, then confirm with the matching status command.
4. On timeout or failure, explain and ask the user before re-running. Do not retry in a loop — each retry opens another browser window.
5. Both commands are idempotent — re-running them after success is safe.

**Headless / SSH sessions:** `lhm login` listens for the OAuth callback on `localhost:51234`–`51243` _of the machine running the CLI_. If the user's browser is on a different machine, the callback cannot reach the CLI — forward a port first (`ssh -L 51234:localhost:51234 <host>`) or run `lhm login` on the user's local machine instead.

## The Manifest — lhm.plugin.json

Both `lhm plugin publish` and `lhm plugin update` read `lhm.plugin.json` from the target directory. Minimal example:

Use `lhm plugin init --stdio "<command>" [--dir ...]` or `lhm plugin init --url <endpoint> [--dir ...]` to generate a draft. It initializes the MCP server and captures server metadata plus `tools/list`, `resources/list`, `resources/templates/list`, and `prompts/list`; package.json and the GitHub remote supply fallback project metadata. The command never contacts the marketplace or invokes the repository crawler. It refuses to replace an existing manifest unless `--force` is supplied. Always review the generated file: once saved and sent by `publish` / `update`, it is the owner's declaration and source of truth.

```json
{
  "description": "Control the iOS Simulator from MCP",
  "identifier": "joshuayoes-ios-simulator-mcp",
  "name": "iOS Simulator MCP",
  "version": "1.4.0"
}
```

- `identifier`, `name`, and `version` are required. For first publication, choose and declare the stable marketplace identifier before running publish. The response confirms that same identifier immediately. For an existing listing, use its exact current identifier.
- Updating an existing `version` **merges** the supplied fields into that version — fields you omit keep their current values (the listing's README and install options are preserved). Use a **new** `version` for actual releases of the server; it starts from the previous latest version with your fields applied.
- `homepage` and `cloudEndpoint` are owner-managed listing fields. Supplying them stores/updates them; omitting them during update preserves their current values. `cloudEndpoint` is authoritative for the preferred remote deployment URL shown to users, while crawler-derived auth schemas and installation details are preserved.
- Updating marks the version **validated** (owner-updated versions are trusted), so the listing drops the "Unvalidated" badge.
- The display **name / description / tags** are per-language. Your `name`/`description`/`tags` are the `en-US` source (verbatim, never machine-translated); other locales are translated from it automatically. To control a translation yourself, add a `localizations` array to the manifest, or use `lhm plugin i18n set` (see below). Owner-provided locales are authoritative and are never overwritten by the translator or a re-crawl.

Full field table, capability arrays (`tools` / `resources` / `prompts`), the `localizations` array, URL-validated fields, and complete examples: [references/manifest.md](references/manifest.md)

## Update

```bash
npx -y @lobehub/market-cli plugin update --dir /home/user/projects/my-mcp
```

Successful output:

```
✓ Authenticated as Jane Smith
  Reading lhm.plugin.json...
✓ Updated joshuayoes-ios-simulator-mcp (1.3.0 → 1.4.0)
```

The CLI validates the manifest, verifies you own the plugin (via `plugin list`), and posts the version. A new version becomes the latest, and translations are generated automatically. Updating the same `version` again changes that version in place (merge), so re-running after a partial failure is safe; bump `version` when the server itself has a new release.

## Verify & Manage

```bash
# Confirm the new version is live
npx -y @lobehub/market-cli plugin list --output json
# Optional public check (needs M2M identity from `lhm register`)
npx -y @lobehub/market-cli mcp view joshuayoes-ios-simulator-mcp --output json

# Delist / re-list
npx -y @lobehub/market-cli plugin unpublish joshuayoes-ios-simulator-mcp
npx -y @lobehub/market-cli plugin republish joshuayoes-ios-simulator-mcp

# Permanently delete (irreversible!)
npx -y @lobehub/market-cli plugin delete joshuayoes-ios-simulator-mcp --yes
```

`delete` is permanent and cannot be undone. `--yes` skips the CLI's confirmation prompt — only pass it after the user has explicitly confirmed the deletion in conversation.

## Errors

| Error                                                                                                | Cause                                                   | What to do                                                                                                                                                                |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ``Not logged in. Run `lhm login` first.``                                                            | No user credentials                                     | Run `lhm login` (needs human, see Interactive Steps)                                                                                                                      |
| ``Session expired. Run `lhm login` again.``                                                          | Refresh token expired                                   | Re-run `lhm login` (needs human); do not retry the failed command first                                                                                                   |
| ``No credentials found. Run `lhm register` first or set MARKET_CLIENT_ID and MARKET_CLIENT_SECRET.`` | `mcp ...` commands use the M2M identity, not your login | Run `lhm register` once (see references/lhm-commands.md), or verify with `lhm plugin list` instead                                                                        |
| ``You don't own plugin "x". Use `lhm plugin claim x` first.``                                        | Plugin not in your owned list                           | Run `lhm plugin claim x` once, then retry update                                                                                                                          |
| `Claim failed: Plugin "x" not found`                                                                 | Not listed under that identifier                        | Check the identifier with `lhm mcp search --q ...`; if the plugin is not in the marketplace at all, publish it with `lhm plugin publish <repo-url>` (see Critical Rule 1) |
| `Claim failed: You do not have push access to this repository.`                                      | GitHub not connected, or no push access to the repo     | Check `lhm github status`; connect an account that can push to the plugin's repository (org-owned repos work as long as you have push access)                             |
| `Publish failed: GitHub user "x" does not have push access to repository "org/repo" ...`             | The connected account cannot write to the repository    | Connect a GitHub account with push access, ask the organization to grant access, or use the website submission flow                                                       |
| `Publish failed: You must link and verify your GitHub account ...`                                   | GitHub not connected                                    | Run `lhm github connect` (needs human, see Interactive Steps)                                                                                                             |
| `lhm.plugin.json not found in <dir>`                                                                 | Wrong directory                                         | Pass `--dir` with the absolute path to the directory containing the manifest                                                                                              |
| 400 validation error on update                                                                       | Invalid field (e.g. `authorUrl` is not a valid URL)     | Fix the field per [references/manifest.md](references/manifest.md), then retry once                                                                                       |

Full per-command error tables: [references/lhm-commands.md](references/lhm-commands.md)

## Everything You Can Do

| Goal                      | Command                                                  | Interactive?            |
| ------------------------- | -------------------------------------------------------- | ----------------------- |
| Check auth state          | `lhm auth status --output json`                          | No                      |
| Log in                    | `lhm login`                                              | **Yes (browser)**       |
| Check GitHub connection   | `lhm github status`                                      | No                      |
| Connect GitHub            | `lhm github connect`                                     | **Yes (browser)**       |
| List owned plugins        | `lhm plugin list --output json`                          | No                      |
| Publish a new listing     | `lhm plugin publish <repo-url>`                          | No                      |
| Claim an existing plugin  | `lhm plugin claim <identifier>`                          | No                      |
| Update an existing plugin | `lhm plugin update --dir <absolute-path>`                | No                      |
| List localizations        | `lhm plugin i18n list <identifier>`                      | No                      |
| Edit a localization       | `lhm plugin i18n set <identifier> --locale <locale> ...` | No                      |
| Remove a localization     | `lhm plugin i18n rm <identifier> --locale <locale>`      | No                      |
| Inspect a live listing    | `lhm mcp view <identifier> --output json`                | No                      |
| Find a listing            | `lhm mcp search --q <keywords>`                          | No                      |
| Delist / re-list          | `lhm plugin unpublish/republish <identifier>`            | No                      |
| Delete permanently        | `lhm plugin delete <identifier> --yes`                   | No (ask the user first) |

`mcp view` / `mcp search` authenticate with the M2M agent identity (run `lhm register` once); every other command above uses your user login.


---

<!-- verified-against: @lobehub/market-cli@next; last-synced: 2026-08-05 -->

# lhm Command Reference — MCP Publishing

Every command below runs as `npx -y @lobehub/market-cli <command>`; `lhm` is the global-install shorthand. Commands that support `--output json` should be run that way when a program needs to parse the result.

## login

Log in as a human user via OIDC PKCE browser flow. Opens a browser, listens on `localhost:51234`–`51243` for the OAuth callback (up to 5 minutes), then stores credentials in `~/.lobehub-market/user-credentials.json` (mode 0600).

```bash
npx -y @lobehub/market-cli login [--base-url https://market.lobehub.com]
```

```
Opening browser for authentication...
If your browser does not open, visit:
  https://market.lobehub.com/lobehub-oidc/auth?client_id=...

✓ Logged in as Jane Smith (jane@example.com)
```

Tokens auto-refresh on every subsequent command; re-login is only needed when a command fails with ``Session expired. Run `lhm login` again.``

`--base-url` targets a self-hosted or staging marketplace. The `MARKET_BASE_URL` environment variable does the same for `login` and the M2M commands (`mcp ...`, `auth ...`) only — `github ...` and `plugin ...` commands always use the base URL saved in the credentials file at login time, so re-run `lhm login` to switch marketplaces.

## logout

Remove the stored user credentials (M2M credentials are unaffected).

```bash
npx -y @lobehub/market-cli logout
```

## auth status

Show M2M and user authentication state. **Exits with code 1 when no credentials of either kind exist** — treat that as "not logged in".

```bash
npx -y @lobehub/market-cli auth status --output json
```

```json
{
  "m2m": { "status": "not configured" },
  "user": {
    "displayName": "Jane Smith",
    "email": "jane@example.com",
    "expiresAt": "2026-06-12T10:00:00.000Z",
    "status": "authenticated",
    "userId": "user_abc123"
  }
}
```

`user.status` is one of `authenticated`, `token expired`, or `not logged in`. `token expired` still publishes fine — commands refresh the token automatically. The `m2m` section is irrelevant to publishing: M2M credentials have no publish permission.

## github connect

Connect your GitHub account via OAuth. Required once before claiming, publishing, or updating. The connection provides the verified username and OAuth token used for repository access checks. Opens a browser and polls every 2 seconds for up to 5 minutes.

```bash
npx -y @lobehub/market-cli github connect
```

```
Opening browser for GitHub OAuth...
If your browser does not open, visit:
  https://market.lobehub.com/api/connect/github/start?code=...

Waiting for GitHub authorization...

✓ GitHub connected as janedoe
```

Requires being logged in first. On timeout, re-run the command.

## github status / github disconnect

```bash
npx -y @lobehub/market-cli github status
# ✓ GitHub connected as janedoe
# ✗ GitHub not connected. Run `lhm github connect` to connect.

npx -y @lobehub/market-cli github disconnect
# ✓ GitHub disconnected
```

Disconnecting blocks new claims but already-claimed plugins remain yours.

## plugin init

Generate an owner-manifest draft by connecting directly to the MCP server. This command is local: it requires neither login nor GitHub OAuth and does not publish or invoke the repository crawler.

```bash
# The process is started with --dir as its working directory
npx -y @lobehub/market-cli plugin init --stdio "node dist/index.js" --dir /home/user/weather-mcp

# Or inspect a running Streamable HTTP endpoint
npx -y @lobehub/market-cli plugin init --url https://weather.example.com/mcp --dir /home/user/weather-mcp
```

Exactly one of `--stdio` and `--url` is required. The generator initializes MCP, follows pagination for tools, resources, resource templates, and prompts, and combines that protocol data with `package.json` and Git/GitHub metadata. It writes two-space JSON with a trailing newline to `<dir>/lhm.plugin.json`.

| Option              | Default           | Description                                                        |
| ------------------- | ----------------- | ------------------------------------------------------------------ |
| `--dir <path>`      | current directory | Plugin directory and stdio working directory                       |
| `--stdio <command>` | —                 | Safely tokenize and start an MCP stdio command without a shell     |
| `--url <url>`       | —                 | Connect to a running HTTP(S) Streamable HTTP MCP endpoint          |
| `--force`           | false             | Replace an existing `lhm.plugin.json` instead of refusing to write |

Review the generated file before publication. It is only a draft at generation time; after saving and publishing it, the manifest—not the generator or crawler—is the owner-declared source of truth.

## plugin list

List plugins owned by your account. Claimable-but-unclaimed plugins do **not** appear here — `lhm plugin claim <identifier>` discovers those through a separate claim scan.

```bash
npx -y @lobehub/market-cli plugin list --output json
```

Text output:

```
IDENTIFIER              NAME                LATEST VERSION  STATUS     CLAIMED
janedoe-weather-mcp     Weather MCP         2.0.1           published  yes
janedoe-db-mcp          DB MCP              -               published  no

2 plugin(s)
```

`CLAIMED: no` means the plugin was assigned to your account without an explicit claim (e.g. assigned at import time); you can still update it. With no plugins at all it prints ``No plugins found. Use `lhm plugin publish <gitUrl>` to list a new plugin, or `lhm plugin claim <identifier>` to claim an existing one.``

## plugin publish

Publish the owner declaration in `lhm.plugin.json` as a **new** MCP plugin listing, then start asynchronous enrichment from a GitHub repository you own.

```bash
npx -y @lobehub/market-cli plugin publish https://github.com/janedoe/weather-mcp --dir /home/user/weather-mcp
```

```
✓ Authenticated as Jane Smith
✓ Published janedoe-weather-mcp@1.0.0
Repository enrichment for janedoe/weather-mcp is processing.
```

Requires a local manifest with non-empty `identifier`, `name`, and `version`; validation happens before authentication or network access. `--dir <path>` selects its directory and defaults to the current directory. Requires login + GitHub connection. Repositories owned by your username are accepted directly; all others require push or admin access. `--output json` prints the typed server response, including the concrete identifier/version and `status: "processing"`. Repository publication/import is limited to 10 attempts per account per hour.

The listing and owner-declared version exist when the command succeeds. Repository crawling is enrichment only and may continue after the response; it does not assign the identifier or overwrite owner fields. If the same repository already has an unclaimed listing under that identifier, publish claims and converges it. Retrying the same initial identifier/version is safe, but once publication is established a new version must use `lhm plugin update`. A taken identifier or repository bound to a different identifier returns a conflict. There is currently no dedicated enrichment-status CLI command.

## plugin claim

Claim ownership of a plugin that already exists in the marketplace.

```bash
npx -y @lobehub/market-cli plugin claim janedoe-weather-mcp
# ✓ Claimed ownership of plugin "janedoe-weather-mcp"
```

On failure:

```
Plugin "janedoe-weather-mcp" is not claimable. Make sure:
  1. The plugin exists in the marketplace
  2. Your GitHub account is connected (lhm github connect)
  3. Your GitHub username matches the plugin's author
```

Requires login + GitHub connection. The claim scan matches your GitHub username against the plugin's GitHub homepage URL — only a direct repo-owner match is discovered by the scan; org-repo collaborators with push/admin access cannot claim through the CLI today.

## plugin update

Update an existing plugin from `lhm.plugin.json` (see [manifest.md](manifest.md)).

```bash
npx -y @lobehub/market-cli plugin update --dir /home/user/projects/my-mcp
```

| Option         | Default           | Description                            |
| -------------- | ----------------- | -------------------------------------- |
| `--dir <path>` | current directory | Directory containing `lhm.plugin.json` |

Flow: parses the manifest → checks `identifier` / `name` / `version` are present → verifies the plugin is in your `plugin list` → posts the version. Success:

```
✓ Authenticated as Jane Smith
  Reading lhm.plugin.json...
✓ Updated janedoe-weather-mcp (2.0.0 → 2.0.1)
```

Updating the same `version` changes that version in place — supplied fields are merged, omitted fields keep their current values — so retrying after a partial failure is safe. Bump `version` when the server itself has a new release; the new version starts from the previous latest with your fields applied. The updated version is also marked **validated** (drops the "Unvalidated" badge).

## plugin i18n (list / set / rm)

Manage the per-language **name / description / summary / tags** of a plugin version. `en-US` is the source of truth (your manifest `name`/`description`/`tags`); other locales are translated from it automatically. These commands let you override or correct any locale yourself — owner-provided locales are authoritative and are never overwritten by the translator or a re-crawl. All operate on the **latest** version unless you pass `--version`.

```bash
# List current localizations
npx -y @lobehub/market-cli plugin i18n list janedoe-weather-mcp

# Set/correct one locale from flags (only supplied fields change)
npx -y @lobehub/market-cli plugin i18n set janedoe-weather-mcp \
  --locale zh-CN --name "天气 MCP" --description "实时天气查询" --tags "天气,API"

# Set one or many locales from a JSON file (one object or an array of objects)
npx -y @lobehub/market-cli plugin i18n set janedoe-weather-mcp --file ./i18n.json

# Remove a locale (en-US cannot be removed — it is the source)
npx -y @lobehub/market-cli plugin i18n rm janedoe-weather-mcp --locale zh-CN
```

| Command                  | Key options                                                                                           | Notes                                                                                                                                           |
| ------------------------ | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `i18n list <identifier>` | `--version`, `--output json`                                                                          | Lists localizations of the target version                                                                                                       |
| `i18n set <identifier>`  | `--locale`, `--name`, `--description`, `--summary`, `--tags` (comma-separated), `--file`, `--version` | Merge: only supplied fields overwrite. A brand-new locale requires both `--name` and `--description`. Editing `en-US` also updates the listing. |
| `i18n rm <identifier>`   | `--locale` (required), `--version`                                                                    | Cannot remove `en-US`                                                                                                                           |

The `--file` payload is a localization object `{ "locale": "zh-CN", "name"?, "description"?, "summary"?, "tags"? }` or an array of them. Every object must include `locale`.

## plugin unpublish / republish

Delist or re-list a plugin (the listing and its versions are kept).

```bash
npx -y @lobehub/market-cli plugin unpublish janedoe-weather-mcp
# ✓ Plugin "janedoe-weather-mcp" has been delisted (unpublished)

npx -y @lobehub/market-cli plugin republish janedoe-weather-mcp
# ✓ Plugin "janedoe-weather-mcp" is now listed (published)
```

Both accept `--output json`.

## plugin delete

Permanently delete an owned plugin and all its versions. **Irreversible.**

```bash
npx -y @lobehub/market-cli plugin delete janedoe-weather-mcp --yes
# ✓ Plugin "janedoe-weather-mcp" has been permanently deleted
```

Without `--yes` the CLI prompts `Are you sure you want to permanently delete plugin "..."? This cannot be undone. [y/N]` on the TTY. Agents should pass `--yes` only after the user has explicitly confirmed the deletion in conversation.

## register (M2M agent identity)

One-time machine-to-machine registration; this is what the read-only `mcp ...` commands authenticate with. It has no publish permission and is independent of `lhm login`. Re-running on the same device returns the existing credentials — safe to repeat.

```bash
npx -y @lobehub/market-cli register --name "My Agent" --source claude-code
```

| Option          | Required | Description                                                         |
| --------------- | -------- | ------------------------------------------------------------------- |
| `--name`        | Yes      | A distinctive display name for the agent                            |
| `--source`      | No       | Agent platform (e.g. `claude-code`, `open-claw`, `codex`, `cursor`) |
| `--description` | No       | Short description of the agent                                      |

## mcp search / mcp view

Read-only marketplace queries — useful for finding the exact `identifier` and verifying a publish went live.

**These authenticate with M2M credentials, not your user login.** Run `lhm register --name <agent-name> --source <platform>` once (or set `MARKET_CLIENT_ID` / `MARKET_CLIENT_SECRET`) before using them; without M2M credentials they exit 1 with ``No credentials found. Run `lhm register` first or set MARKET_CLIENT_ID and MARKET_CLIENT_SECRET.`` If M2M is unavailable, verify a publish with `lhm plugin list --output json` instead.

```bash
npx -y @lobehub/market-cli mcp search --q "weather" --output json
npx -y @lobehub/market-cli mcp view janedoe-weather-mcp --output json
```

`mcp search` supports `--category`, `--sort`, `--order`, `--page`, `--page-size`, `--locale`. `mcp view` supports `--version`, `--locale`, and `-c, --comments`. Note: a plugin missing from public search/view does not prove the identifier is free — it may be delisted. Trust `plugin list` / `plugin claim` errors over `mcp view` 404s.

## Environment Variables

| Variable                                    | Purpose                                                                                                         |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `MARKET_BASE_URL`                           | Overrides the base URL for `login` and M2M commands; `github`/`plugin` commands use the base URL saved at login |
| `MARKET_CLIENT_ID` / `MARKET_CLIENT_SECRET` | M2M agent identity, used by `mcp ...` commands (search/rate/comment only — **cannot publish**)                  |

## Error Reference

| Error                                                                                                | Exit | Retryable?                  | What to do                                                                                                           |
| ---------------------------------------------------------------------------------------------------- | ---- | --------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| ``Not logged in. Run `lhm login` first.``                                                            | 1    | After login                 | Run `lhm login` (human + browser)                                                                                    |
| ``Session expired. Run `lhm login` again.``                                                          | 1    | After login                 | Run `lhm login` (human + browser)                                                                                    |
| ``No credentials found. Run `lhm register` ... or `lhm login` ...``                                  | 1    | After login                 | From `auth status` on a clean machine — run `lhm login`                                                              |
| ``No credentials found. Run `lhm register` first or set MARKET_CLIENT_ID and MARKET_CLIENT_SECRET.`` | 1    | After register              | From `mcp ...` commands — run `lhm register` once, or verify with `plugin list` instead                              |
| ``You don't own plugin "x". Use `lhm plugin claim x` first.``                                        | 1    | After claim                 | Run `lhm plugin claim x`, then retry update once                                                                     |
| `Plugin "x" is not claimable`                                                                        | 1    | Only after fixing the cause | Check GitHub connection and identifier; if not listed at all, publish your repo with `lhm plugin publish <repo-url>` |
| `Publish failed: GitHub user "x" does not have push access to repository "org/repo" ...`             | 1    | Only after fixing the cause | Connect a GitHub account with push access, ask the organization to grant access, or use the website submission flow  |
| `Publish failed: You must link and verify your GitHub account ...`                                   | 1    | After connect               | Run `lhm github connect` (human + browser)                                                                           |
| `Publish failed: Too many repository submissions ...`                                                | 1    | After ~1 hour               | The shared publication/import budget is 10 attempts per account per hour                                             |
| `lhm.plugin.json not found in <dir>`                                                                 | 1    | After fix                   | Pass `--dir` with the correct absolute path, or create the manifest                                                  |
| `Failed to parse lhm.plugin.json: ...`                                                               | 1    | After fix                   | Fix the JSON syntax error                                                                                            |
| `lhm.plugin.json must include a/an "..." field.`                                                     | 1    | After fix                   | Add the missing `identifier` / `name` / `version` field                                                              |
| 400 validation message naming a field                                                                | 1    | After fix                   | Fix the field per [manifest.md](manifest.md), retry once                                                             |
| 5xx / network errors                                                                                 | 1    | Once                        | Retry once; if it persists, stop and report to the user                                                              |


---

<!-- verified-against: @lobehub/market-cli@next; last-synced: 2026-08-05 -->

# lhm.plugin.json Reference

Complete schema for the manifest consumed by both `lhm plugin publish` and `lhm plugin update`.

## Generate a Draft

The CLI can initialize an MCP connection and generate this file locally:

```bash
# Start a stdio server from the plugin directory
lhm plugin init --stdio "node dist/index.js" --dir /path/to/plugin

# Or inspect an already-running Streamable HTTP server
lhm plugin init --url https://example.com/mcp --dir /path/to/plugin
```

`init` reads MCP server info and all pages of `tools/list`, `resources/list`, `resources/templates/list`, and `prompts/list`. It supplements that protocol data with `package.json` and the Git/GitHub remote; a URL endpoint is also written as `cloudEndpoint`. Because the manifest has one resource capability array, resource templates are included in `resources` with their standard `uriTemplate` shape.

This is a local generator, not a marketplace crawler or publication request. The generated file is a draft until the developer reviews it. `publish` and `update` only consume the saved file; they do not re-run introspection. Existing files are protected by default—use `--force` only when replacing one intentionally.

## Fields

| Field           | Type       | Required | Constraints                              | Description                                                                                                              |
| --------------- | ---------- | -------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `identifier`    | `string`   | Yes      | First publish: `^[\da-z][\d_a-z-]*$`     | Owner-declared before first publish; must match the listing on update                                                    |
| `name`          | `string`   | Yes      | Non-empty                                | Display name shown in the marketplace                                                                                    |
| `version`       | `string`   | Yes      | Non-empty                                | Version label; the same value merges in place and a new value creates a release                                          |
| `author`        | `string`   | No       | —                                        | Author display name                                                                                                      |
| `authorUrl`     | `string`   | No       | Must be a valid URL                      | Author profile URL (e.g. GitHub profile)                                                                                 |
| `category`      | `string`   | No       | First publish: marketplace category enum | Marketplace category name (for example `developer`, `productivity`, `tools`, or `weather`)                               |
| `cloudEndpoint` | `string`   | No       | Must be a valid URL                      | Canonical URL for the owner-managed preferred remote deployment                                                          |
| `description`   | `string`   | No       | —                                        | Short description of what the plugin does                                                                                |
| `homepage`      | `string`   | No       | Must be a valid URL                      | Owner-managed homepage or repository URL stored on the listing                                                           |
| `icon`          | `string`   | No       | —                                        | Icon (emoji or image URL)                                                                                                |
| `localizations` | `object[]` | No       | Each item needs a `locale`               | Owner-provided translations (see [Localizations](#localizations-i18n)). en-US is the source and also updates the listing |
| `prompts`       | `object[]` | No       | Array of objects                         | MCP prompt template definitions                                                                                          |
| `resources`     | `object[]` | No       | Array of objects                         | MCP resource definitions                                                                                                 |
| `tags`          | `string[]` | No       | Array of strings                         | Search/discovery tags                                                                                                    |
| `tools`         | `object[]` | No       | Array of objects                         | MCP tool definitions (standard MCP tool shape: `name`, `description`, `inputSchema`)                                     |

Unknown extra fields are silently stripped by the server. Omitted fields use merge semantics on update, so leaving out `homepage` or `cloudEndpoint` preserves the existing listing value. When `cloudEndpoint` is supplied, it is authoritative for the preferred HTTP/SSE deployment URL shown to users; crawler-derived authentication schemas, descriptions, installation details, and other deployment options remain intact.

## Capability Flags

The marketplace derives the listing's capability badges from the manifest: a non-empty `tools` array sets the "tools" capability, and likewise for `resources` and `prompts`. To advertise what your MCP server can do, declare the actual definitions — there is no separate capabilities field.

## Localizations (i18n)

The marketplace shows a per-language **name / description / summary / tags**. `en-US` is the **source of truth** — it holds your declared `name`/`description`/`tags` verbatim and is never machine-translated. Every other locale is translated from it automatically in the background.

You can override any locale yourself in two ways:

- **Inline in `lhm.plugin.json`** — add a `localizations` array; it is applied on publish and update.
- **Standalone, without updating the full manifest** — `lhm plugin i18n set <identifier> --locale zh-CN --name ...` (see [references/lhm-commands.md](lhm-commands.md)).

Each localization object: `{ "locale": "zh-CN", "name"?, "description"?, "summary"?, "tags"? }`. First publication requires both `name` and `description` for every supplied locale. On update, only supplied fields overwrite; creating a brand-new locale still requires both `name` and `description`. Owner-provided locales are authoritative — the background translator only fills the locales you have **not** provided, and a re-crawl never overwrites them.

```json
{
  "description": "A UniProt protein database MCP server",
  "identifier": "fzlzjerry-uniprot",
  "localizations": [
    {
      "description": "UniProt 蛋白质数据库 MCP 服务器",
      "locale": "zh-CN",
      "name": "UniProt 蛋白质数据库"
    }
  ],
  "name": "UniProt",
  "version": "0.1.0"
}
```

## What Happens on Update

1. An unknown `identifier` fails with `Plugin "x" not found` (the CLI normally catches this earlier as `You don't own plugin "x"`)
2. Ownership is verified; update requires the authenticated account to own and have claimed the listing. First publication handles ownership verification and can claim a matching unclaimed repository listing
3. If the `version` already exists, the supplied fields are merged into that version (omitted fields keep their current values); otherwise a new version is created, starting from the previous latest version with your fields applied, and marked as the latest
4. The updated version is marked **validated** (owner-updated versions are trusted), so the listing no longer shows "Unvalidated"
5. Any supplied `localizations` are applied, then translations for the remaining locales are generated automatically in the background — they do not block or fail the update
6. If `cloudEndpoint` is supplied, public MCP configuration uses it instead of a crawler-inferred remote URL, including after later repository enrichment

## Examples

### Minimal

```json
{
  "description": "Control the iOS Simulator from MCP",
  "identifier": "joshuayoes-ios-simulator-mcp",
  "name": "iOS Simulator MCP",
  "version": "1.4.0"
}
```

### Cloud-hosted MCP server with tools

```json
{
  "author": "Jane Smith",
  "authorUrl": "https://github.com/janedoe",
  "cloudEndpoint": "https://weather-mcp.example.com/mcp",
  "description": "Real-time weather lookups for any city",
  "homepage": "https://github.com/janedoe/weather-mcp",
  "identifier": "janedoe-weather-mcp",
  "name": "Weather MCP",
  "tags": ["weather", "api"],
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather for a city",
      "inputSchema": {
        "type": "object",
        "properties": { "city": { "type": "string" } },
        "required": ["city"]
      }
    }
  ],
  "version": "2.1.0"
}
```

### Full

```json
{
  "author": "Jane Smith",
  "authorUrl": "https://github.com/janedoe",
  "category": "developer",
  "cloudEndpoint": "https://my-mcp.example.com/mcp",
  "description": "Browse, query, and edit project databases over MCP",
  "homepage": "https://github.com/janedoe/db-mcp",
  "icon": "🗄️",
  "identifier": "janedoe-db-mcp",
  "name": "DB MCP",
  "prompts": [
    {
      "name": "explain_schema",
      "description": "Explain the schema of a connected database"
    }
  ],
  "resources": [
    {
      "name": "schema",
      "description": "Live database schema",
      "uri": "db://schema"
    }
  ],
  "tags": ["database", "sql"],
  "tools": [
    {
      "name": "run_query",
      "description": "Run a read-only SQL query",
      "inputSchema": {
        "type": "object",
        "properties": { "sql": { "type": "string" } },
        "required": ["sql"]
      }
    }
  ],
  "version": "3.0.0"
}
```

## Common Manifest Errors

| Symptom                                               | Fix                                                                                       |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `lhm.plugin.json must include an "identifier" field.` | Add `identifier` matching the marketplace listing                                         |
| `lhm.plugin.json must include a "name" field.`        | Add a non-empty `name`                                                                    |
| `lhm.plugin.json must include a "version" field.`     | Add a non-empty `version`                                                                 |
| `Failed to parse lhm.plugin.json: ...`                | Fix the JSON syntax error reported in the message                                         |
| 400 with a validation message mentioning a URL field  | `authorUrl`, `cloudEndpoint`, and `homepage` must be absolute, valid URLs (`https://...`) |
| 400 mentioning `tools` / `resources` / `prompts`      | These must be arrays of objects, not a single object or strings                           |
