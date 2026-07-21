"""
Omnissiah generator CLI.

Stdlib-only (argparse, json, pathlib, re, datetime). Collects ~8 answers
(interactively, from an --answers JSON file, or from the built-in --defaults
profile), derives the assistant slug/tagline and generation date, then renders
the templates/ tree into a personalized assistant repo.

Run:
    uv run omnissiah                       # interactive, writes a repo
    uv run omnissiah --output ../my-asst   # set output dir
    uv run omnissiah --answers answers.json --output <dir>
    uv run omnissiah --defaults --output <dir>   # demo defaults, no prompts
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

from omnissiah.render import render_tree

# Locate templates/ relative to the installed package: the repo root is two
# levels up from this file (omnissiah/cli.py -> omnissiah/ -> repo root).
_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _REPO_ROOT / "templates"

# The canonical demo profile (also the test fixture). Matches the build spec.
DEFAULTS = {
    "assistant_name": "Omnissiah",
    "principal_name": "Magos",
    "principal_role": "a systems operator and builder",
    "principal_domains": "engineering, ops, personal logistics",
    "task_system": "Asana",
    "chat_surface": "Signal",
    "timezone": "America/New_York",
    "tools_email": True,
    "tools_calendar": True,
    "tools_chat": True,
}

# Answer keys that carry boolean tool toggles.
_BOOL_KEYS = ("tools_email", "tools_calendar", "tools_chat")

# Convenience shell aliases. The whole point: the OPERATING-CONTRACT is the
# guardrail, so the assistant is meant to run with host permission prompts off.
# These make that the easy path. Written between guard markers so the block is
# idempotent (re-running updates in place rather than duplicating).
_ALIAS_BEGIN = "# >>> omnissiah aliases >>>"
_ALIAS_END = "# <<< omnissiah aliases <<<"
_ALIAS_BODY = (
    "# Run your MCP host permissionless; the OPERATING-CONTRACT is the guardrail.\n"
    'alias claudex="claude --dangerously-skip-permissions"\n'
    "# Same, plus remote control: names the session after the current directory.\n"
    "alias claudexrc='claude --rc --name \"$(basename \"$(pwd)\")\" "
    '--dangerously-skip-permissions\'\n'
)


def alias_block() -> str:
    """The full guarded alias block, including markers and a trailing newline."""
    return f"{_ALIAS_BEGIN}\n{_ALIAS_BODY}{_ALIAS_END}\n"


def detect_rc_file() -> Path:
    """Pick the shell rc file to receive aliases.

    Honors $SHELL (zsh -> ~/.zshrc, bash -> ~/.bashrc); otherwise falls back to
    the first existing rc file, then ~/.profile.
    """
    shell = os.environ.get("SHELL", "")
    home = Path.home()
    if "zsh" in shell:
        return home / ".zshrc"
    if "bash" in shell:
        return home / ".bashrc"
    for name in (".zshrc", ".bashrc", ".profile"):
        if (home / name).exists():
            return home / name
    return home / ".profile"


def install_aliases(rc_path: Path) -> str:
    """Write or update the guarded alias block in rc_path. Returns a status line.

    Idempotent: if the block already exists it is replaced in place, so running
    the generator repeatedly never duplicates the aliases.
    """
    block = alias_block()
    text = rc_path.read_text(encoding="utf-8") if rc_path.exists() else ""
    if _ALIAS_BEGIN in text and _ALIAS_END in text:
        pattern = re.compile(
            re.escape(_ALIAS_BEGIN) + r".*?" + re.escape(_ALIAS_END) + r"\n?",
            re.DOTALL,
        )
        new_text = pattern.sub(lambda _m: block, text, count=1)
        action = "Updated"
    else:
        prefix = text if text == "" or text.endswith("\n") else text + "\n"
        if prefix:
            prefix += "\n"
        new_text = prefix + block
        action = "Added"
    rc_path.parent.mkdir(parents=True, exist_ok=True)
    rc_path.write_text(new_text, encoding="utf-8")
    return (
        f"{action} omnissiah aliases (claudex, claudexrc) in {rc_path}. "
        f"Run 'source {rc_path}' or open a new shell to use them."
    )

# Answer keys collected from a human or an --answers file (no derived fields).
_ANSWER_KEYS = (
    "assistant_name",
    "principal_name",
    "principal_role",
    "principal_domains",
    "task_system",
    "chat_surface",
    "timezone",
    *_BOOL_KEYS,
)


def slugify(name: str) -> str:
    """Derive a valid Python identifier slug from an assistant name.

    Lowercase, non-alphanumeric runs collapse to a single underscore, leading
    digits and underscores are stripped so the result is import-safe.
    """
    lowered = name.strip().lower()
    # Replace any run of non-alphanumeric characters with a single underscore.
    collapsed = re.sub(r"[^a-z0-9]+", "_", lowered)
    # Strip leading characters that cannot start an identifier (digits, _).
    stripped = re.sub(r"^[0-9_]+", "", collapsed)
    # Strip any trailing underscores left behind.
    return stripped.strip("_")


def _coerce_bool(value) -> bool:
    """Coerce an answers-file or interactive value to a bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "on"}
    return bool(value)


