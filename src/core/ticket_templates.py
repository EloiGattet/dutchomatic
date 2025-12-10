"""Ticket template management."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class TicketTemplateManager:
    """Manages ticket templates stored in JSON."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize template manager.
        
        Args:
            config_path: Path to templates JSON file (default: config/ticket_templates.json)
        """
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / 'config' / 'ticket_templates.json'
        
        self.config_path = Path(config_path)
        self._templates = None
    
    def _load_templates(self) -> Dict:
        """Load templates from JSON file."""
        if self._templates is not None:
            return self._templates
        
        default_templates = {
            'templates': [
                {
                    'id': 'default',
                    'name': 'Template par défaut',
                    'enabled': True,
                    'order': 0,
                    'type': 'exercise',
                    'header': {
                        'image': None,
                        'text': None,
                        'custom_text': None
                    },
                    'content': {
                        'show_title': True,
                        'show_niveau': True,
                        'show_prompt': True,
                        'max_items': None,
                        'item_format': 'numbered'
                    },
                    'footer': {
                        'image': None,
                        'text': None,
                        'custom_text': None
                    }
                }
            ]
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Merge with defaults
                    if 'templates' in data:
                        default_templates['templates'] = data['templates']
                    self._templates = default_templates
            except Exception as e:
                print(f"Warning: Could not load ticket templates: {e}")
                self._templates = default_templates
        else:
            self._templates = default_templates
            self._save_templates()
        
        return self._templates
    
    def _save_templates(self) -> bool:
        """Save templates to JSON file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._templates, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving ticket templates: {e}")
            return False
    
    def get_templates(self) -> List[Dict]:
        """Get all templates, sorted by order."""
        templates = self._load_templates()
        return sorted(
            templates.get('templates', []),
            key=lambda t: (t.get('order', 999), t.get('name', ''))
        )
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID."""
        templates = self.get_templates()
        for template in templates:
            if template.get('id') == template_id:
                return template
        return None
    
    def get_active_template(self, template_type: str = 'exercise') -> Optional[Dict]:
        """Get the first enabled template of given type."""
        templates = self.get_templates()
        for template in templates:
            if (template.get('enabled', False) and 
                template.get('type') == template_type):
                return template
        return None
    
    def add_template(self, template: Dict) -> str:
        """Add a new template.
        
        Args:
            template: Template dict (must have 'id' and 'name')
        
        Returns:
            Template ID
        """
        self._load_templates()
        if 'id' not in template:
            raise ValueError("Template must have an 'id' field")
        
        # Check if ID already exists
        existing = self.get_template(template['id'])
        if existing:
            raise ValueError(f"Template with ID '{template['id']}' already exists")
        
        # Set defaults
        template.setdefault('enabled', True)
        template.setdefault('order', len(self._templates['templates']))
        template.setdefault('type', 'exercise')
        
        self._templates['templates'].append(template)
        self._save_templates()
        self._templates = None  # Force reload
        return template['id']
    
    def update_template(self, template_id: str, updates: Dict) -> bool:
        """Update a template.
        
        Args:
            template_id: ID of template to update
            updates: Dict with fields to update
        
        Returns:
            True if successful
        """
        self._load_templates()
        templates = self._templates['templates']
        
        for i, template in enumerate(templates):
            if template.get('id') == template_id:
                templates[i].update(updates)
                self._save_templates()
                self._templates = None  # Force reload
                return True
        
        return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template.
        
        Args:
            template_id: ID of template to delete
        
        Returns:
            True if successful
        """
        self._load_templates()
        templates = self._templates['templates']
        
        for i, template in enumerate(templates):
            if template.get('id') == template_id:
                templates.pop(i)
                self._save_templates()
                self._templates = None  # Force reload
                return True
        
        return False
    
    def reorder_templates(self, template_ids: List[str]) -> bool:
        """Reorder templates.
        
        Args:
            template_ids: List of template IDs in desired order
        
        Returns:
            True if successful
        """
        self._load_templates()
        templates = self._templates['templates']
        
        # Create mapping
        template_map = {t.get('id'): t for t in templates}
        
        # Reorder
        reordered = []
        for template_id in template_ids:
            if template_id in template_map:
                template = template_map[template_id]
                template['order'] = len(reordered)
                reordered.append(template)
        
        # Add any remaining templates
        for template in templates:
            if template.get('id') not in template_ids:
                template['order'] = len(reordered)
                reordered.append(template)
        
        self._templates['templates'] = reordered
        self._save_templates()
        self._templates = None  # Force reload
        return True

