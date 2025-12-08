"""Formatting functions for exercises and answers."""

from typing import Dict, Optional


TICKET_WIDTH = 58


def _center_text(text: str, width: int) -> str:
    """Center text within width, truncate if too long."""
    text = text.strip()
    if len(text) > width:
        text = text[:width - 3] + '...'
    padding = (width - len(text)) // 2
    return ' ' * padding + text + ' ' * (width - len(text) - padding)


def _format_box(title: str, width: int = TICKET_WIDTH) -> str:
    """Format a boxed title."""
    inner_width = width - 2
    top = '╔' + '═' * inner_width + '╗'
    centered = _center_text(title, inner_width)
    title_line = '║' + centered + '║'
    bottom = '╚' + '═' * inner_width + '╝'
    return f"{top}\n{title_line}\n{bottom}"


def format_exercise(exercise: Dict, daily: Optional[Dict] = None) -> str:
    """Format exercise for printing.
    
    Args:
        exercise: Exercise dict
        daily: Optional daily item dict
    
    Returns:
        Formatted ASCII string
    """
    lines = []
    
    # Title box
    title = f"EXERCICE — {exercise.get('title', '')} ({exercise.get('niveau', '')})"
    lines.append(_format_box(title))
    lines.append('')
    
    # Prompt
    prompt = exercise.get('prompt', '')
    if prompt:
        lines.append(prompt)
        lines.append('')
    
    # Items
    items = exercise.get('items', [])
    for i, item in enumerate(items, 1):
        question_nl = item.get('question_nl', '')
        question_fr = item.get('question_fr', '')
        img = item.get('img', '')
        
        item_line = f"{i}. {question_nl}"
        if img:
            item_line += f" {img}"
        lines.append(item_line)
        
        if question_fr:
            lines.append(f"   {question_fr}")
        lines.append('')
    
    # Daily bonus
    if daily:
        lines.append('─' * TICKET_WIDTH)
        lines.append('💡 BONUS DU JOUR')
        nl_text = daily.get('nl', '')
        fr_text = daily.get('fr', '')
        if nl_text and fr_text:
            lines.append(f"{nl_text} → {fr_text}")
        lines.append('─' * TICKET_WIDTH)
    
    return '\n'.join(lines)


def format_answers(exercise: Dict) -> str:
    """Format answers for printing.
    
    Args:
        exercise: Exercise dict
    
    Returns:
        Formatted ASCII string with corrections
    """
    lines = []
    
    # Title box
    title = f"CORRECTIONS — {exercise.get('title', '')} ({exercise.get('niveau', '')})"
    lines.append(_format_box(title))
    lines.append('')
    
    # Items with answers
    items = exercise.get('items', [])
    for i, item in enumerate(items, 1):
        question_nl = item.get('question_nl', '')
        question_fr = item.get('question_fr', '')
        answer = item.get('answer', '')
        img = item.get('img', '')
        
        lines.append(f"{i}. {question_nl}")
        if img:
            lines.append(f"   {img}")
        if question_fr:
            lines.append(f"   {question_fr}")
        if answer:
            lines.append(f"   ✓ {answer}")
        lines.append('')
    
    # Explanations
    explanations = exercise.get('explanations', '')
    if explanations:
        lines.append('─' * TICKET_WIDTH)
        lines.append('📝 EXPLICATIONS')
        lines.append(explanations)
        lines.append('─' * TICKET_WIDTH)
    
    return '\n'.join(lines)