def _ask(prompt: str, default: str) -> str:
    """Prompt for a string answer, returning the default on empty input."""
    suffix = f" [{default}]" if default else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    return raw or default


def _ask_bool(prompt: str, default: bool) -> bool:
    """Prompt for a yes/no answer."""
    hint = "Y/n" if default else "y/N"
    raw = input(f"{prompt} [{hint}]: ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes", "true", "1", "on"}


def collect_interactive() -> dict:
    """Ask the friend the ~8 questions and return raw answers."""
    print("Omnissiah generator: answer a few questions to scaffold your assistant repo.")
    print("Press Enter to accept the bracketed default.\n")
    answers = {
        "assistant_name": _ask("Assistant display name", DEFAULTS["assistant_name"]),
        "principal_name": _ask("Principal name (the human it serves)", DEFAULTS["principal_name"]),
        "principal_role": _ask("Principal role (one line)", DEFAULTS["principal_role"]),
        "principal_domains": _ask(
            "Principal work domains (comma list)", DEFAULTS["principal_domains"]
        ),
        "task_system": _ask("Task system (where commitments live)", DEFAULTS["task_system"]),
        "chat_surface": _ask("Chat surface (or 'none')", DEFAULTS["chat_surface"]),
        "timezone": _ask("Timezone (IANA, e.g. America/New_York)", DEFAULTS["timezone"]),
        "tools_email": _ask_bool("Scaffold email tools?", DEFAULTS["tools_email"]),
        "tools_calendar": _ask_bool("Scaffold calendar tools?", DEFAULTS["tools_calendar"]),
        "tools_chat": _ask_bool("Scaffold chat tools?", DEFAULTS["tools_chat"]),
    }
    return answers


def load_answers_file(path: Path) -> dict:
    """Load and normalize an --answers JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("answers JSON must be an object of key/value pairs")
    # Start from defaults so a partial answers file still produces a valid repo.
    answers = dict(DEFAULTS)
    for key in _ANSWER_KEYS:
        if key in data:
            answers[key] = data[key]
    return answers


def normalize_answers(answers: dict) -> dict:
    """Coerce bool fields and strip strings on a raw answers dict."""
    out = dict(answers)
    for key in _BOOL_KEYS:
        out[key] = _coerce_bool(out.get(key, False))
    for key in _ANSWER_KEYS:
        if key not in _BOOL_KEYS:
            out[key] = str(out.get(key, "")).strip()
    return out


def build_context(answers: dict) -> dict:
    """Turn normalized answers into the full {{VAR}} template context.

    Derives assistant_slug, a default tagline, and stamps the real local date.
    """
    answers = normalize_answers(answers)
    name = answers["assistant_name"]
    slug = slugify(name)
    today = datetime.date.today()
    tagline = f"a bounded personal operating assistant for {answers['principal_name']}"

    return {
        "ASSISTANT_NAME": name,
        "ASSISTANT_SLUG": slug,
        # Uppercase slug: the canonical env-var prefix. common.py reads
        # <SLUG>.upper() + "_VAR_DIR", so docs and .env.example must match it.
        "ASSISTANT_SLUG_UPPER": slug.upper(),
        "ASSISTANT_TAGLINE": tagline,
        "PRINCIPAL_NAME": answers["principal_name"],
        "PRINCIPAL_ROLE": answers["principal_role"],
        "PRINCIPAL_DOMAINS": answers["principal_domains"],
        "TASK_SYSTEM": answers["task_system"],
        "CHAT_SURFACE": answers["chat_surface"],
        "TIMEZONE": answers["timezone"],
        "TOOLS_EMAIL": answers["tools_email"],
        "TOOLS_CALENDAR": answers["tools_calendar"],
        "TOOLS_CHAT": answers["tools_chat"],
        "GEN_DATE": today.isoformat(),
        "GEN_YEAR": str(today.year),
    }


def validate_context(context: dict) -> list[str]:
    """Return a list of validation error strings (empty when valid)."""
    errors: list[str] = []
    slug = context["ASSISTANT_SLUG"]
    if not slug or not slug.isidentifier():
        errors.append(
            f"assistant_slug '{slug}' is not a valid Python identifier "
            "(derive it from a name with letters)"
        )
    if not context["TIMEZONE"]:
        errors.append("timezone must not be empty")
    return errors


def _output_is_nonempty(output_dir: Path) -> bool:
    """Whether the output dir already exists with contents in it."""
    return output_dir.exists() and any(output_dir.iterdir())


def _print_next_steps(output_dir: Path, context: dict) -> None:
    """Print a concrete next-steps summary after a successful write."""
    slug = context["ASSISTANT_SLUG"]
    rel = output_dir
    print("\nDone. Wrote", len(list(output_dir.rglob("*"))), "paths under", str(rel))
    print("\nNext steps:")
    print(f"  cd {rel}")
    print("  git init")
    print("  cp .env.example .env   # then fill in real values")
    print("  uv sync                # install mcp[cli] and the package")
    print(f"  uv run {slug}-mcp      # start the MCP server on stdio")
    print("  uv run python -m unittest discover -s tests   # run the skeleton tests")
    print(
        f"\nRegister the server in ~/.claude.json under mcpServers as "
        f'"{slug}" running: uv run {slug}-mcp'
    )
    print("Then edit OPERATING-CONTRACT.md and ASSISTANT-PROFILE.md to fit your actual setup.")
    print(
        "\nThe OPERATING-CONTRACT is the guardrail, so the assistant is meant to run with\n"
        "host permission prompts off (see OPERATING-CONTRACT.md)."
    )


def parse_args(argv) -> argparse.Namespace:
    """Build and parse the CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="omnissiah",
        description="Generate a personalized bounded-assistant repo from the Omnissiah templates.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output directory for the generated repo (interactive prompt if omitted).",
    )
    parser.add_argument(
        "--answers",
        default=None,
        help="Path to a JSON answers file (non-interactive).",
    )
    parser.add_argument(
        "--defaults",
        action="store_true",
        help="Use the built-in demo defaults, no prompts.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Write into a non-empty output directory.",
    )
    parser.add_argument(
        "--install-aliases",
        action="store_true",
        help="Append the claudex/claudexrc convenience aliases to your shell rc.",
    )
    parser.add_argument(
        "--no-install-aliases",
        action="store_true",
        help="Skip the alias prompt and do not modify your shell rc.",
    )
    parser.add_argument(
        "--rc-file",
        default=None,
        help="Shell rc file to receive aliases (default: autodetect ~/.zshrc or ~/.bashrc).",
    )
    return parser.parse_args(argv)


