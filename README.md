# Omnissiah

A generator that scaffolds a personalized, bounded MCP assistant repo: a baked-in operating contract plus a runnable MCP server skeleton you can extend.

You answer about eight questions and Omnissiah writes a complete repo for your own assistant: a governance layer (operating contract, assistant profile, host config) and a provider-agnostic MCP server with one real example tool. The generated repo works with Claude Code, Codex, or any MCP host.

## The framing (kept light)

The Omnissiah is the machine-god the Adeptus Mechanicus serves: every machine has a spirit, and you honor it by knowing exactly what it does. That is the whole borrowed idea. An assistant that can act on your email, calendar, and tasks is a machine with a spirit. You do not appease it with vibes. You give it a written contract, a narrow tool surface, and an audit trail, and you understand every line of it. The name is a joke with a point. The point is the rest of this document.

## Where it comes from

Omnissiah is modeled on Wintermute, a private RevOps assistant boundary. Wintermute is one person's hand-written MCP server with a tightly scoped tool surface and a contract that says how the assistant behaves across fresh sessions. Omnissiah takes Wintermute's strengths and strips its private contents so you can stand up your own:

1. A concrete operating contract: modes, a control loop, and a safety/reversibility posture.
2. A scoped, auditable MCP tool boundary instead of ambient authority.
3. The safe-but-permissive balance: capable enough to act, conservative enough to leave tracks.

## Who it is for

Friends who want their own Wintermute. People who already use an MCP host and want an assistant that can do real work (draft email, manage a calendar, drain a capture inbox) without handing it a blank check. You should be comfortable editing Markdown and Python; the generated repo is yours to shape, not a black box.

## What it produces

A new repo named for your assistant, containing:

- `OPERATING-CONTRACT.md`: how the assistant behaves, with the safe-but-permissive defaults baked in and each one explained inline.
- `ASSISTANT-PROFILE.md`, `SYSTEM-MAP.md`, `README.md`: who it serves, what it is, where everything lives.
- `AGENTS.md` and `CLAUDE.md`: host guidance you paste into Claude Code, Codex, or another host.
- A runnable Python MCP server (`<slug>/mcp/server.py`) with `health_check` and a real local notes provider that demonstrates list, read, append, and draft-outbound.
- `pyproject.toml`, `.env.example`, tests, and setup docs for wiring real providers.

The notes provider is intentionally small and real. It shows the boundary in working code: reads list and fetch, one append is an auditable local write, and draft-outbound creates a draft record and never sends. Email, calendar, and chat tools are scaffolded as commented stubs gated on the answers you gave, so disabled categories do not ship dead tools.

## Quickstart

```
git clone <omnissiah repo>
cd omnissiah
uv run omnissiah
```

Answer the questions, then:

```
cd ../<your-assistant-slug>
uv run <your-assistant-slug>-mcp
```

Register it in `~/.claude.json` and you have a working assistant boundary. Full walkthrough, including the non-interactive `--defaults` and `--answers` paths, is in [QUICKSTART.md](QUICKSTART.md).

## Design stance: defaults ON, and explained

Omnissiah ships the safe-but-permissive middle-ground defaults turned on, not off. Most scaffolding tools either hand you raw capability with no posture, or lock everything down so hard the assistant cannot do useful work. Both fail. An assistant that cannot act is a worse notepad; an assistant that acts freely will eventually send the wrong email or delete the wrong file.

The middle ground is a small set of habits: drafts over sends, read a record before you act on it, single calendar events over fragile recurrence, verify high-stakes facts, one capture surface that drains, no destructive operations unless you ask, secrets stay local, scoped tools over ambient authority, move when the next action is clear. These ship enabled and each carries a one-line inline rationale in the generated contract so you can tune them knowingly instead of discovering them by accident.

Omnissiah lets you override surface details (name, role, which tool categories scaffold) but does not give you a switch to silently disable the safety posture. If you want the assistant to send mail directly or run destructive git, you edit the contract by hand. That edit is deliberate, visible in your git history, and yours to own.

For the reasoning behind each default, the failure modes on both sides, and how to tune each one, read [docs/DEFAULTS-RATIONALE.md](docs/DEFAULTS-RATIONALE.md). After you generate, the authoritative behavioral document for your assistant is its own generated `OPERATING-CONTRACT.md`.

## Writing style

No em dashes anywhere, in this repo or in generated output. Direct, concrete, no flattery or hype. The renderer is stdlib-only (no Jinja); plain `{{VAR}}` substitution.
