from pathlib import Path

import pytest
from check_docs import REQUIRED_READMES, check_repo

HEADINGS = "## What it does\n## How it fits\n## Running its tests\n## Main files\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for folder in REQUIRED_READMES:
        readme = tmp_path / folder / "README.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(HEADINGS, encoding="utf-8")
    return tmp_path


def test_missing_readme_is_reported(repo: Path) -> None:
    (repo / "core/README.md").unlink()
    assert check_repo(repo) == ["core/README.md: missing"]


def test_missing_required_heading_is_reported(repo: Path) -> None:
    (repo / "core/README.md").write_text(
        HEADINGS.replace("## Main files\n", ""), encoding="utf-8"
    )
    assert check_repo(repo) == ["core/README.md: missing heading '## Main files'"]


def test_broken_relative_link_is_reported(repo: Path) -> None:
    (repo / "README.md").write_text("[x](nope.md)\n", encoding="utf-8")
    assert check_repo(repo) == ["README.md: broken link nope.md"]


def test_broken_anchor_is_reported(repo: Path) -> None:
    (repo / "README.md").write_text("[x](other.md#absent)\n", encoding="utf-8")
    (repo / "other.md").write_text("# Present\n", encoding="utf-8")
    assert check_repo(repo) == ["README.md: broken link other.md#absent"]


def test_valid_anchor_passes(repo: Path) -> None:
    (repo / "README.md").write_text(
        "[x](other.md#topics-and-messages)\n[local](#same-page)\n## Same page\n",
        encoding="utf-8",
    )
    (repo / "other.md").write_text("## Topics and messages\n", encoding="utf-8")
    assert check_repo(repo) == []


def test_external_links_and_fenced_code_are_ignored(repo: Path) -> None:
    (repo / "README.md").write_text(
        "[external](https://example.com/none)\n"
        "````md\n```\n[x](nope.md)\n```\n````\n"
        "~~~\n[y](also-missing.md)\n~~~\n",
        encoding="utf-8",
    )
    assert check_repo(repo) == []
