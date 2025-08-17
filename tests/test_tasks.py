"""
Unit tests for task functions.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from src.pipeline.transformation.tasks import (
    fetch_monsters_task,
    select_random_monsters_task,
    fetch_monster_details_task,
    save_monsters_task
)
from src.pipeline.transformation.models import Monster, MonsterSummary


class TestTasks:
    """Test pipeline task functions."""
    
    @patch('src.pipeline.transformation.tasks._client')
    def test_fetch_monsters_task(self, mock_client):
        """Test fetch_monsters_task function with simple limiting."""
        # Setup mock
        mock_monsters = [
            MonsterSummary(index="goblin", name="Goblin", url="/api/monsters/goblin"),
            MonsterSummary(index="skeleton", name="Skeleton", url="/api/monsters/skeleton")
        ]
        mock_client.fetch_monsters_list.return_value = mock_monsters
        
        # Execute 
        context = {}
        result = fetch_monsters_task(**context)
        
        # Verify
        assert len(result) == 2
        assert result[0]["name"] == "Goblin"
        assert result[1]["name"] == "Skeleton"
        mock_client.fetch_monsters_list.assert_called_once_with(limit=None)
    
    @patch('src.pipeline.transformation.tasks._client')
    def test_select_random_monsters_task(self, mock_client):
        """Test select_random_monsters_task function."""
        # Setup mock context with XCom data
        mock_context = {
            'count': 3,
            'ti': Mock()
        }
        
        # Mock XCom data (serialized monsters)
        monsters_data = [
            {"index": f"monster{i}", "name": f"Monster {i}", "url": f"/api/monsters/monster{i}"}
            for i in range(10)
        ]
        mock_context['ti'].xcom_pull.return_value = monsters_data
        
        # Setup client mock
        selected_monsters = [
            MonsterSummary(index="monster1", name="Monster 1", url="/api/monsters/monster1"),
            MonsterSummary(index="monster5", name="Monster 5", url="/api/monsters/monster5"),
            MonsterSummary(index="monster8", name="Monster 8", url="/api/monsters/monster8")
        ]
        mock_client.select_random_monsters.return_value = selected_monsters
        
        # Execute
        result = select_random_monsters_task(**mock_context)
        
        # Verify
        assert len(result) == 3
        assert all("name" in monster for monster in result)
        mock_client.select_random_monsters.assert_called_once()
        
        # Verify it was called with correct count
        call_args = mock_client.select_random_monsters.call_args
        assert call_args[0][1] == 3  # count parameter
    
    def test_select_random_monsters_task_no_data(self):
        """Test select_random_monsters_task with no XCom data."""
        # Setup mock context with no data
        mock_context = {
            'ti': Mock()
        }
        mock_context['ti'].xcom_pull.return_value = None
        
        # Execute and verify exception
        with pytest.raises(ValueError) as exc_info:
            select_random_monsters_task(**mock_context)
        
        assert "No monster data received" in str(exc_info.value)
    
    @patch('src.pipeline.transformation.tasks._client')
    def test_fetch_monster_details_task(self, mock_client):
        """Test fetch_monster_details_task function."""
        # Setup mock context
        mock_context = {
            'ti': Mock()
        }
        
        # Mock XCom data (selected monsters)
        selected_monsters_data = [
            {"index": "goblin", "name": "Goblin", "url": "/api/monsters/goblin"},
            {"index": "skeleton", "name": "Skeleton", "url": "/api/monsters/skeleton"}
        ]
        mock_context['ti'].xcom_pull.return_value = selected_monsters_data
        
        # Mock detailed monsters
        detailed_monsters = [
            Monster(name="Goblin", hit_points=15, armor_class=12, actions=[]),
            Monster(name="Skeleton", hit_points=13, armor_class=13, actions=[])
        ]
        
        # Mock the client methods
        mock_client.fetch_monster_details.return_value = {"raw": "data"}
        mock_client.process_monster_data.side_effect = detailed_monsters
        
        # Execute
        result = fetch_monster_details_task(**mock_context)
        
        # Verify
        assert len(result) == 2
        assert result[0]["name"] == "Goblin"
        assert result[1]["name"] == "Skeleton"
        assert mock_client.fetch_monster_details.call_count == 2
        assert mock_client.process_monster_data.call_count == 2
    
    @patch('src.pipeline.transformation.tasks._client')
    def test_fetch_monster_details_task_with_errors(self, mock_client):
        """Test fetch_monster_details_task with some monsters failing."""
        # Setup mock context
        mock_context = {
            'ti': Mock()
        }
        
        selected_monsters_data = [
            {"index": "goblin", "name": "Goblin", "url": "/api/monsters/goblin"},
            {"index": "skeleton", "name": "Skeleton", "url": "/api/monsters/skeleton"}
        ]
        mock_context['ti'].xcom_pull.return_value = selected_monsters_data
        
        # Mock one success, one failure
        def side_effect_details(url):
            if "goblin" in url:
                return {"raw": "data"}
            else:
                raise Exception("API Error")
        
        def side_effect_process(data):
            return Monster(name="Goblin", hit_points=15, armor_class=12, actions=[])
        
        mock_client.fetch_monster_details.side_effect = side_effect_details
        mock_client.process_monster_data.side_effect = side_effect_process
        
        # Execute
        result = fetch_monster_details_task(**mock_context)
        
        # Verify - should have only successful monster
        assert len(result) == 1
        assert result[0]["name"] == "Goblin"
    
    @patch('src.pipeline.transformation.tasks._client')
    def test_save_monsters_task(self, mock_client):
        """Test save_monsters_task function."""
        # Setup mock context
        mock_context = {
            'output_file': 'test_output.json',
            'ti': Mock()
        }
        
        # Mock XCom data (monster details)
        monsters_data = [
            {"name": "Goblin", "hit_points": 15, "armor_class": 12, "actions": []},
            {"name": "Skeleton", "hit_points": 13, "armor_class": 13, "actions": []}
        ]
        mock_context['ti'].xcom_pull.return_value = monsters_data
        
        # Mock the save method
        mock_client.save_monsters_to_json.return_value = 'test_output.json'
        
        # Execute
        result = save_monsters_task(**mock_context)
        
        # Verify
        assert result == 'test_output.json'
        mock_client.save_monsters_to_json.assert_called_once()
        
        # Verify the monsters passed to save method
        call_args = mock_client.save_monsters_to_json.call_args[0]
        monsters_list = call_args[0]
        assert len(monsters_list) == 2
        assert all(isinstance(monster, Monster) for monster in monsters_list)
    
    @patch('src.pipeline.transformation.tasks._client')
    def test_save_monsters_task_default_filename(self, mock_client):
        """Test save_monsters_task with default filename."""
        # Setup mock context without output_file
        mock_context = {
            'ti': Mock()
        }
        
        monsters_data = [
            {"name": "Goblin", "hit_points": 15, "armor_class": 12, "actions": []}
        ]
        mock_context['ti'].xcom_pull.return_value = monsters_data
        
        mock_client.save_monsters_to_json.return_value = 'monsters.json'
        
        # Execute
        result = save_monsters_task(**mock_context)
        
        # Verify default filename was used
        call_args = mock_client.save_monsters_to_json.call_args
        assert call_args[0][1] == 'monsters.json'  # Default filename