def _maybe_install_aliases(args) -> None:
    """Install the convenience aliases when asked, or prompt in interactive mode.

    Default is to leave the shell rc untouched: aliases install only when the
    friend opts in (interactively or via --install-aliases). Modifying a shell
    rc is a side effect outside the generated repo, so it is never silent.
    """
    if args.no_install_aliases:
        return
    rc_path = Path(args.rc_file).expanduser() if args.rc_file else detect_rc_file()
    if args.install_aliases:
        should = True
    elif args.defaults or args.answers:
        # Non-interactive run: do not touch the shell rc unless explicitly asked.
        return
    else:
        print()
        should = _ask_bool(
            f"Add convenience shell aliases (claudex / claudexrc) to {rc_path}?",
            False,
        )
    if should:
        try:
            print(install_aliases(rc_path))
        except OSError as e:
            print(f"Could not write aliases to {rc_path}: {e}", file=sys.stderr)


def main(argv=None) -> int:
    """Entry point for the console script."""
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.defaults and args.answers:
        print("Error: use only one of --defaults or --answers.", file=sys.stderr)
        return 2

    if not _TEMPLATES_DIR.is_dir():
        print(
            f"Error: templates directory not found at {_TEMPLATES_DIR}. "
            "Run from a full Omnissiah checkout.",
            file=sys.stderr,
        )
        return 1

    # Gather answers.
    if args.defaults:
        answers = dict(DEFAULTS)
    elif args.answers:
        try:
            answers = load_answers_file(Path(args.answers))
        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(f"Error reading --answers file: {e}", file=sys.stderr)
            return 1
    else:
        answers = collect_interactive()

    context = build_context(answers)

    errors = validate_context(context)
    if errors:
        for err in errors:
            print(f"Error: {err}", file=sys.stderr)
        return 1

    # Resolve output dir.
    output_value = args.output
    if output_value is None:
        if args.defaults or args.answers:
            print("Error: --output is required in non-interactive mode.", file=sys.stderr)
            return 2
        output_value = _ask("Output directory", f"../{context['ASSISTANT_SLUG']}")

    output_dir = Path(output_value).expanduser().resolve()

    if _output_is_nonempty(output_dir) and not args.force:
        print(
            f"Error: output directory {output_dir} is not empty. "
            "Pass --force to write anyway.",
            file=sys.stderr,
        )
        return 1

    written = render_tree(_TEMPLATES_DIR, output_dir, context, context["ASSISTANT_SLUG"])

    print(f"Generated {context['ASSISTANT_NAME']} ({context['ASSISTANT_SLUG']}):")
    for path in written:
        print(f"  {path}")

    _print_next_steps(output_dir, context)
    _maybe_install_aliases(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
