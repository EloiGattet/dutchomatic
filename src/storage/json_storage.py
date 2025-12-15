"""JSON storage implementation for Dutch-o-matic."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .interface import StorageInterface
from ..models.state import State
from ..utils.validators import validate_exercise, validate_daily, validate_state


class JSONStorage(StorageInterface):
    """JSON file-based storage implementation."""

    def __init__(self, data_dir: str = 'data'):
        """Initialize JSON storage with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.exercises_file = self.data_dir / 'exercises.json'
        self.daily_file = self.data_dir / 'daily.json'
        self.courses_file = self.data_dir / 'courses.json'
        self.state_file = self.data_dir / 'state.json'
        
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """Create JSON files if they don't exist."""
        if not self.exercises_file.exists():
            self._write_json(self.exercises_file, [])
        if not self.daily_file.exists():
            self._write_json(self.daily_file, [])
        if not self.courses_file.exists():
            self._write_json(self.courses_file, [])
        if not self.state_file.exists():
            default_state = State.DEFAULT_STATE.copy()
            self._write_json(self.state_file, default_state)

    def _read_json(self, filepath: Path) -> Any:
        """Read JSON file with error handling."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise IOError(f"Error reading {filepath}: {e}")

    def _write_json(self, filepath: Path, data: Any) -> None:
        """Write JSON file atomically."""
        temp_file = filepath.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(filepath)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise IOError(f"Error writing {filepath}: {e}")

    # Exercise methods
    def get_exercise(self, exercise_id: str) -> Optional[Dict[str, Any]]:
        """Get a single exercise by ID."""
        exercises = self._read_json(self.exercises_file)
        for ex in exercises:
            if ex.get('id') == exercise_id:
                return ex
        return None

    def get_all_exercises(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all exercises, optionally filtered."""
        exercises = self._read_json(self.exercises_file)
        if not filters:
            return exercises
        
        filtered = []
        for ex in exercises:
            match = True
            if 'niveau' in filters and ex.get('niveau') != filters['niveau']:
                match = False
            if 'type' in filters and ex.get('type') != filters['type']:
                match = False
            if 'tags' in filters:
                ex_tags = ex.get('tags', [])
                filter_tags = filters['tags']
                if isinstance(filter_tags, str):
                    filter_tags = [filter_tags]
                if not any(tag in ex_tags for tag in filter_tags):
                    match = False
            if match:
                filtered.append(ex)
        return filtered

    def add_exercise(self, exercise: Dict[str, Any]) -> str:
        """Add a new exercise."""
        validated = validate_exercise(exercise)
        exercises = self._read_json(self.exercises_file)
        
        # Check if ID already exists
        if any(ex.get('id') == validated['id'] for ex in exercises):
            raise ValueError(f"Exercise with ID {validated['id']} already exists")
        
        exercises.append(validated)
        self._write_json(self.exercises_file, exercises)
        return validated['id']

    def update_exercise(self, exercise_id: str, exercise: Dict[str, Any]) -> bool:
        """Update an existing exercise."""
        validated = validate_exercise(exercise)
        if validated['id'] != exercise_id:
            raise ValueError("Exercise ID mismatch")
        
        exercises = self._read_json(self.exercises_file)
        for i, ex in enumerate(exercises):
            if ex.get('id') == exercise_id:
                exercises[i] = validated
                self._write_json(self.exercises_file, exercises)
                return True
        return False

    def delete_exercise(self, exercise_id: str) -> bool:
        """Delete an exercise."""
        exercises = self._read_json(self.exercises_file)
        original_len = len(exercises)
        exercises = [ex for ex in exercises if ex.get('id') != exercise_id]
        if len(exercises) < original_len:
            self._write_json(self.exercises_file, exercises)
            return True
        return False

    # Daily methods
    def get_daily(self, daily_id: str) -> Optional[Dict[str, Any]]:
        """Get a single daily item by ID."""
        daily_items = self._read_json(self.daily_file)
        for item in daily_items:
            if item.get('id') == daily_id:
                return item
        return None

    def get_all_daily(self, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all daily items, optionally filtered by kind."""
        daily_items = self._read_json(self.daily_file)
        if kind:
            return [item for item in daily_items if item.get('kind') == kind]
        return daily_items

    def add_daily(self, daily: Dict[str, Any]) -> str:
        """Add a new daily item."""
        validated = validate_daily(daily)
        daily_items = self._read_json(self.daily_file)
        
        # Check if ID already exists
        if any(item.get('id') == validated['id'] for item in daily_items):
            raise ValueError(f"Daily item with ID {validated['id']} already exists")
        
        daily_items.append(validated)
        self._write_json(self.daily_file, daily_items)
        return validated['id']

    def update_daily(self, daily_id: str, daily: Dict[str, Any]) -> bool:
        """Update an existing daily item."""
        validated = validate_daily(daily)
        if validated['id'] != daily_id:
            raise ValueError("Daily ID mismatch")
        
        daily_items = self._read_json(self.daily_file)
        for i, item in enumerate(daily_items):
            if item.get('id') == daily_id:
                daily_items[i] = validated
                self._write_json(self.daily_file, daily_items)
                return True
        return False

    def delete_daily(self, daily_id: str) -> bool:
        """Delete a daily item."""
        daily_items = self._read_json(self.daily_file)
        original_len = len(daily_items)
        daily_items = [item for item in daily_items if item.get('id') != daily_id]
        if len(daily_items) < original_len:
            self._write_json(self.daily_file, daily_items)
            return True
        return False

    # State methods
    def get_state(self) -> Dict[str, Any]:
        """Get the current state."""
        state_data = self._read_json(self.state_file)
        return validate_state(state_data)

    def update_state(self, key: str, value: Any) -> bool:
        """Update a state key."""
        state_data = self.get_state()
        state_data[key] = value
        self._write_json(self.state_file, state_data)
        return True

    def add_history_entry(self, entry: Dict[str, Any]) -> bool:
        """Add an entry to the history."""
        state_data = self.get_state()
        if 'history' not in state_data:
            state_data['history'] = []
        state_data['history'].append(entry)
        self._write_json(self.state_file, state_data)
        return True

    # Course methods
    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get a single course by ID."""
        courses = self._read_json(self.courses_file)
        for course in courses:
            if course.get('id') == course_id:
                return course
        return None

    def get_all_courses(self, course_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all courses, optionally filtered by type."""
        courses = self._read_json(self.courses_file)
        if course_type:
            return [course for course in courses if course.get('type') == course_type]
        return courses

    def add_course(self, course: Dict[str, Any]) -> str:
        """Add a new course."""
        courses = self._read_json(self.courses_file)
        
        # Check if ID already exists
        if any(c.get('id') == course.get('id') for c in courses):
            raise ValueError(f"Course with ID {course.get('id')} already exists")
        
        courses.append(course)
        self._write_json(self.courses_file, courses)
        return course.get('id', '')

    def update_course(self, course_id: str, course: Dict[str, Any]) -> bool:
        """Update an existing course."""
        if course.get('id') != course_id:
            raise ValueError("Course ID mismatch")
        
        courses = self._read_json(self.courses_file)
        for i, c in enumerate(courses):
            if c.get('id') == course_id:
                courses[i] = course
                self._write_json(self.courses_file, courses)
                return True
        return False

    def delete_course(self, course_id: str) -> bool:
        """Delete a course."""
        courses = self._read_json(self.courses_file)
        original_len = len(courses)
        courses = [c for c in courses if c.get('id') != course_id]
        if len(courses) < original_len:
            self._write_json(self.courses_file, courses)
            return True
        return False
