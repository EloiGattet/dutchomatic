"""Course selection logic."""

import random
from typing import Dict, Optional

from ..storage import StorageInterface


def select_course(storage: StorageInterface, course_type: Optional[str] = None) -> Optional[Dict]:
    """Select a random course.
    
    Args:
        storage: Storage interface
        course_type: Optional course type filter (vocabulary, conjugation, conversation, grammar)
    
    Returns:
        Selected course dict or None if none available
    """
    all_courses = storage.get_all_courses(course_type=course_type)
    
    if not all_courses:
        return None
    
    return random.choice(all_courses)

