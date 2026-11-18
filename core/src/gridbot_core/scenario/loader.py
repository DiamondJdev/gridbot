"""Load scenario and rig files, reporting problems by file and field."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from gridbot_core.scenario.models import Scenario
from gridbot_core.sensors.rig import Rig


class ScenarioError(ValueError):
    """A scenario or rig file could not be read or failed validation."""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ScenarioError(f"{path}: cannot read file: {error}") from error


def _validation_error(path: Path, error: ValidationError) -> ScenarioError:
    problems: list[str] = []
    for item in error.errors(include_url=False, include_input=False):
        field = ".".join(str(part) for part in item["loc"])
        problems.append(f"{field}: {item['msg']}" if field else item["msg"])
    return ScenarioError(f"{path}: {'; '.join(problems)}")


def load_scenario(path: Path) -> Scenario:
    """Load a scenario JSON file or raise ``ScenarioError``."""
    text = _read_text(path)
    try:
        return Scenario.model_validate_json(text)
    except ValidationError as error:
        raise _validation_error(path, error) from error


def load_rig(path: Path) -> Rig:
    """Load a sensor rig YAML file or raise ``ScenarioError``."""
    text = _read_text(path)
    try:
        return Rig.model_validate(yaml.safe_load(text))
    except yaml.YAMLError as error:
        raise ScenarioError(f"{path}: invalid YAML: {error}") from error
    except ValidationError as error:
        raise _validation_error(path, error) from error
