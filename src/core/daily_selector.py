"""Daily item selection logic."""

import random
from typing import Dict, Optional

from ..storage import StorageInterface


def select_daily(storage: StorageInterface) -> Optional[Dict]:
    """Select a random daily item (expression, fact, or quote).
    
    Args:
        storage: Storage interface
    
    Returns:
        Selected daily dict or None if none available
    """
    all_daily = storage.get_all_daily()
    
    if not all_daily:
        return None
    
    return random.choice(all_daily)
