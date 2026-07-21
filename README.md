# Omnissiah

Generate your own bounded MCP assistant. Answer about eight questions and Omnissiah writes a complete repo for a personal assistant you control: a baked-in operating contract plus a runnable MCP server skeleton you can extend. The generated repo works with Claude Code, Codex, or any MCP host.

It exists because an assistant that can act on your email, calendar, and tasks is powerful and easy to get wrong. Most setups give you raw capability with no posture, or lock things down so hard the assistant cannot do useful work. Omnissiah ships the middle ground: capable enough to act, conservative enough to leave tracks, with every safety default turned on and explained.

## Requirements

- [uv](https://docs.astral.sh/uv/) (handles Python and dependencies)
- Python 3.10 or newer
- An MCP host to run the result (Claude Code, Codex, or similar). Optional for generating; required for using the assistant.

## 30-second example

```
git clone https://github.com/jwmarcus/omnissiah
cd omnissiah
uv run omnissiah
```

Omnissiah asks about eight questions (every prompt has a default, so you can press Enter through them):

```
Omnissiah generator: answer a few questions to scaffold your assistant repo.
Assistant display name [Omnissiah]: Jarvis
Principal name (the human it serves) [Magos]: Tony
Principal role (one line) [a systems operator and builder]: an engineer and founder
Principal work domains (comma list) [engineering, ops, personal logistics]: product, hardware, personal
Task system (where commitments live) [Asana]: Linear
Chat surface (or 'none') [Signal]: none
Timezone (IANA, e.g. America/New_York) [America/New_York]: America/Los_Angeles
Scaffold email tools? [Y/n]: y
Scaffold calendar tools? [Y/n]: y
Scaffold chat tools? [Y/n]: n
```

It writes a repo and tells you exactly what to do next:

```
Done. Wrote 33 paths under ../jarvis

Next steps:
  cd ../jarvis
  git init
  cp .env.example .env   # then fill in real values
  uv sync                # install mcp[cli] and the package
  uv run jarvis-mcp      # start the MCP server on stdio
  uv run python -m unittest discover -s tests   # run the skeleton tests
```

The assistant name becomes your Python package and console script (`jarvis-mcp`), derived as a valid identifier. The example notes provider runs with no credentials, so `uv run jarvis-mcp` works immediately, before you wire up anything real.

## What you get

A new repo named for your assistant. With the answers above it looks like this:

```
jarvis/
  OPERATING-CONTRACT.md          # how the assistant behaves (the source of truth)
  ASSISTANT-PROFILE.md           # who it serves and what it is
  SYSTEM-MAP.md                  # one line per file in the repo
  README.md                      # the generated repo's own readme
  AGENTS.md                      # canonical coding-assistant instructions
  CLAUDE.md                      # Claude Code adapter to AGENTS.md
  pyproject.toml                 # console script: jarvis-mcp
  .env.example                   # documented placeholders, no real secrets
  .gitignore                     # excludes .env, var/, secrets/, caches
  jarvis/
    mcp/
      server.py                  # the MCP server: health_check + the notes tools
    integrations/
      common.py                  # env loading and local paths
      providers/
        base.py                  # provider-agnostic interfaces (the shape to implement)
        notes.py                 # the runnable example provider (local JSON file)
  docs/
    integrations/SETUP.md        # how to wire real email/calendar/chat providers
    playbooks/README.md          # opt-in domain playbook loading rules
  work/
    README.md                    # the workbench convention (one folder per job)
    YYYY-MM-DD--example/         # placeholder showing the YYYY-MM-DD--slug format
  tests/
    test_server_tools.py         # stdlib unittest, no network, no credentials
    test_providers.py
```

The `work/` folder is the assistant's scratch space: one folder per job named `YYYY-MM-DD--slug/` for inputs, intermediates, and drafts in progress. It is allowed to be messy and is gitignored (except the README and the example placeholder), so job inputs never enter git history. Durable outputs graduate explicitly to a task, a repo doc, or their real channel. It is a more structured version of an ad-hoc working directory.

### The example tool surface

The generated server registers five working tools out of the box:

| Tool | What it does | What it demonstrates |
|---|---|---|
| `health_check` | Reports config and which tool categories are enabled. Read-only. | Safe introspection |
| `notes_list` | List stored notes. | Read |
| `notes_read` | Fetch one note by id. | Read (list, then read) |
| `notes_append` | Append a note to a local JSON file. | An auditable local write |
| `notes_draft_outbound` | Create a draft outbound record. Never sends. | Drafts over sends |

The notes provider is small and real on purpose: it shows the safe-but-permissive boundary in working code you can read in a minute. Email, calendar, and chat tools are scaffolded as commented stubs gated on the answers you gave. A category you turn off ships no live tool, no enabled-category wiring, and no environment variable; all that remains is a one-line note on how to add it later. Choosing `chat: no` above leaves the generated server with exactly the five notes-and-health tools and no chat surface.

### What the contract looks like

The behavioral source of truth is the generated `OPERATING-CONTRACT.md`. Every safe-but-permissive default is baked in and carries a one-line inline rationale, so you meet each one in context and can tune it knowingly:

```markdown
## Safety And Reversibility

- Do not run destructive filesystem or git commands unless Tony explicitly asks
  for that operation. (Why: a backup is a recovery path, not a license to delete.)
- Prefer drafts, previews, and reviewable artifacts for anything that leaves the
  local machine. (Why: outbound actions are the ones you cannot take back.)
- Verify high-stakes input (dates, money, health, legal, external-system state,
  current facts) against a source before acting on it. (Why: these are exactly
  the inputs where being wrong is expensive.)
```

The contract is filled in with your principal's name, role, domains, task system, and timezone throughout.

## Register it in your MCP host

After generating, point your host at the console script. For Claude Code, add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "jarvis": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/jarvis", "jarvis-mcp"]
    }
  }
}
```

Restart the host and the tools appear. Open the generated repository so the
host loads `AGENTS.md`, then read `OPERATING-CONTRACT.md` as directed there.

## Running posture: permissionless on purpose

The guardrails live in the `OPERATING-CONTRACT.md`, not in the host's per-action permission prompts. That is the design: a written contract you can audit, instead of a confirmation dialog you click through. So the intended way to run your assistant is with prompts disabled, for a low-friction, rolling session. For Claude Code that is `--dangerously-skip-permissions`.

Omnissiah can install two convenience aliases for this. It offers during interactive generation, or run `uv run omnissiah --install-aliases` (works alongside `--defaults` and `--answers`). The block it appends to your shell rc is idempotent and clearly marked:

```sh
alias claudex="claude --dangerously-skip-permissions"
alias claudexrc='claude --rc --name "$(basename "$(pwd)")" --dangerously-skip-permissions'
```

`claudex` from inside your assistant repo starts a rolling session; `claudexrc` also exposes it for remote control. This is only safe because the contract holds. If you weaken the contract (allow direct sends, allow destructive git), you are removing the actual guardrail, so make that edit deliberately and keep it in git history.

## Non-interactive generation

Skip the prompts for testing, scripting, or a one-shot setup.

```
uv run omnissiah --defaults --output ../demo-assistant    # built-in demo defaults
uv run omnissiah --answers answers.json --output ../my-assistant
```

`answers.json` keys are the template variables, lowercased, without braces:

```json
{
  "assistant_name": "Jarvis",
  "principal_name": "Tony",
  "principal_role": "an engineer and founder",
  "principal_domains": "product, hardware, personal",
  "task_system": "Linear",
  "chat_surface": "none",
  "timezone": "America/Los_Angeles",
  "tools_email": true,
  "tools_calendar": true,
  "tools_chat": false
}
```

`assistant_slug` is derived from `assistant_name`; the date is stamped from your machine. Omnissiah refuses to write into a non-empty directory unless you pass `--force`. The full walkthrough is in [QUICKSTART.md](QUICKSTART.md).

## Design stance: defaults ON, and explained

Omnissiah ships the middle-ground defaults turned on, not off. An assistant that cannot act is a worse notepad; an assistant that acts freely will eventually send the wrong email or delete the wrong file. The balance is a small set of habits:

- Drafts over sends; the human sends.
- Read a record before you act on it.
- Single calendar events over fragile recurrence for short protocols.
- Verify high-stakes facts (dates, money, health, legal, external state).
- One capture surface that drains, not a pile of inboxes.
- No destructive filesystem or git operations unless you ask.
- Secrets stay local, never in commits or chat.
- Scoped MCP tools over broad ambient authority.
- Move when the next action is clear; ask one sharp question when it is not.
- Concrete reporting, no flattery standing in for a status.
- Commitments and durable decisions outlive the chat.

You can override surface details (name, role, which tool categories scaffold), but there is no switch that silently disables the safety posture. If you want the assistant to send mail directly or run destructive git, you edit the contract by hand. That edit is deliberate, visible in your git history, and yours to own.

Each default's reasoning, the failure modes on both sides, and how to tune it are in [docs/DEFAULTS-RATIONALE.md](docs/DEFAULTS-RATIONALE.md).

## Where it comes from

Omnissiah is modeled on Wintermute, a private personal-assistant boundary: one person's hand-written MCP server with a tightly scoped tool surface and a contract that says how the assistant behaves across fresh sessions. Omnissiah takes those strengths (a concrete operating contract, a scoped and auditable tool boundary, the safe-but-permissive balance) and strips the private contents so you can stand up your own.

The name is borrowed from the machine-god of the Adeptus Mechanicus, who is honored by knowing exactly what each machine does. That is the whole idea: an assistant that can act is a machine with a spirit, and you do not appease it with vibes. You give it a written contract, a narrow tool surface, and an audit trail, and you understand every line.

## How it works under the hood

The renderer is stdlib-only (no Jinja). Templates live in `templates/` and use plain `{{VAR}}` substitution plus line and inline `{{#IF TOOLS_*}} ... {{/IF}}` conditionals. The engine walks the template tree, so adding a `.tmpl` file is all it takes to add a generated file. If you want to change the generator itself, open this folder in Claude Code or Codex; `AGENTS.md` here orients you, and `docs/dev/BUILD-SPEC.md` is the internal contract.

## Conventions

No em dashes anywhere, in this repo or in generated output. Direct, concrete writing, no flattery or hype.

## License

MIT. See [LICENSE](LICENSE).
