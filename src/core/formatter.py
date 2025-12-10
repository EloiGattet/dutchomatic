"""Formatting functions for exercises and answers."""

import os
from pathlib import Path
from typing import Dict, Optional

from .ticket_templates import TicketTemplateManager


TICKET_WIDTH = 58
template_manager = TicketTemplateManager()


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


def _format_custom_text(text: str, exercise: Dict, daily: Optional[Dict] = None) -> str:
    """Format custom text with variable substitution."""
    if not text:
        return ''
    
    replacements = {
        '{title}': exercise.get('title', ''),
        '{niveau}': exercise.get('niveau', ''),
        '{type}': exercise.get('type', ''),
        '{prompt}': exercise.get('prompt', ''),
    }
    
    if daily:
        replacements['{daily_nl}'] = daily.get('nl', '')
        replacements['{daily_fr}'] = daily.get('fr', '')
    
    result = text
    for key, value in replacements.items():
        result = result.replace(key, str(value))
    
    return result


def format_exercise(exercise: Dict, daily: Optional[Dict] = None, template_id: Optional[str] = None) -> tuple[str, list[str]]:
    """Format exercise for printing.
    
    Args:
        exercise: Exercise dict
        daily: Optional daily item dict
        template_id: Optional template ID to use (default: active template)
    
    Returns:
        Tuple of (formatted ASCII string, list of image paths to print before text)
    """
    # Get template
    if template_id:
        template = template_manager.get_template(template_id)
    else:
        template = template_manager.get_active_template('exercise')
    
    # Fallback to default if no template
    if not template:
        template = {
            'header': {'image': None, 'custom_text': None},
            'content': {
                'show_title': True,
                'show_niveau': True,
                'show_prompt': True,
                'max_items': None,
                'item_format': 'numbered'
            },
            'footer': {'image': None, 'custom_text': None}
        }
    
    lines = []
    header_images = []
    
    # Header image
    header_image = template.get('header', {}).get('image')
    if header_image:
        # Try data/ first, then web/static/images/
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        data_image = project_root / 'data' / header_image
        web_image = project_root / 'src' / 'web' / 'static' / 'images' / header_image
        
        if data_image.exists():
            header_images.append(str(data_image.relative_to(project_root)))
        elif web_image.exists():
            header_images.append(str(web_image.relative_to(project_root)))
        else:
            # Try direct path
            header_images.append(header_image)
    
    # Default logo if no header image specified
    if not header_images:
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        # Try data/ first, then web/static/images/
        default_logo_data = project_root / 'data' / 'logo_print.png'
        default_logo_web = project_root / 'src' / 'web' / 'static' / 'images' / 'logo_print.png'
        
        if default_logo_data.exists():
            header_images.append(str(default_logo_data.relative_to(project_root)))
        elif default_logo_web.exists():
            header_images.append(str(default_logo_web.relative_to(project_root)))
    
    # Header custom text
    if template.get('header', {}).get('custom_text'):
        header_text = _format_custom_text(
            template['header']['custom_text'],
            exercise,
            daily
        )
        if header_text:
            lines.append(header_text)
            lines.append('')
    
    # Title box (if enabled)
    if template.get('content', {}).get('show_title', True):
        if template.get('content', {}).get('show_niveau', True):
            title = f"EXERCICE — {exercise.get('title', '')} ({exercise.get('niveau', '')})"
        else:
            title = f"EXERCICE — {exercise.get('title', '')}"
        lines.append(_format_box(title))
        lines.append('')
    
    # Prompt (if enabled)
    if template.get('content', {}).get('show_prompt', True):
        prompt = exercise.get('prompt', '')
        if prompt:
            lines.append(prompt)
            lines.append('')
    
    # Items
    items = exercise.get('items', [])
    max_items = template.get('content', {}).get('max_items')
    if max_items:
        items = items[:max_items]
    
    item_format = template.get('content', {}).get('item_format', 'numbered')
    
    for i, item in enumerate(items, 1):
        question_nl = item.get('question_nl', '')
        question_fr = item.get('question_fr', '')
        img = item.get('img', '')
        
        if item_format == 'numbered':
            item_line = f"{i}. {question_nl}"
        elif item_format == 'bulleted':
            item_line = f"- {question_nl}"
        else:  # plain
            item_line = question_nl
        
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
    
    # Footer custom text
    if template.get('footer', {}).get('custom_text'):
        footer_text = _format_custom_text(
            template['footer']['custom_text'],
            exercise,
            daily
        )
        if footer_text:
            lines.append('')
            lines.append(footer_text)
    
    return '\n'.join(lines), header_images


def format_answers(exercise: Dict, template_id: Optional[str] = None) -> tuple[str, list[str]]:
    """Format answers for printing.
    
    Args:
        exercise: Exercise dict
        template_id: Optional template ID to use (default: active template)
    
    Returns:
        Tuple of (formatted ASCII string, list of image paths to print before text)
    """
    # Get template
    if template_id:
        template = template_manager.get_template(template_id)
    else:
        template = template_manager.get_active_template('answers')
    
    # Fallback to default if no template
    if not template:
        template = {
            'header': {'image': None, 'custom_text': None},
            'content': {
                'show_title': True,
                'show_niveau': True,
                'max_items': None,
                'item_format': 'numbered'
            },
            'footer': {'image': None, 'custom_text': None}
        }
    
    lines = []
    header_images = []
    
    # Header image
    header_image = template.get('header', {}).get('image')
    if header_image:
        # Try data/ first, then web/static/images/
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        data_image = project_root / 'data' / header_image
        web_image = project_root / 'src' / 'web' / 'static' / 'images' / header_image
        
        if data_image.exists():
            header_images.append(str(data_image.relative_to(project_root)))
        elif web_image.exists():
            header_images.append(str(web_image.relative_to(project_root)))
        else:
            # Try direct path
            header_images.append(header_image)
    
    # Header custom text
    if template.get('header', {}).get('custom_text'):
        header_text = _format_custom_text(
            template['header']['custom_text'],
            exercise
        )
        if header_text:
            lines.append(header_text)
            lines.append('')
    
    # Title box (if enabled)
    if template.get('content', {}).get('show_title', True):
        if template.get('content', {}).get('show_niveau', True):
            title = f"CORRECTIONS — {exercise.get('title', '')} ({exercise.get('niveau', '')})"
        else:
            title = f"CORRECTIONS — {exercise.get('title', '')}"
        lines.append(_format_box(title))
        lines.append('')
    
    # Items with answers
    items = exercise.get('items', [])
    max_items = template.get('content', {}).get('max_items')
    if max_items:
        items = items[:max_items]
    
    item_format = template.get('content', {}).get('item_format', 'numbered')
    
    for i, item in enumerate(items, 1):
        question_nl = item.get('question_nl', '')
        question_fr = item.get('question_fr', '')
        answer = item.get('answer', '')
        img = item.get('img', '')
        
        if item_format == 'numbered':
            lines.append(f"{i}. {question_nl}")
        elif item_format == 'bulleted':
            lines.append(f"- {question_nl}")
        else:  # plain
            lines.append(question_nl)
        
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
    
    # Footer custom text
    if template.get('footer', {}).get('custom_text'):
        footer_text = _format_custom_text(
            template['footer']['custom_text'],
            exercise
        )
        if footer_text:
            lines.append('')
            lines.append(footer_text)
    
    return '\n'.join(lines), header_images
