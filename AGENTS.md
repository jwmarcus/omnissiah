# Omnissiah Project Instructions

This file orients an AI coding assistant opened in this folder. It is about
changing the generator itself. The generated project contract comes from
`templates/AGENTS.md.tmpl`; `templates/CLAUDE.md.tmpl` is its Claude Code
adapter.

## What this project is

Omnissiah is a generator. Someone clones it, runs a CLI, answers a few questions,
and gets a personalized repo for their own bounded MCP assistant: a governance
layer (operating contract, assistant profile, host config) plus a runnable,
provider-agnostic MCP server skeleton. It exists to hand other people the
strengths of a private assistant called Wintermute without its private contents:
a concrete operating contract, a scoped and auditable tool boundary, and a "safe
but permissive" set of defaults.

The full design contract is `docs/dev/BUILD-SPEC.md`. Read it before changing
behavior. It defines the template variables, the output layout, the file
manifest, and the CLI interface.

## Architecture

- `omnissiah/` is the generator's own code (stdlib only, no third-party deps):
  - `omnissiah/render.py`: the rendering engine. Walks `templates/`, evaluates
    conditionals, substitutes tokens, strips `.tmpl`, and renames the `pkg/`
    directory to the assistant slug.
  - `omnissiah/cli.py`: argparse CLI. Interactive prompts, `--answers <json>`,
    `--defaults`, `--output`, `--force`. Derives the slug and stamps the date.
  - `pyproject.toml` (root): console script `omnissiah = "omnissiah.cli:main"`.
- `templates/` is the corpus that gets rendered into a friend's repo. Every file
  ends in `.tmpl`. The `templates/pkg/` tree becomes the generated Python package
  (renamed to the assistant slug). The crown jewel is
  `templates/OPERATING-CONTRACT.md.tmpl`.
- `docs/DEFAULTS-RATIONALE.md` explains why each safe-but-permissive default is
  the recommended middle ground. `docs/dev/BUILD-SPEC.md` is the internal spec.

## Template syntax

- Tokens: `{{VAR}}` (double braces). Variable names are fixed in the spec; do not
  invent new ones without updating the spec, the CLI context, and the rationale.
- Conditionals: `{{#IF VAR}} ... {{/IF}}`, both own-line and inline. They are
  evaluated before token substitution, so `{{ASSISTANT_SLUG}}` inside an `{{#IF}}`
  block renders fine. Wrap whole statements or whole lines so that any on/off
  combination still renders valid Python and clean Markdown.

## How to change things safely

1. State the concrete target. Read `docs/dev/BUILD-SPEC.md` and the file you are
   about to touch.
2. Make the smallest change that advances the target.
3. Always test by actually generating and running the output:
   ```bash
   uv run omnissiah --defaults --output /tmp/omni-check --force
   grep -rn '{{' /tmp/omni-check          # must find nothing: no leaked tokens
   grep -rn '#IF\|/IF' /tmp/omni-check     # must find nothing: conditionals resolved
   uv run --directory /tmp/omni-check python -m compileall -q omnissiah
   uv run --directory /tmp/omni-check python -m unittest discover -s tests
   ```
   Also test with tools disabled (a different answers file) so the `{{#IF}}`
   branches both get exercised.
4. If you change the package code in `templates/pkg/`, the generated tests in
   `templates/tests/` must still pass after rendering.

## Conventions (do not drift)

- No em dashes anywhere. Use commas, colons, semicolons, or parentheses.
- The generator stays stdlib only. No Jinja, no third-party rendering deps.
- The generated MCP skeleton keeps dependencies minimal (`mcp[cli]` and only what
  the example truly needs).
- The "safe but permissive" defaults are the point of this project. Keep them on
  by default, keep their inline rationale, and do not make it easy to silently
  disable the safety posture. If you add a new default, add its entry to
  `docs/DEFAULTS-RATIONALE.md` with its too-restrictive and too-permissive failure
  modes.
- Direct, concrete writing. No flattery or hype in docs or output.

## Adding a new template file

Drop a `.tmpl` file anywhere under `templates/`. The renderer discovers it by
walking the tree; you do not register it anywhere. It renders to the mirrored
path with `.tmpl` stripped (and a leading `pkg/` rewritten to the slug). Special
top-level names: `gitignore.tmpl` becomes `.gitignore`, `env.example.tmpl`
becomes `.env.example`.
