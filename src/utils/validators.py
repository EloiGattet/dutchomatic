"""Validators for data models."""

from typing import Any, Dict

from ..models.exercise import Exercise
from ..models.daily import Daily
from ..models.state import State


def validate_exercise(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and return exercise data."""
    exercise = Exercise.from_dict(data)
    return exercise.to_dict()


def validate_daily(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and return daily data."""
    daily = Daily.from_dict(data)
    return daily.to_dict()


def validate_state(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize state data."""
    state = State.from_dict(data)
    return state.to_dict()
