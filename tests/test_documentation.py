import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


class _SiteReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(str(values["id"]))
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.references.append(str(values[attribute]))


class DocumentationIntegrityTests(unittest.TestCase):
    def test_markdown_relative_links_resolve(self) -> None:
        public_markdown = [ROOT / "README.md", ROOT / "CHANGELOG.md"]
        for directory in ("docs", "results", "unity"):
            public_markdown.extend((ROOT / directory).rglob("*.md"))

        missing: list[str] = []
        for document in public_markdown:
            text = document.read_text(encoding="utf-8")
            for raw_target in MARKDOWN_LINK.findall(text):
                target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith(("#", "mailto:")):
                    continue
                path = unquote(parsed.path)
                if path and not (document.parent / path).resolve().exists():
                    missing.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [], "Broken Markdown links:\n" + "\n".join(missing))

    def test_site_local_assets_and_fragments_resolve(self) -> None:
        index = ROOT / "docs" / "index.html"
        parser = _SiteReferenceParser()
        parser.feed(index.read_text(encoding="utf-8"))
        missing: list[str] = []
        for reference in parser.references:
            parsed = urlsplit(reference)
            if parsed.scheme or reference.startswith(("mailto:", "javascript:")):
                continue
            if parsed.path:
                target = (index.parent / unquote(parsed.path)).resolve()
                if not target.exists():
                    missing.append(reference)
            elif parsed.fragment and parsed.fragment not in parser.ids:
                missing.append(reference)
        self.assertEqual(missing, [], "Broken site references: " + ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
