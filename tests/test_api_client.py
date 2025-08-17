"""
Unit tests for API client functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests

from src.pipeline.transformation.api_client import DnDAPIClient
from src.pipeline.transformation.models import Monster, MonsterSummary, Action


class TestDnDAPIClient:
    """Test DnDAPIClient functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = DnDAPIClient()
    
    @patch('src.pipeline.transformation.api_client.requests.Session.get')
    def test_fetch_monsters_list_success(self, mock_get):
        """Test successful fetch of monsters list with simple limiting."""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "count": 10,
            "results": [
                {"index": f"monster{i}", "name": f"Monster {i}", "url": f"/api/monsters/monster{i}"}
                for i in range(10)
            ]
        }
        mock_get.return_value = mock_response
        
        # Execute with limit parameter
        monsters = self.client.fetch_monsters_list(limit=5)
        
        # Verify - should get first 5 monsters
        assert len(monsters) == 5
        assert monsters[0].name == "Monster 0"
        assert monsters[4].name == "Monster 4"
        
        # Verify API was called once
        mock_get.assert_called_once()
    
    @patch('src.pipeline.transformation.api_client.requests.Session.get')
    def test_fetch_monsters_list_api_error(self, mock_get):
        """Test fetch monsters list with API error."""
        # Mock API error
        mock_get.side_effect = requests.RequestException("API Error")
        
        # Execute and verify exception
        with pytest.raises(Exception) as exc_info:
            self.client.fetch_monsters_list()
        
        assert "Failed to fetch monsters list" in str(exc_info.value)
    
    @patch('src.pipeline.transformation.api_client.requests.Session.get')
    def test_fetch_monster_details_success(self, mock_get):
        """Test successful fetch of monster details."""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "name": "Goblin",
            "hit_points": 15,
            "armor_class": [{"type": "natural", "value": 12}],
            "actions": [
                {
                    "name": "Scimitar",
                    "desc": "Melee Weapon Attack: +4 to hit, reach 5 ft., one target."
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Execute
        details = self.client.fetch_monster_details("/api/monsters/goblin")
        
        # Verify
        assert details["name"] == "Goblin"
        assert details["hit_points"] == 15
        assert len(details["actions"]) == 1
        mock_get.assert_called_once()
    
    def test_select_random_monsters_success(self):
        """Test successful random monster selection."""
        # Create test monsters
        monsters = [
            MonsterSummary(index=f"monster{i}", name=f"Monster {i}", url=f"/api/monsters/monster{i}")
            for i in range(10)
        ]
        
        # Execute
        selected = self.client.select_random_monsters(monsters, 3)
        
        # Verify
        assert len(selected) == 3
        assert all(isinstance(monster, MonsterSummary) for monster in selected)
        # Verify no duplicates
        names = [monster.name for monster in selected]
        assert len(names) == len(set(names))
    
    def test_select_random_monsters_not_enough(self):
        """Test random selection with insufficient monsters - now returns all available."""
        # Create insufficient monsters
        monsters = [
            MonsterSummary(index="monster1", name="Monster 1", url="/api/monsters/monster1")
        ]
        
        # Execute - should now return all available instead of raising error
        selected = self.client.select_random_monsters(monsters, 5)
        
        # Verify - should get all available monsters
        assert len(selected) == 1
        assert selected[0].name == "Monster 1"
    
    def test_process_monster_data_complete(self):
        """Test processing complete monster data."""
        # Mock raw data
        raw_data = {
            "name": "Dragon",
            "hit_points": 200,
            "armor_class": [{"type": "natural", "value": 18}],
            "actions": [
                {"name": "Bite", "desc": "Bite attack"},
                {"name": "Claw", "desc": "Claw attack"}
            ]
        }
        
        # Execute
        monster = self.client.process_monster_data(raw_data)
        
        # Verify
        assert isinstance(monster, Monster)
        assert monster.name == "Dragon"
        assert monster.hit_points == 200
        assert monster.armor_class == 18
        assert len(monster.actions) == 2
        assert monster.actions[0].name == "Bite"
    
    def test_process_monster_data_minimal(self):
        """Test processing minimal monster data."""
        # Mock minimal data
        raw_data = {
            "name": "Simple Monster",
            "hit_points": 10
        }
        
        # Execute
        monster = self.client.process_monster_data(raw_data)
        
        # Verify defaults
        assert monster.name == "Simple Monster"
        assert monster.hit_points == 10
        assert monster.armor_class is None  # No armor_class in API = None
        assert monster.actions == []  # Default empty
    
    def test_process_monster_data_different_armor_formats(self):
        """Test processing different armor class formats."""
        # Test list format
        raw_data_list = {
            "name": "Monster",
            "hit_points": 10,
            "armor_class": [{"value": 15}]
        }
        monster = self.client.process_monster_data(raw_data_list)
        assert monster.armor_class == 15
        
        # Test integer format
        raw_data_int = {
            "name": "Monster",
            "hit_points": 10,
            "armor_class": 12
        }
        monster = self.client.process_monster_data(raw_data_int)
        assert monster.armor_class == 12
    
    def test_process_monster_data_missing_hit_points(self):
        """Test processing monster data with missing hit_points."""
        # Test completely missing hit_points
        raw_data_missing = {
            "name": "Ghost",
            "armor_class": [{"value": 11}]
            # No hit_points field
        }
        monster = self.client.process_monster_data(raw_data_missing)
        assert monster.name == "Ghost"
        assert monster.hit_points is None  # Should be None, not default
        assert monster.armor_class == 11
        
        # Test explicit null hit_points
        raw_data_null = {
            "name": "Spirit",
            "hit_points": None,
            "armor_class": [{"value": 12}]
        }
        monster = self.client.process_monster_data(raw_data_null)
        assert monster.name == "Spirit"
        assert monster.hit_points is None  # Should preserve None
        assert monster.armor_class == 12
    
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.dump')
    def test_save_monsters_to_json(self, mock_json_dump, mock_open):
        """Test saving monsters to JSON file."""
        # Create test monsters
        monsters = [
            Monster(name="Goblin", hit_points=15, armor_class=12, actions=[]),
            Monster(name="Skeleton", hit_points=13, armor_class=13, actions=[])
        ]
        
        # Execute
        result = self.client.save_monsters_to_json(monsters, "test.json")
        
        # Verify
        assert result == "test.json"
        mock_open.assert_called_once_with("test.json", 'w', encoding='utf-8')
        mock_json_dump.assert_called_once()
        
        # Verify the data structure passed to json.dump
        call_args = mock_json_dump.call_args[0]
        saved_data = call_args[0]
        assert len(saved_data) == 2
        assert saved_data[0]["name"] == "Goblin"
        assert saved_data[1]["name"] == "Skeleton"
