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
