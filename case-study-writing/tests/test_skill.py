#!/usr/bin/env python3
"""Tests for the case-study-writing skill.

Run from the skill directory:
    python3 -m unittest discover tests -v

Stdlib only. The pandoc pipeline test is skipped when pandoc is not installed.
"""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from build_reference_docx import EXTRA_STYLES, build  # noqa: E402

PANDOC_STYLE_IDS = [style_id for style_id, _ in EXTRA_STYLES]


class TestSkillStructure(unittest.TestCase):
    def setUp(self):
        self.skill_md = (SKILL_DIR / "SKILL.md").read_text()

    def test_required_files_exist(self):
        for name in ("SKILL.md", "README.md", "template.md", "style.md",
                      "reference.docx", "scripts/build_reference_docx.py"):
            self.assertTrue((SKILL_DIR / name).exists(), f"missing {name}")

    def test_frontmatter(self):
        match = re.match(r"^---\n(.*?)\n---\n", self.skill_md, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md must start with YAML frontmatter")
        frontmatter = match.group(1)

        name = re.search(r'^name:\s*"?([a-z0-9-]+)"?\s*$', frontmatter, re.MULTILINE)
        self.assertIsNotNone(name, "frontmatter must define a lowercase-hyphen name")
        self.assertEqual(name.group(1), SKILL_DIR.name,
                         "name must match the skill directory name")

        description = re.search(r'^description:\s*"?(.+?)"?\s*$', frontmatter,
                                re.MULTILINE)
        self.assertIsNotNone(description, "frontmatter must define a description")
        self.assertLess(len(description.group(1)), 1024,
                        "description must be under 1024 characters")

    def test_skill_md_under_500_lines(self):
        self.assertLess(len(self.skill_md.splitlines()), 500)

    def test_referenced_files_resolve(self):
        for ref in set(re.findall(r"\]\((?!http)([\w./-]+\.md)\)", self.skill_md)):
            self.assertTrue((SKILL_DIR / ref).exists(),
                            f"SKILL.md references missing file {ref}")
        self.assertIn("reference.docx", self.skill_md)

    def test_no_llm_markup_outside_rule_lines(self):
        # The forbidden characters may only appear on lines naming them as forbidden.
        for path in ("SKILL.md", "style.md"):
            for n, line in enumerate((SKILL_DIR / path).read_text().splitlines(), 1):
                if "\u2014" in line or "\u2192" in line:
                    self.assertTrue(
                        "LLM markup" in line or "em dash" in line,
                        f"{path}:{n} contains forbidden typography: {line!r}",
                    )


class TestBuildReferenceDocx(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    @staticmethod
    def style_ids(docx_path):
        with zipfile.ZipFile(docx_path) as zf:
            styles = zf.read("word/styles.xml").decode("utf-8")
        return re.findall(r'w:styleId="([^"]+)"', styles)

    def test_reference_docx_has_all_pandoc_styles(self):
        ids = set(self.style_ids(SKILL_DIR / "reference.docx"))
        for style_id in PANDOC_STYLE_IDS:
            self.assertIn(style_id, ids)
        for builtin in ("Normal", "Heading1", "Heading2", "Title"):
            self.assertIn(builtin, ids)

    def test_build_is_idempotent(self):
        first = self.tmp / "ref1.docx"
        second = self.tmp / "ref2.docx"
        build(str(SKILL_DIR / "reference.docx"), str(first))
        build(str(first), str(second))
        ids = self.style_ids(second)
        for style_id in PANDOC_STYLE_IDS:
            self.assertEqual(ids.count(style_id), 1,
                             f"{style_id} duplicated on rebuild")

    def test_output_is_valid_zip(self):
        out = self.tmp / "ref.docx"
        build(str(SKILL_DIR / "reference.docx"), str(out))
        with zipfile.ZipFile(out) as zf:
            self.assertIsNone(zf.testzip())
            self.assertIn("word/document.xml", zf.namelist())


@unittest.skipUnless(shutil.which("pandoc"), "pandoc not installed")
class TestPandocPipeline(unittest.TestCase):
    def test_compiled_docx_uses_branded_styles(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            sample = tmp / "sample.md"
            sample.write_text(
                "# Heading\n\n"
                "Body with a [link](https://lincolnloop.com).\n\n"
                "- item one\n- item two\n\n"
                "> A client quote.\n"
            )
            out = tmp / "sample.docx"
            subprocess.run(
                ["pandoc", str(sample),
                 "--reference-doc", str(SKILL_DIR / "reference.docx"),
                 "-o", str(out)],
                check=True, capture_output=True,
            )
            with zipfile.ZipFile(out) as zf:
                document = zf.read("word/document.xml").decode("utf-8")
                styles = zf.read("word/styles.xml").decode("utf-8")
            for style in ("Compact", "BlockText", "Heading1"):
                self.assertIn(f'w:pStyle w:val="{style}"', document)
                self.assertIn(f'w:styleId="{style}"', styles)
            self.assertIn('w:rStyle w:val="Hyperlink"', document)


if __name__ == "__main__":
    unittest.main()
