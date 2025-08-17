"""
Integration tests for the complete pipeline.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock

from src.pipeline.transformation.api_client import DnDAPIClient
from src.pipeline.transformation.models import Monster, MonsterSummary


class TestPipelineIntegration:
    """Integration tests for the complete pipeline."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = DnDAPIClient()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.pipeline.transformation.api_client.requests.Session.get')
    def test_full_pipeline_flow(self, mock_get):
        """Test the complete pipeline flow with mocked API."""
        # Mock API responses
        def mock_api_response(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if '/monsters' in url and url.endswith('/monsters'):
                # Mock monsters list
                mock_response.json.return_value = {
                    "count": 3,
                    "results": [
                        {"index": "goblin", "name": "Goblin", "url": "/api/monsters/goblin"},
                        {"index": "skeleton", "name": "Skeleton", "url": "/api/monsters/skeleton"},
                        {"index": "dragon", "name": "Dragon", "url": "/api/monsters/dragon"}
                    ]
                }
            elif 'goblin' in url:
                # Mock goblin details
                mock_response.json.return_value = {
                    "name": "Goblin",
                    "hit_points": 15,
                    "armor_class": [{"type": "natural", "value": 12}],
                    "actions": [
                        {"name": "Scimitar", "desc": "Melee attack with scimitar"}
                    ]
                }
            elif 'skeleton' in url:
                # Mock skeleton details
                mock_response.json.return_value = {
                    "name": "Skeleton",
                    "hit_points": 13,
                    "armor_class": [{"type": "armor", "value": 13}],
                    "actions": [
                        {"name": "Shortsword", "desc": "Melee attack with shortsword"}
                    ]
                }
            elif 'dragon' in url:
                # Mock dragon details
                mock_response.json.return_value = {
                    "name": "Dragon",
                    "hit_points": 200,
                    "armor_class": [{"type": "natural", "value": 18}],
                    "actions": [
                        {"name": "Bite", "desc": "Bite attack"},
                        {"name": "Fire Breath", "desc": "Breathes fire"}
                    ]
                }
            
            return mock_response
        
        mock_get.side_effect = mock_api_response
        
        # Execute pipeline steps
        # Step 1: Fetch monsters list with simple limiting
        monsters_list = self.client.fetch_monsters_list(limit=10)  # Get first 10
        assert len(monsters_list) == 3
        assert all(isinstance(m, MonsterSummary) for m in monsters_list)
        
        # Step 2: Select monsters (select all for predictable testing)
        selected_monsters = monsters_list[:2]  # Select first 2
        assert len(selected_monsters) == 2
        
        # Step 3: Fetch details for selected monsters
        detailed_monsters = []
        for monster_summary in selected_monsters:
            raw_data = self.client.fetch_monster_details(monster_summary.url)
            monster = self.client.process_monster_data(raw_data)
            detailed_monsters.append(monster)
        
        assert len(detailed_monsters) == 2
        assert all(isinstance(m, Monster) for m in detailed_monsters)
        
        # Step 4: Save to JSON
        output_file = os.path.join(self.temp_dir, "test_monsters.json")
        saved_file = self.client.save_monsters_to_json(detailed_monsters, output_file)
        
        # Verify output
        assert saved_file == output_file
        assert os.path.exists(output_file)
        
        # Verify JSON content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert all("name" in monster for monster in data)
        assert all("hit_points" in monster for monster in data)
        assert all("armor_class" in monster for monster in data)
        assert all("actions" in monster for monster in data)
    
    def test_pipeline_data_validation(self):
        """Test that pipeline produces valid data structures."""
        # Create test monsters
        monsters = [
            Monster(
                name="Test Goblin",
                hit_points=15,
                armor_class=12,
                actions=[
                    {"name": "Bite", "desc": "Bite attack"}
                ]
            ),
            Monster(
                name="Test Skeleton",
                hit_points=13,
                armor_class=13,
                actions=[]
            )
        ]
        
        # Save to temp file
        output_file = os.path.join(self.temp_dir, "validation_test.json")
        self.client.save_monsters_to_json(monsters, output_file)
        
        # Load and validate structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Validate required fields
        for monster_data in data:
            assert "name" in monster_data
            assert "hit_points" in monster_data
            assert "armor_class" in monster_data
            assert "actions" in monster_data
            
            # Validate types - hit_points and armor_class can be None (honest extraction)
            assert isinstance(monster_data["name"], str)
            assert monster_data["hit_points"] is None or isinstance(monster_data["hit_points"], int)
            assert monster_data["armor_class"] is None or isinstance(monster_data["armor_class"], int)
            assert isinstance(monster_data["actions"], list)
            
            # Validate actions structure
            for action in monster_data["actions"]:
                assert "name" in action
                assert "desc" in action
                assert isinstance(action["name"], str)
                assert isinstance(action["desc"], str)
    
    def test_pipeline_error_handling(self):
        """Test pipeline behavior with various error conditions."""
        # Test empty monsters list - should return empty list, not raise error
        empty_monsters = []
        result = self.client.select_random_monsters(empty_monsters, 5)
        assert result == []  # Should return empty list
        
        # Test insufficient monsters - should return all available monsters
        few_monsters = [
            MonsterSummary(index="goblin", name="Goblin", url="/api/monsters/goblin")
        ]
        result = self.client.select_random_monsters(few_monsters, 5)
        assert len(result) == 1  # Should return the 1 available monster
        assert result[0].name == "Goblin"
        
        # Test invalid monster data processing - preserves API data as-is
        invalid_data = {}  # Missing required fields
        monster = self.client.process_monster_data(invalid_data)
        assert monster.name == ""  # Default empty string
        assert monster.hit_points is None  # Missing = None (honest extraction)
        assert monster.armor_class is None  # No armor_class = None (honest)
