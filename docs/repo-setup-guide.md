# Repo setup guide: sqlfluff-mcp-server

A one-time runbook for taking this project from a local folder to a published,
protected, CI/CD-backed GitHub repo, and getting it listed in MCP directories.
The code itself already has a working CI workflow, tests, and a PyPI publish
workflow (`.github/workflows/ci.yml` and `.github/workflows/publish.yml`) —
this doc is about the GitHub/PyPI/directory-side configuration around it.

## 1. Create the GitHub repository

The local git repo already exists (branch `main`, one clean commit). Two ways
to create the remote:

**Via the `gh` CLI (recommended — does init + push in one step):**

```bash
cd /path/to/sqlfluff-mcp-server
gh repo create sqlfluff-mcp-server --public \
  --source=. --remote=origin \
  --description "MCP server exposing SQLFluff's lint/fix/parse over the Model Context Protocol" \
  --push
```

**Via the web UI:**

1. Go to <https://github.com/new>.
2. Repository name: `sqlfluff-mcp-server`. Public. Do **not** initialize with
   a README/.gitignore/license — this repo already has them, and GitHub will
   refuse to push if histories conflict.
3. Create, then locally:

   ```bash
   git remote add origin git@github.com:<your-username>/sqlfluff-mcp-server.git
   git push -u origin main
   ```

Either way, afterward set the repo's About section (gear icon on the repo
homepage) — description, topics (`mcp`, `sqlfluff`, `sql`, `linter`,
`model-context-protocol`), and the homepage URL if you have one. Topics are
how people find the repo via GitHub search and is one of the signals
directory sites like mcpservers.org look at.

## 2. Branch protection (no direct pushes to `main`)

Settings → Code and automation → **Branches** → **Add branch protection
rule**.

- Branch name pattern: `main`
- Check **Require a pull request before merging**. As a solo maintainer, you
  can leave "Require approvals" at 0 — the point is forcing every change
  through a PR (so CI runs and you get a diff view) rather than requiring a
  second human. Raise it to 1+ once you have collaborators.
- Check **Require status checks to pass before merging**, then search for
  and select the `test` job from your CI workflow (it'll appear in the list
  after the workflow has run at least once, so do this after your first PR).
  Also check **Require branches to be up to date before merging**.
- Check **Require conversation resolution before merging**.
- Leave **Do not allow bypassing the above settings** checked unless you
  specifically want an escape hatch for emergency fixes — if unchecked, repo
  admins (i.e. you) can still push straight to `main` when needed.
- Leave **Allow force pushes** and **Allow deletions** unchecked.

This combination is what actually prevents `git push origin main`: without a
PR, the push is rejected outright.

GitHub's newer **Rulesets** (Settings → Rules → Rulesets) are the
longer-term direction, are also free on public repos, and can layer with
protection rules — a classic branch protection rule is still simpler for a
single-branch solo project and works everywhere, so is what's described
above. Reference: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets).

## 3. CI/CD pipeline

Already committed:

- **`.github/workflows/ci.yml`** — runs on every push to `main` and every
  PR. Installs the project with dev extras, runs `ruff check .`, runs
  `pytest -v` across Python 3.10–3.12. This is what you'll select as the
  required status check in step 2.
- **`.github/workflows/publish.yml`** — runs when you publish a GitHub
  Release. Builds the sdist/wheel and pushes to PyPI using **Trusted
  Publishing** (OIDC) rather than a stored API token.

One-time PyPI-side setup for trusted publishing (do this before your first
release):

1. Create the project on PyPI once, either by uploading a first release
   manually (`pip install build twine && python -m build && twine upload
   dist/*` with a temporary API token) or via PyPI's "pending publisher"
   flow if the project name is still free.
2. On PyPI, go to your project → Settings → Publishing → **Add a new
   publisher**. Choose GitHub, and fill in:
   - Owner: your GitHub username
   - Repository: `sqlfluff-mcp-server`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. In the GitHub repo, Settings → Environments → **New environment** named
   `pypi` (matches the `environment: pypi` in the workflow). Optionally add
   a required reviewer on that environment as a manual gate before publish.

From then on, cutting a GitHub Release (Releases → Draft a new release, tag
e.g. `v0.1.0`) triggers the publish workflow automatically — no secrets to
rotate or leak.

## 4. Getting listed in MCP directories

These are third-party sites; requirements can change, so treat this as a
starting point and check the live submission pages before you submit.

**mcpservers.org**

1. Push the repo and make sure the README clearly states what the server
   does and lists its tools (this repo's README already has a tools table).
2. Go to <https://mcpservers.org/submit> and fill in: Server Name, a short
   description, the GitHub link, a category (this project fits
   "Development" or "Database"), and a contact email.
3. Free listing; there's an optional one-time $39 "Premium Submit" for
   faster review and a badge — not necessary to get listed.

**LobeHub MCP Marketplace**

1. Full current workflow lives at
   <https://market.lobehub.com/s/publish-mcp> — read it first since this is
   a CLI-driven flow that has changed shape before.
2. Broadly: install LobeHub's CLI, verify GitHub ownership of the repo, add
   an `lhm.plugin.json` manifest to the repo describing the server, then run
   `lhm plugin submit <repo-url>`.
3. Listings are reviewed and typically published within 24 hours.
   LobeHub pulls metadata (description, stars, license, README) directly
   from GitHub, so a clean README and topics help here too.

**Also worth doing** (not requested, but low-effort and high-visibility for
an MCP server):

- Open a PR adding this project to
  [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)'s
  community list, or [wong2/awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers) —
  both are widely linked-to curated lists.
- Register with the official [MCP Registry](https://github.blog/ai-and-ml/generative-ai/how-to-find-install-and-manage-mcp-servers-with-the-github-mcp-registry/)
  now surfaced through GitHub itself, which is becoming the canonical
  discovery source for MCP servers.
