"""Check required READMEs and local Markdown links."""

import os
import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote, urlsplit

REQUIRED_READMES = (
    "core",
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
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")
# shortcut: Supports inline links, including angle-bracket paths. Add a Markdown
# parser if the repo adopts reference links or nested parentheses in destinations.
LINK = re.compile(r'\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+"[^"]*")?\s*\)')
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
    fence = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        match = FENCE.match(line)
        if fence:
            if match and match[1].startswith(fence) and not match[2].strip():
                fence = ""
        elif match:
            fence = match[1]
        else:
            yield line


def anchors(lines: list[str]) -> set[str]:
    """Collect heading anchors, including suffixes for duplicate headings."""
    found: set[str] = set()
    for line in lines:
        if match := HEADING.match(line):
            slug = re.sub(r"[^\w -]", "", match[2].lower()).replace(" ", "-")
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
                link = match[1] or match[2]
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
