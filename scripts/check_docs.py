"""Check required READMEs and local Markdown links."""

import os
import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

REQUIRED_READMES = (
    "core",
    "core/src/gridbot_core/metrics",
    "core/src/gridbot_core/scenario",
    "core/src/gridbot_core/sensors",
    "core/src/gridbot_core/sim",
    "core/src/gridbot_core/world",
    "runner",
    "gateway",
    "ui",
    "e2e",
    "ros",
    "ros/src/gridbot_msgs",
    "ros/src/gridbot_sim",
    "ros/src/gridbot_nodes",
    "ros/src/gridbot_bringup",
    "config",
    "assets",
    "scenarios",
    "docker",
    "deploy",
    "scripts",
    "docs",
    ".github/workflows",
)
HEADINGS = ("What it does", "How it fits", "Running its tests", "Main files")
SKIP_DIRS = {
    ".git",
    ".superpowers",
    ".venv",
    "node_modules",
    "dist",
    "artifacts",
    "build",
    "install",
    "log",
}
HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")
# shortcut: Checks inline links. Use parser tokens if we need reference links
# or nested parentheses in destinations.
LINK = re.compile(
    r"\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<plain>[^\s)]+))"
    r'(?:\s+"[^"]*")?\s*\)'
)
HEADING_LINK = re.compile(r"\[(?P<label>[^\[\]]*)" + LINK.pattern)
INLINE_CODE = re.compile(r"(`+).*?\1")


def markdown_files(root: Path) -> Iterator[Path]:
    """Yield Markdown paths, pruning generated directories."""
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(set(dirs) - SKIP_DIRS)
        yield from (
            Path(folder) / name for name in sorted(files) if name.endswith(".md")
        )


def content_lines(path: Path) -> Iterator[str]:
    """Yield Markdown lines outside fenced code blocks."""
    text = path.read_text(encoding="utf-8")
    fenced_lines = {
        number
        for token in MarkdownIt().parse(text)
        if token.type == "fence" and token.map is not None
        for number in range(token.map[0], token.map[1])
    }
    for number, line in enumerate(text.split("\n")):
        if number not in fenced_lines:
            yield line


def anchors(lines: list[str]) -> set[str]:
    """Collect heading anchors, including suffixes for duplicate headings."""
    found: set[str] = set()
    for line in lines:
        if match := HEADING.match(line):
            heading = HEADING_LINK.sub(r"\g<label>", match[2])
            slug = re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
            unique = slug
            suffix = 1
            while unique in found:
                unique = f"{slug}-{suffix}"
                suffix += 1
            found.add(unique)
    return found


def check_repo(root: Path) -> list[str]:
    """Return path-relative descriptions of Markdown problems under root."""
    root = root.resolve()
    documents = {path: list(content_lines(path)) for path in markdown_files(root)}
    slugs = {path: anchors(lines) for path, lines in documents.items()}
    problems: list[str] = []
    for folder in REQUIRED_READMES:
        path = root / folder / "README.md"
        relative = path.relative_to(root).as_posix()
        if path not in documents:
            problems.append(f"{relative}: missing")
            continue
        sections = {line.strip() for line in documents[path]}
        for heading in HEADINGS:
            if f"## {heading}" not in sections:
                problems.append(f"{relative}: missing heading '## {heading}'")

    for path, lines in documents.items():
        for line in lines:
            for match in LINK.finditer(INLINE_CODE.sub("", line)):
                link = match["angle"] or match["plain"]
                url = urlsplit(link)
                if url.scheme or url.netloc:
                    continue
                base = root if url.path.startswith("/") else path.parent
                target = (
                    (base / unquote(url.path).lstrip("/")).resolve()
                    if url.path
                    else path
                )
                if (
                    not target.is_relative_to(root)
                    or not target.exists()
                    or (
                        url.fragment
                        and unquote(url.fragment) not in slugs.get(target, set())
                    )
                ):
                    problems.append(f"{path.relative_to(root)}: broken link {link}")
    return problems


def main() -> int:
    """Print documentation problems and return the check's exit status."""
    problems = check_repo(Path(__file__).resolve().parents[1])
    for problem in problems:
        print(problem)
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
