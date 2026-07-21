# Omnissiah Build Spec (authoritative)

This is the contract every builder works against. Do not deviate from variable
names, file paths, or the CLI interface defined here. If something is
underspecified, make the smallest reasonable choice consistent with the design
philosophy below and note it.

## What Omnissiah is

Omnissiah is a **generator**. A friend clones it, runs an interactive CLI, answers
~8 questions, and gets a personalized "personal operating system" repo for their
own bounded assistant: a parameterized governance layer (operating contract,
assistant profile, host config) PLUS a runnable, provider-agnostic MCP server
skeleton with one real example tool they can extend.

It is modeled on Wintermute (a private RevOps assistant boundary). The point of
Omnissiah is to hand other people Wintermute's *strengths* without its private
contents:

1. A concrete **operating contract** (modes, control loop, safety/reversibility).
2. A scoped, auditable **MCP tool boundary** (not ambient authority).
3. The **"safe but permissive" balance**: capable enough to act, conservative
   enough to leave tracks. Drafts over sends. Verify on high-stakes facts.
   Capture is messy but drains. Move when the next action is clear.

The generated repo must be usable with Claude Code, Codex, or any MCP host.

## Design philosophy (the middle-ground defaults: bake these IN, ON by default)

Every generated artifact must ship these defaults enabled, each with a one-line
inline rationale so a friend can tune them knowingly rather than discover them:

- **Drafts over sends.** Outbound email/messages are created as reviewable drafts; the human sends.
- **List -> read -> act.** Never act on a record (archive/label/reply) without reading it first.
- **Single events over fragile recurrence** for short protocols (meds, travel, sprints).
- **Verify on high-stakes input:** dates, money, health, legal, external-system state, current facts.
- **Capture is allowed to be messy, but it drains.** One capture surface, drained on a cadence; never stand up a second inbox.
- **No destructive fs/git** unless the principal explicitly asks for that operation.
- **Secrets stay local:** never in commits, notes, chat summaries, or docs.
- **Scoped MCP tools over broad ambient authority** when touching external systems.
- **Move when the next action is clear; ask the smallest necessary question** otherwise.
- **Concrete communication.** No flattery, no approval language as a substitute for reporting actions/evidence/results.
- **Durable context survives the chat:** tasks to the task system, durable decisions to repo docs.

These are presented as the recommended balance. The generator should let a friend
override surface details (name, role, tools) but should *not* make it easy to
silently turn off the safety posture; if they want to, they edit the contract by hand.

## Template variables

All templates use `{{VAR}}` substitution (double braces, exact names below).
Rendering is plain string replacement (no Jinja/mustache dependency).

| Variable | Meaning | Example |
|---|---|---|
| `{{ASSISTANT_NAME}}` | Display name of the assistant | `Wintermute` |
| `{{ASSISTANT_SLUG}}` | snake_case, valid Python package + console-script prefix | `wintermute` |
| `{{ASSISTANT_TAGLINE}}` | one-line description | `a bounded personal operating assistant` |
| `{{PRINCIPAL_NAME}}` | the human it serves | `John` |
| `{{PRINCIPAL_ROLE}}` | one-line role | `a RevOps executive and consultant` |
| `{{PRINCIPAL_DOMAINS}}` | comma list of work domains | `Salesforce, HubSpot, AI workflows` |
| `{{TASK_SYSTEM}}` | where tasks/commitments live | `Asana` |
| `{{CHAT_SURFACE}}` | messaging surface or `none` | `Signal` |
| `{{TIMEZONE}}` | IANA tz | `America/New_York` |
| `{{TOOLS_EMAIL}}` | `true`/`false` scaffold email tools | `true` |
| `{{TOOLS_CALENDAR}}` | `true`/`false` scaffold calendar tools | `true` |
| `{{TOOLS_CHAT}}` | `true`/`false` scaffold chat tools | `true` |
| `{{GEN_DATE}}` | ISO date generated (CLI stamps real date) | `2026-06-23` |
| `{{GEN_YEAR}}` | year generated | `2026` |

