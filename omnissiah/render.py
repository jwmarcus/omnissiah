"""
Omnissiah rendering engine.

Stdlib-only. Walks the templates/ tree, substitutes {{VAR}} tokens, evaluates
line-delimited {{#IF VAR}}...{{/IF}} conditional blocks, strips the .tmpl
suffix, rewrites a leading 'pkg/' path segment to the assistant slug, and maps
a few top-level template names to dotfile output names.

The renderer never hardcodes the file manifest: any .tmpl file added under
templates/ is rendered and written to its mirrored output path. This keeps the
generator and the templates loosely coupled.
"""

import re
from pathlib import Path

# {{VAR}} token, e.g. {{ASSISTANT_NAME}}. Names are UPPER_SNAKE.
_TOKEN_RE = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")

# {{#IF VAR}} and {{/IF}} block markers. They may sit alone on their own line
# OR be embedded inline within a line of prose. A single matcher finds both the
# open and close forms anywhere in the text; the evaluator below walks them in
# order, honoring nesting.
_IF_MARKER_RE = re.compile(r"\{\{#IF\s+([A-Z0-9_]+)\s*\}\}|\{\{/IF\s*\}\}")

# An {{#IF}} or {{/IF}} marker that occupies a whole line by itself (optionally
# with surrounding whitespace). When a marker is alone on its line we also
# consume the line's trailing newline so dropping/keeping it leaves no blank
# line behind.
_IF_OWNLINE_RE = re.compile(
    r"(?m)^[ \t]*(?:\{\{#IF\s+[A-Z0-9_]+\s*\}\}|\{\{/IF\s*\}\})[ \t]*\n"
)

# Top-level template names that map to dotfiles or otherwise renamed outputs.
# Keyed by the template path relative to templates/, with the .tmpl suffix
# already stripped.
_NAME_MAP = {
    "gitignore": ".gitignore",
    "env.example": ".env.example",
}

# Values that count as false for {{#IF}} evaluation. Everything else that is
# non-empty is truthy. Booleans are handled directly.
_FALSE_STRINGS = {"", "false", "0", "no", "off", "none"}


def is_truthy(value) -> bool:
    """Return whether a context value should enable an {{#IF}} block.

    True when the value is boolean True, or a non-empty string that is not one
    of the recognized false words (false/0/no/off/none, case-insensitive).
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in _FALSE_STRINGS
    # Numbers, lists, etc: fall back to Python truthiness.
    return bool(value)


def substitute_tokens(text: str, context: dict) -> str:
    """Replace every {{VAR}} token with its context value (as a string).

    Unknown tokens are left untouched so a missing variable is visible in the
    output rather than silently blanked.
    """

    def repl(match: "re.Match") -> str:
        name = match.group(1)
        if name not in context:
            return match.group(0)
        value = context[name]
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    return _TOKEN_RE.sub(repl, text)


def _strip_ownline_marker_newlines(text: str) -> str:
    """Tag own-line {{#IF}}/{{/IF}} markers so their trailing newline is dropped.

    When a marker is the only non-whitespace content on its line, the friend
    expects the whole line (including its newline) to disappear, leaving no
    blank gap. We rewrite the line down to just the bare marker(s) by removing
    the leading indentation and the trailing whitespace + newline. The
    surviving bare markers are then handled uniformly by evaluate_conditionals.
    """
    return _IF_OWNLINE_RE.sub(
        lambda m: m.group(0).strip(" \t").rstrip("\n").strip(" \t"), text
    )


def evaluate_conditionals(text: str, context: dict) -> str:
    """Evaluate {{#IF VAR}}...{{/IF}} conditional blocks.

    Markers may stand alone on their own line OR be embedded inline within a
    line of prose; both forms are honored, and blocks may nest. When VAR is
    truthy the inner content is kept (the markers themselves removed); when
    falsy the whole span including its markers is dropped.

    Own-line markers also consume their line's trailing newline so a dropped or
    kept block does not leave a blank line behind.
    """
    # First collapse own-line markers so they no longer carry a trailing
    # newline of their own; after this every marker is just the bare token.
    text = _strip_ownline_marker_newlines(text)

    out: list[str] = []
    # Stack of bools: whether the enclosing blocks are all currently emitting.
    keep_stack: list[bool] = []
    pos = 0

    for match in _IF_MARKER_RE.finditer(text):
        # Emit the literal text since the previous marker, but only when every
        # enclosing block is currently keeping.
        if all(keep_stack):
            out.append(text[pos:match.start()])
        pos = match.end()

        var = match.group(1)
        if var is not None:  # {{#IF VAR}}
            parent_keeps = all(keep_stack) if keep_stack else True
            keep_stack.append(parent_keeps and is_truthy(context.get(var)))
        else:  # {{/IF}}
            if keep_stack:
                keep_stack.pop()

    if all(keep_stack):
        out.append(text[pos:])

    return "".join(out)


def render_text(text: str, context: dict) -> str:
    """Render a single template string: conditionals first, then tokens."""
    text = evaluate_conditionals(text, context)
    text = substitute_tokens(text, context)
    return text


def output_relpath(template_relpath: Path, slug: str) -> Path:
    """Map a template path (relative to templates/) to its output path.

    - Strips a trailing .tmpl suffix.
    - Rewrites a leading 'pkg/' path segment to the assistant slug.
    - Maps top-level dotfile names (gitignore -> .gitignore, etc).
    """
    parts = list(template_relpath.parts)
    if not parts:
        raise ValueError("empty template path")

    # Strip .tmpl from the final segment.
    last = parts[-1]
    if last.endswith(".tmpl"):
        last = last[: -len(".tmpl")]
    parts[-1] = last

    # Rewrite a leading pkg/ segment to the slug.
    if parts[0] == "pkg":
        parts[0] = slug

    # Top-level dotfile remap: only when the path is a single top-level file.
    if len(parts) == 1 and parts[0] in _NAME_MAP:
        parts[0] = _NAME_MAP[parts[0]]

    return Path(*parts)


def iter_templates(templates_dir: Path):
    """Yield (template_path, relative_path) for every .tmpl file under the tree.

    template_path is absolute; relative_path is relative to templates_dir.
    """
    for path in sorted(templates_dir.rglob("*.tmpl")):
        if path.is_file():
            yield path, path.relative_to(templates_dir)


def render_tree(templates_dir: Path, output_dir: Path, context: dict, slug: str) -> list[Path]:
    """Render every template under templates_dir into output_dir.

    Returns the list of absolute output paths written, in write order.
    """
    written: list[Path] = []
    for template_path, relpath in iter_templates(templates_dir):
        rendered = render_text(template_path.read_text(encoding="utf-8"), context)
        out_rel = output_relpath(relpath, slug)
        out_path = output_dir / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        written.append(out_path)
    return written
