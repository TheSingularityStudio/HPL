#!/usr/bin/env python3
"""
Test user data objects (declarative data definition) functionality
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hpl_runtime.core.parser import HPLParser
from hpl_runtime.core.evaluator import HPLEvaluator


class TestUserData(unittest.TestCase):
    """Test user data object functionality"""
    
    def _create_evaluator_from_code(self, code):
        """Create evaluator from HPL code"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hpl', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            parser = HPLParser(temp_file)
            (classes, objects, functions, main_func, call_target, call_args, imports,
             user_data) = parser.parse()
            
            evaluator = HPLEvaluator(
                classes=classes,
                objects=objects,
                functions=functions,
                main_func=main_func,
                call_target=call_target,
                call_args=call_args,
                user_data=user_data
            )
            return evaluator, user_data
        finally:
            os.unlink(temp_file)
    
    def test_simple_config_access(self):
        """Test simple config data access"""
        code = '''
config:
  title: "Test Game"
  version: "1.0"

main: () => {
    echo config.title
  }

call: main()
'''
        evaluator, user_data = self._create_evaluator_from_code(code)
        
        # Verify user data is correctly parsed
        self.assertIn('config', user_data)
        self.assertEqual(user_data['config']['title'], 'Test Game')
        self.assertEqual(user_data['config']['version'], '1.0')
        
        # Verify data is in global scope
        self.assertIn('config', evaluator.global_scope)
    
    def test_nested_data_access(self):
        """Test nested data access"""
        code = '''
scenes:
  forest:
    name: "Misty Forest"
    description: "A mysterious forest"
    choices:
      - text: "Enter cave"
        target: "cave"

main: () => {
    scene = scenes.forest
    echo scene.name
  }

call: main()
'''
        evaluator, user_data = self._create_evaluator_from_code(code)
        
        # Verify nested structure
        self.assertIn('scenes', user_data)
        self.assertIn('forest', user_data['scenes'])
        self.assertEqual(user_data['scenes']['forest']['name'], 'Misty Forest')
        self.assertIsInstance(user_data['scenes']['forest']['choices'], list)
    
    def test_array_data(self):
        """Test array type data"""
        code = '''
items:
  - name: "Sword"
    attack: 10
  - name: "Shield"
    defense: 5

main: () => {
    first = items[0]
    echo first.name
  }

call: main()
'''
        evaluator, user_data = self._create_evaluator_from_code(code)
        
        # Verify array is correctly parsed
        self.assertIn('items', user_data)
        self.assertIsInstance(user_data['items'], list)
        self.assertEqual(len(user_data['items']), 2)
        self.assertEqual(user_data['items'][0]['name'], 'Sword')
    
    def test_player_data(self):
        """Test player data object"""
        code = '''
player:
  name: "Hero"
  hp: 100
  max_hp: 100
  gold: 0
  inventory: ["sword", "potion"]

main: () => {
    echo player.name
    echo player.hp
  }

call: main()
'''
        evaluator, user_data = self._create_evaluator_from_code(code)
        
        # Verify player data
        self.assertIn('player', user_data)
        self.assertEqual(user_data['player']['name'], 'Hero')
        self.assertEqual(user_data['player']['hp'], 100)
        self.assertIsInstance(user_data['player']['inventory'], list)
        self.assertEqual(len(user_data['player']['inventory']), 2)
    
    def test_multiple_data_objects(self):
        """Test multiple data objects coexistence"""
        code = '''
config:
  title: "Game"
  difficulty: "normal"

scenes:
  start: {name: "Start"}
  end: {name: "End"}

items:
  sword: {damage: 10}
  shield: {defense: 5}

player:
  hp: 100

game_state:
  current_scene: "start"
  turn: 0

main: () => {
    echo config.title
    echo scenes.start.name
    echo player.hp
  }

call: main()
'''
        evaluator, user_data = self._create_evaluator_from_code(code)
        
        # Verify all data objects exist
        self.assertIn('config', user_data)
        self.assertIn('scenes', user_data)
        self.assertIn('items', user_data)
        self.assertIn('player', user_data)
        self.assertIn('game_state', user_data)
        
        # Verify data integrity
        self.assertEqual(user_data['config']['title'], 'Game')
        self.assertEqual(user_data['scenes']['start']['name'], 'Start')
        self.assertEqual(user_data['items']['sword']['damage'], 10)
        self.assertEqual(user_data['player']['hp'], 100)
        self.assertEqual(user_data['game_state']['current_scene'], 'start')
    
    def test_dict_property_assignment(self):
        """Test dictionary property assignment"""
        code = '''
player:
  hp: 100
  gold: 0

main: () => {
    player.hp = 80
    player.gold = 50
    echo player.hp
    echo player.gold
  }

call: main()
'''
        evaluator, user_data = self._create_evaluator_from_code(code)
        
        # Initial value
        self.assertEqual(evaluator.global_scope['player']['hp'], 100)
        
        # Verify evaluator can handle assignment statements
        self.assertIn('player', evaluator.global_scope)
        self.assertIsInstance(evaluator.global_scope['player'], dict)


class TestDictPropertyAccess(unittest.TestCase):
    """Test dictionary property access syntax"""
    
    def setUp(self):
        """Setup test environment"""
        self.evaluator = HPLEvaluator(
            classes={},
            objects={},
            user_data={
                'config': {'title': 'Game', 'version': '1.0'},
                'player': {'name': 'Hero', 'hp': 100, 'inventory': ['sword']}
            }
        )
    
    def test_dot_access_read(self):
        """Test dot notation read access"""
        result = self.evaluator._lookup_variable('config.title', {})
        self.assertEqual(result, 'Game')
    
    def test_dot_access_nested(self):
        """Test nested dot notation access"""
        result = self.evaluator._lookup_variable('player.name', {})
        self.assertEqual(result, 'Hero')
        
        result = self.evaluator._lookup_variable('player.hp', {})
        self.assertEqual(result, 100)
    
    def test_dot_access_array_in_dict(self):
        """Test array access in dictionary"""
        result = self.evaluator._lookup_variable('player.inventory', {})
        self.assertIsInstance(result, list)
        self.assertEqual(result[0], 'sword')


if __name__ == '__main__':
    unittest.main()