Conditional blocks in templates use line-delimited markers the renderer honors:

```
{{#IF TOOLS_EMAIL}}
...email-specific lines...
{{/IF}}
```

Keep conditionals minimal; prefer prose that reads fine regardless. Only the MCP
server skeleton and SETUP doc truly need them.

## Output repo layout (what the friend's generated repo looks like)

```
<assistant-slug>/
  README.md
  SYSTEM-MAP.md
  ASSISTANT-PROFILE.md
  OPERATING-CONTRACT.md
  AGENTS.md
  CLAUDE.md                       # Claude Code adapter to AGENTS.md
  pyproject.toml
  .gitignore
  .env.example
  <assistant-slug>/               # python package (templates/pkg/ renamed)
    __init__.py
    mcp/
      __init__.py
      server.py                   # MCP server: health_check + example tool(s)
    integrations/
      __init__.py
      common.py                   # env loading, local paths
      providers/
        __init__.py
        base.py                   # provider-agnostic Protocols/ABCs
        notes.py                  # the runnable EXAMPLE provider (local JSON-backed)
  docs/
    integrations/
      SETUP.md                    # how to wire real providers + register MCP server
    playbooks/
      README.md                   # opt-in domain playbook loading rules
  tests/
    test_server_tools.py
    test_providers.py
```

## Template -> output path manifest (the renderer/CLI builds against THIS)

Source under `templates/`, written to the output dir. `.tmpl` suffix stripped.
`pkg/` directory is renamed to `{{ASSISTANT_SLUG}}/`.

| Template source | Output path |
|---|---|
| `templates/README.md.tmpl` | `README.md` |
| `templates/SYSTEM-MAP.md.tmpl` | `SYSTEM-MAP.md` |
| `templates/ASSISTANT-PROFILE.md.tmpl` | `ASSISTANT-PROFILE.md` |
| `templates/OPERATING-CONTRACT.md.tmpl` | `OPERATING-CONTRACT.md` |
| `templates/AGENTS.md.tmpl` | `AGENTS.md` |
| `templates/CLAUDE.md.tmpl` | `CLAUDE.md` |
| `templates/pyproject.toml.tmpl` | `pyproject.toml` |
| `templates/gitignore.tmpl` | `.gitignore` |
| `templates/env.example.tmpl` | `.env.example` |
| `templates/pkg/__init__.py.tmpl` | `<slug>/__init__.py` |
| `templates/pkg/mcp/__init__.py.tmpl` | `<slug>/mcp/__init__.py` |
| `templates/pkg/mcp/server.py.tmpl` | `<slug>/mcp/server.py` |
| `templates/pkg/integrations/__init__.py.tmpl` | `<slug>/integrations/__init__.py` |
| `templates/pkg/integrations/common.py.tmpl` | `<slug>/integrations/common.py` |
| `templates/pkg/integrations/providers/__init__.py.tmpl` | `<slug>/integrations/providers/__init__.py` |
| `templates/pkg/integrations/providers/base.py.tmpl` | `<slug>/integrations/providers/base.py` |
| `templates/pkg/integrations/providers/notes.py.tmpl` | `<slug>/integrations/providers/notes.py` |
| `templates/docs/integrations/SETUP.md.tmpl` | `docs/integrations/SETUP.md` |
| `templates/docs/playbooks/README.md.tmpl` | `docs/playbooks/README.md` |
| `templates/tests/test_server_tools.py.tmpl` | `tests/test_server_tools.py` |
| `templates/tests/test_providers.py.tmpl` | `tests/test_providers.py` |

The renderer discovers files by walking `templates/`, so the manifest is a guide,
not a hardcoded list; any `.tmpl` file added under `templates/` is rendered and
written to the mirrored path (with `pkg/` -> slug and `.tmpl` stripped). The CLI
must NOT hardcode the file list; it walks the tree.

