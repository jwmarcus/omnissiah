# Quickstart

From cloning Omnissiah to a running assistant in a few minutes. Omnissiah needs [uv](https://docs.astral.sh/uv/) and Python 3.10 or newer.

## 1. Clone Omnissiah

```
git clone <omnissiah repo>
cd omnissiah
```

## 2. Generate your assistant repo

Interactive (the normal path):

```
uv run omnissiah
```

Omnissiah asks about eight questions:

- Assistant name (display name, for example `Wintermute`). The slug is derived from it: lowercased, non-alphanumeric characters become `_`, repeats collapse. It must be a valid Python identifier, since it names your package and console script.
- Principal name (the human it serves).
- Principal role (one line).
- Principal domains (comma list of work areas).
- Task system (where tasks and commitments live, for example `Asana`).
- Chat surface (a messaging surface, or `none`).
- Timezone (IANA, for example `America/New_York`).
- Which tool categories to scaffold: email, calendar, chat (each true/false).

By default the new repo is written next to Omnissiah. Set the location explicitly with `--output`:

```
uv run omnissiah --output ../my-assistant
```

Omnissiah refuses to write into a non-empty directory unless you pass `--force`.

## 3. Enter the generated repo

```
cd ../<your-assistant-slug>
git init
```

Look at what was generated. The behavioral source of truth is `OPERATING-CONTRACT.md`; `SYSTEM-MAP.md` describes every file in one line.

## 4. Configure the environment

```
cp .env.example .env
```

Edit `.env`. The example provider (local notes) needs no credentials and runs as-is. Real email, calendar, and chat providers are wired per `docs/integrations/SETUP.md`.

## 5. Run the MCP server

```
uv run <your-assistant-slug>-mcp
```

This starts the server on stdio. Then call `health_check`, which is read-only and reports your config plus which tool categories are enabled. Run the tests anytime:

```
uv run python -m unittest discover -s tests
```

## Running posture (permissionless on purpose)

The guardrails for your assistant live in `OPERATING-CONTRACT.md`, not in the host's per-action permission prompts. So the intended way to run it is with prompts disabled, for a low-friction, rolling session. For Claude Code that is `--dangerously-skip-permissions`.

Omnissiah can install two convenience aliases for you. In interactive mode it asks at the end; non-interactively, pass `--install-aliases`:

```
uv run omnissiah --install-aliases          # also works alongside --defaults / --answers
```

That appends an idempotent, clearly-marked block to your shell rc (`~/.zshrc` or `~/.bashrc`, autodetected; override with `--rc-file`):

```sh
alias claudex="claude --dangerously-skip-permissions"
alias claudexrc='claude --rc --name "$(basename "$(pwd)")" --dangerously-skip-permissions'
```

Then `claudex` from inside your assistant repo starts a rolling session, and `claudexrc` also exposes it for remote control. This is only safe because the contract holds: if you weaken it, you are removing the actual guardrail.

## Working files

Your generated repo has a `work/` folder for session scratch space: downloaded inputs, intermediates, drafts in progress. The convention is one folder per job named `YYYY-MM-DD--slug/`. It is allowed to be messy and it is gitignored (except `work/README.md` and the `work/YYYY-MM-DD--example/` placeholder), so job inputs never enter git history. Durable outputs graduate explicitly: a commitment becomes a task, a decision becomes a repo doc, a deliverable goes out by its real channel. See `work/README.md` in the generated repo.

## 6. Register in your MCP host

For Claude Code, add the server to `~/.claude.json`:

```json
{
  "mcpServers": {
    "<your-assistant-slug>": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/<your-assistant-slug>",
        "<your-assistant-slug>-mcp"
      ]
    }
  }
}
```

Use the absolute path to the generated repo. For Codex or another host, point it at the same console script. Restart the host and the tools appear.

## Non-interactive generation

For testing, scripting, or a one-shot setup, skip the prompts.

Wintermute-like demo defaults, no questions asked:

```
uv run omnissiah --defaults --output ../demo-assistant
```

Your own answers from a file:

```
uv run omnissiah --answers answers.json --output ../my-assistant
```

`answers.json` keys are the template variables, lowercased, without braces:

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

`assistant_slug` is derived from `assistant_name`; `assistant_tagline` gets a sensible default; `gen_date` and `gen_year` are stamped from the real local date. Add `--force` to overwrite a non-empty output directory.

## Next

Read `docs/DEFAULTS-RATIONALE.md` in this Omnissiah repo for why each baked-in default is the middle ground and how to tune it. Then read your generated `OPERATING-CONTRACT.md`, since that is the document your assistant actually operates under.
