#!/usr/bin/env python3
"""Test script for storage layer."""

import os
import shutil
import tempfile
from pathlib import Path

from src.storage import JSONStorage


def test_storage():
    """Test all storage operations."""
    # Create temporary directory
    test_dir = tempfile.mkdtemp()
    print(f"Testing in: {test_dir}")
    
    try:
        storage = JSONStorage(data_dir=test_dir)
        
        # Test 1: Files are created
        print("✓ Test 1: Files created")
        assert Path(test_dir, 'exercises.json').exists()
        assert Path(test_dir, 'daily.json').exists()
        assert Path(test_dir, 'state.json').exists()
        
        # Test 2: Exercise CRUD
        print("✓ Test 2: Exercise CRUD")
        exercise = {
            'id': 'test_001',
            'niveau': 'A1',
            'type': 'vocabulary',
            'title': 'Test Exercise',
            'items': []
        }
        ex_id = storage.add_exercise(exercise)
        assert ex_id == 'test_001'
        
        retrieved = storage.get_exercise('test_001')
        assert retrieved is not None
        assert retrieved['title'] == 'Test Exercise'
        
        exercise['title'] = 'Updated Exercise'
        storage.update_exercise('test_001', exercise)
        updated = storage.get_exercise('test_001')
        assert updated['title'] == 'Updated Exercise'
        
        all_exercises = storage.get_all_exercises({'niveau': 'A1'})
        assert len(all_exercises) == 1
        
        storage.delete_exercise('test_001')
        assert storage.get_exercise('test_001') is None
        
        # Test 3: Daily CRUD
        print("✓ Test 3: Daily CRUD")
        daily = {
            'id': 'daily_001',
            'kind': 'expression',
            'nl': 'Test NL',
            'fr': 'Test FR'
        }
        daily_id = storage.add_daily(daily)
        assert daily_id == 'daily_001'
        
        retrieved = storage.get_daily('daily_001')
        assert retrieved is not None
        assert retrieved['nl'] == 'Test NL'
        
        all_daily = storage.get_all_daily('expression')
        assert len(all_daily) == 1
        
        # Test 4: State management
        print("✓ Test 4: State management")
        state = storage.get_state()
        assert 'niveau_actuel' in state
        assert state['niveau_actuel'] == 'A1'
        
        storage.update_state('xp', 10)
        state = storage.get_state()
        assert state['xp'] == 10
        
        history_entry = {
            'exercise_id': 'ex_001',
            'printed_at': '2025-01-01T00:00:00Z',
            'with_answers': False
        }
        storage.add_history_entry(history_entry)
        state = storage.get_state()
        assert len(state['history']) == 1
        assert state['history'][0]['exercise_id'] == 'ex_001'
        
        # Test 5: Validation errors
        print("✓ Test 5: Validation")
        try:
            invalid_exercise = {'id': 'bad', 'niveau': 'A1'}  # Missing type, title
            storage.add_exercise(invalid_exercise)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        
        try:
            invalid_daily = {'id': 'bad', 'kind': 'invalid'}  # Invalid kind
            storage.add_daily(invalid_daily)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        
        print("\n✅ All tests passed!")
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"Cleaned up: {test_dir}")


if __name__ == '__main__':
    test_storage()