## Generator CLI interface

Package: `omnissiah/` (the generator's own code, NOT a template).
Console script: `omnissiah = "omnissiah.cli:main"` in the root `pyproject.toml`.

Run interactively:
```
uv run omnissiah                      # asks ~8 questions, writes a repo
uv run omnissiah --output ../my-asst  # set output dir
```
Run non-interactively (required for testing + one-shot friends):
```
uv run omnissiah --answers answers.json --output <dir>
uv run omnissiah --defaults --output <dir>   # use the Wintermute-like demo defaults, no prompts
```

`--answers` JSON keys map to the template variables WITHOUT the `{{}}`, lowercased:
`assistant_name`, `principal_name`, `principal_role`, `principal_domains`,
`task_system`, `chat_surface`, `timezone`, `tools_email`, `tools_calendar`,
`tools_chat`. The CLI derives `assistant_slug` from `assistant_name`
(lowercase, non-alnum -> `_`, collapse repeats, strip), `assistant_tagline`
(sensible default), and stamps `gen_date`/`gen_year` from the real local date.

Behavior:
- Refuse to write into a non-empty output dir unless `--force`.
- After writing, print a "next steps" summary: cd, `git init`, edit `.env`,
  `uv run <slug>-mcp`, register in `~/.claude.json`.
- Validate: assistant_slug must be a valid Python identifier; timezone non-empty.
- Keep dependencies stdlib-only for the renderer (no Jinja). The CLI may use
  stdlib `argparse`, `json`, `pathlib`, `re`.

The `--defaults` profile (also the canonical test fixture) is:
```json
{
  "assistant_name": "Omnissiah",
  "principal_name": "Magos",
  "principal_role": "a systems operator and builder",
  "principal_domains": "engineering, ops, personal logistics",
  "task_system": "Asana",
  "chat_surface": "Signal",
  "timezone": "America/New_York",
  "tools_email": true,
  "tools_calendar": true,
  "tools_chat": true
}
```

## MCP server skeleton requirements

- Provider-agnostic. `providers/base.py` defines small Protocols/ABCs for the
  capability categories (e.g. `NoteStore`, and commented interface sketches for
  `EmailProvider`/`CalendarProvider`/`ChatProvider`) so a friend sees the shape
  to implement.
- `providers/notes.py` is a REAL, runnable provider backed by a local JSON file
  under a `var/` dir (gitignored). It demonstrates the safe-but-permissive
  boundary directly:
  - `notes_list` / `notes_read` = read (the list->read half).
  - `notes_append` = a real auditable local write (the act half).
  - `notes_draft_outbound` = creates a DRAFT record only, never "sends":
    the in-skeleton demonstration of drafts-over-sends.
- `server.py` exposes via MCP (use `mcp` package, `FastMCP` or low-level Server
  consistent with current `mcp[cli]`): `health_check` (read-only, reports config
  + which tool categories are enabled) and the notes tools above. Email/calendar/
  chat tools are present as clearly-commented stubs gated by the `{{#IF ...}}`
  blocks so disabled categories don't ship dead tools.
- Tests (`tests/`) use stdlib `unittest`, fakes only, no network, no real creds.
  They must pass in the GENERATED repo via `uv run python -m unittest discover -s tests`.
- `pyproject.toml.tmpl`: name `{{ASSISTANT_SLUG}}`, requires-python >=3.10,
  deps `mcp[cli]` (+ only what the example truly needs). Console scripts:
  `{{ASSISTANT_SLUG}}-mcp = "{{ASSISTANT_SLUG}}.mcp.server:main"`. hatchling build,
  wheel packages = `["{{ASSISTANT_SLUG}}"]`.

## Writing style for ALL generated docs and Omnissiah's own docs

- No em dashes anywhere. Use commas, colons, semicolons, parentheses.
- Direct, concrete, pragmatic. No flattery or hype.
- Generated docs address the friend's principal in the same matter-of-fact tone
  Wintermute's docs use about John.
