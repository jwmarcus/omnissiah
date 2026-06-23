"""
Omnissiah: a generator for bounded personal-assistant repos.

A friend clones this, runs `uv run omnissiah`, answers a few questions, and gets
a personalized "personal operating system" repo: a parameterized governance
layer plus a runnable, provider-agnostic MCP server skeleton with one real
example tool to extend.

Public surface:
    omnissiah.cli.main      console-script entry point
    omnissiah.render        the stdlib-only template rendering engine
"""

__version__ = "0.1.0"
