"""Tests for the harness-surface templates and the claude/ path remap."""

import re
import tempfile
import unittest
from pathlib import Path

from omnissiah.cli import DEFAULTS, build_context
from omnissiah.render import output_relpath, render_tree

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _REPO_ROOT / "templates"

# Any surviving {{...}} template marker (token or conditional).
_LEFTOVER_RE = re.compile(r"\{\{.*?\}\}")


class ClaudeSegmentRemapTests(unittest.TestCase):
    def test_claude_dir_maps_to_dot_claude(self):
        self.assertEqual(
            output_relpath(Path("claude/skills/brief/SKILL.md.tmpl"), "omnissiah"),
            Path(".claude/skills/brief/SKILL.md"),
        )

    def test_claude_agents_map_to_dot_claude(self):
        self.assertEqual(
            output_relpath(Path("claude/agents/capture-triage.md.tmpl"), "omnissiah"),
            Path(".claude/agents/capture-triage.md"),
        )

    def test_top_level_file_named_claude_is_not_remapped(self):
        self.assertEqual(output_relpath(Path("claude.tmpl"), "omnissiah"), Path("claude"))

    def test_pkg_rewrite_still_wins(self):
        self.assertEqual(
            output_relpath(Path("pkg/mcp/server.py.tmpl"), "myslug"),
            Path("myslug/mcp/server.py"),
        )


class HarnessTemplateRenderTests(unittest.TestCase):
    """Render the full tree with the demo defaults and inspect the harness files."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name)
        context = build_context(dict(DEFAULTS))
        render_tree(_TEMPLATES_DIR, cls.out, context, context["ASSISTANT_SLUG"])

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _read(self, rel: str) -> str:
        path = self.out / rel
        self.assertTrue(path.is_file(), f"expected generated file at {rel}")
        return path.read_text(encoding="utf-8")

    def test_harness_files_are_generated(self):
        for rel in (
            ".claude/skills/brief/SKILL.md",
            ".claude/skills/drain/SKILL.md",
            ".claude/agents/capture-triage.md",
            "docs/harness-capabilities.md",
        ):
            with self.subTest(rel=rel):
                self._read(rel)

    def test_no_leftover_template_markers(self):
        for rel in (
            ".claude/skills/brief/SKILL.md",
            ".claude/skills/drain/SKILL.md",
            ".claude/agents/capture-triage.md",
            "docs/harness-capabilities.md",
            "OPERATING-CONTRACT.md",
            "AGENTS.md",
            "CLAUDE.md",
        ):
            with self.subTest(rel=rel):
                self.assertIsNone(_LEFTOVER_RE.search(self._read(rel)))

    def test_claude_file_is_agents_adapter(self):
        text = self._read("CLAUDE.md")
        self.assertIn("@AGENTS.md", text)
        self.assertLessEqual(len(text.splitlines()), 10)

        agents = self._read("AGENTS.md")
        self.assertIn("Read `OPERATING-CONTRACT.md`", agents)

    def test_triage_agent_tools_are_scoped_to_notes_reads(self):
        text = self._read(".claude/agents/capture-triage.md")
        self.assertIn(
            "tools: mcp__omnissiah__notes_list, mcp__omnissiah__notes_read", text
        )
        # Least privilege: no mutation tools in the frontmatter tool list.
        tools_line = next(
            line for line in text.splitlines() if line.startswith("tools:")
        )
        self.assertNotIn("notes_append", tools_line)
        self.assertNotIn("notes_draft_outbound", tools_line)

    def test_contract_gains_harness_capabilities_section(self):
        text = self._read("OPERATING-CONTRACT.md")
        self.assertIn("## Harness Capabilities", text)
        self.assertIn("docs/harness-capabilities.md", text)

    def test_brief_skill_honors_tool_toggles(self):
        # Defaults enable calendar and email, so both gated surfaces render.
        text = self._read(".claude/skills/brief/SKILL.md")
        self.assertIn("**Calendar**", text)
        self.assertIn("inbox", text)
        # The judgment-first format always leads with the ranked section.
        self.assertIn("**Needs Magos**", text)
        self.assertIn("Verify before asserting", text)

    def test_brief_skill_drops_gated_sections_when_tools_off(self):
        context = build_context(
            dict(DEFAULTS, tools_email=False, tools_calendar=False)
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            render_tree(_TEMPLATES_DIR, out, context, context["ASSISTANT_SLUG"])
            text = (out / ".claude/skills/brief/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("**Calendar**", text)
        self.assertNotIn("inbox", text)
        self.assertNotIn("quoted sent mail", text)
        # The ungated spine survives the toggles.
        self.assertIn("**Needs Magos**", text)
        self.assertIsNone(_LEFTOVER_RE.search(text))


if __name__ == "__main__":
    unittest.main()
