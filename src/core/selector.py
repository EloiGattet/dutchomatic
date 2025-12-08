"""Exercise selection logic."""

import random
from typing import Dict, List, Optional

from ..storage import StorageInterface


NIVEAU_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']


def _niveau_to_index(niveau: str) -> int:
    """Convert niveau to numeric index for comparison."""
    try:
        return NIVEAU_ORDER.index(niveau)
    except ValueError:
        return 0


def _filter_by_niveau(exercises: List[Dict], max_niveau: str) -> List[Dict]:
    """Filter exercises by niveau (≤ max_niveau)."""
    max_idx = _niveau_to_index(max_niveau)
    return [
        ex for ex in exercises
        if _niveau_to_index(ex.get('niveau', 'A1')) <= max_idx
    ]


def _get_recent_exercise_ids(storage: StorageInterface, limit: int = 10) -> set:
    """Get IDs of recently printed exercises."""
    state = storage.get_state()
    history = state.get('history', [])
    recent = [h for h in history if not h.get('with_answers', False)]
    recent_ids = [h.get('exercise_id') for h in recent[-limit:] if h.get('exercise_id')]
    return set(recent_ids)


def select_exercise(
    storage: StorageInterface,
    niveau_actuel: str,
    policy: str = "strict",
    mix_ratio: float = 0.7,
    exclude_recent: bool = False
) -> Optional[Dict]:
    """Select an exercise based on policy.
    
    Args:
        storage: Storage interface
        niveau_actuel: Current level (A1, A2, etc.)
        policy: "strict" (≤ niveau) or "mix" (70% current, 30% below)
        mix_ratio: Ratio for mix policy (default 0.7 = 70% current level)
        exclude_recent: If True, exclude recently printed exercises
    
    Returns:
        Selected exercise dict or None if none available
    """
    all_exercises = storage.get_all_exercises()
    
    if not all_exercises:
        return None
    
    # Filter by niveau based on policy
    if policy == "strict":
        candidates = _filter_by_niveau(all_exercises, niveau_actuel)
    elif policy == "mix":
        current_level = [ex for ex in all_exercises if ex.get('niveau') == niveau_actuel]
        below_level = _filter_by_niveau(all_exercises, niveau_actuel)
        below_level = [ex for ex in below_level if ex.get('niveau') != niveau_actuel]
        
        if random.random() < mix_ratio:
            candidates = current_level if current_level else below_level
        else:
            candidates = below_level if below_level else current_level
    else:
        raise ValueError(f"Unknown policy: {policy}")
    
    if not candidates:
        return None
    
    # Exclude recent if requested
    if exclude_recent:
        recent_ids = _get_recent_exercise_ids(storage)
        candidates = [ex for ex in candidates if ex.get('id') not in recent_ids]
        if not candidates:
            # Fallback: allow recent if no other options
            candidates = _filter_by_niveau(all_exercises, niveau_actuel)
    
    # Weight by type diversity (simple: random selection)
    # Could be enhanced with type tracking
    return random.choice(candidates)
