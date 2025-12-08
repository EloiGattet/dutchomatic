#!/usr/bin/env python3
"""Test script for core logic."""

import os
import shutil
import tempfile
from pathlib import Path

from src.core import (
    select_exercise,
    select_daily,
    format_exercise,
    format_answers,
    StateManager
)
from src.storage import JSONStorage


def test_core():
    """Test all core logic operations."""
    test_dir = tempfile.mkdtemp()
    print(f"Testing in: {test_dir}")
    
    try:
        storage = JSONStorage(data_dir=test_dir)
        
        # Add test exercises
        exercises = [
            {
                'id': 'ex_a1_1',
                'niveau': 'A1',
                'type': 'vocabulary',
                'title': 'Test A1',
                'prompt': 'Traduis :',
                'items': [
                    {'qid': 'q1', 'question_nl': 'test', 'question_fr': '____', 'answer': 'test'}
                ],
                'tags': []
            },
            {
                'id': 'ex_a1_2',
                'niveau': 'A1',
                'type': 'grammar',
                'title': 'Test A1 Grammar',
                'prompt': 'Complète :',
                'items': [
                    {'qid': 'q1', 'question_nl': 'ik ben', 'question_fr': '____', 'answer': 'je suis'}
                ],
                'tags': []
            },
            {
                'id': 'ex_a2_1',
                'niveau': 'A2',
                'type': 'vocabulary',
                'title': 'Test A2',
                'prompt': 'Traduis :',
                'items': [
                    {'qid': 'q1', 'question_nl': 'advanced', 'question_fr': '____', 'answer': 'avancé'}
                ],
                'tags': []
            }
        ]
        
        for ex in exercises:
            storage.add_exercise(ex)
        
        # Add test daily
        daily = {
            'id': 'daily_001',
            'kind': 'expression',
            'nl': 'Test NL',
            'fr': 'Test FR'
        }
        storage.add_daily(daily)
        
        # Test 1: Selection strict
        print("\n✓ Test 1: Selection strict (A1)")
        selected = select_exercise(storage, 'A1', policy='strict')
        assert selected is not None
        assert selected['niveau'] == 'A1'
        print(f"  Selected: {selected['id']} ({selected['niveau']})")
        
        # Test 2: Selection mix
        print("\n✓ Test 2: Selection mix (A2)")
        selected = select_exercise(storage, 'A2', policy='mix')
        assert selected is not None
        assert selected['niveau'] in ['A1', 'A2']
        print(f"  Selected: {selected['id']} ({selected['niveau']})")
        
        # Test 3: Selection daily
        print("\n✓ Test 3: Selection daily")
        selected_daily = select_daily(storage)
        assert selected_daily is not None
        assert selected_daily['id'] == 'daily_001'
        print(f"  Selected: {selected_daily['id']}")
        
        # Test 4: Formatage exercice
        print("\n✓ Test 4: Formatage exercice")
        exercise = storage.get_exercise('ex_a1_1')
        formatted = format_exercise(exercise, daily)
        assert 'EXERCICE' in formatted
        assert 'Test A1' in formatted
        assert 'BONUS DU JOUR' in formatted
        print("  Formatted exercise (with daily):")
        print(formatted[:200] + "...")
        
        # Test 5: Formatage sans daily
        formatted_no_daily = format_exercise(exercise, None)
        assert 'BONUS DU JOUR' not in formatted_no_daily
        print("  Formatted exercise (without daily): OK")
        
        # Test 6: Formatage réponses
        print("\n✓ Test 5: Formatage réponses")
        exercise['explanations'] = 'Test explanation'
        formatted_answers = format_answers(exercise)
        assert 'CORRECTIONS' in formatted_answers
        assert '✓ test' in formatted_answers
        assert 'EXPLICATIONS' in formatted_answers
        print("  Formatted answers:")
        print(formatted_answers[:200] + "...")
        
        # Test 7: State manager
        print("\n✓ Test 6: State manager")
        state_mgr = StateManager(storage)
        
        # Print exercise
        result = state_mgr.print_exercise('ex_a1_1')
        assert result is True
        
        state = storage.get_state()
        assert state['last_exercise_id'] == 'ex_a1_1'
        assert state['compteur_total'] == 1
        assert state['xp'] == 1
        assert len(state['history']) == 1
        assert state['history'][0]['exercise_id'] == 'ex_a1_1'
        assert state['history'][0]['with_answers'] is False
        print(f"  State after print_exercise: compteur={state['compteur_total']}, xp={state['xp']}")
        
        # Print answers
        result = state_mgr.print_answers('ex_a1_1')
        assert result is True
        
        state = storage.get_state()
        assert len(state['history']) == 2
        assert state['history'][1]['with_answers'] is True
        print(f"  State after print_answers: history entries={len(state['history'])}")
        
        # Test 8: Cas limites
        print("\n✓ Test 7: Cas limites")
        empty_storage = JSONStorage(data_dir=tempfile.mkdtemp())
        no_exercise = select_exercise(empty_storage, 'A1')
        assert no_exercise is None
        print("  No exercise available: OK")
        
        no_daily = select_daily(empty_storage)
        assert no_daily is None
        print("  No daily available: OK")
        
        print("\n✅ All tests passed!")
        
    finally:
        shutil.rmtree(test_dir)
        print(f"Cleaned up: {test_dir}")


if __name__ == '__main__':
    test_core()
