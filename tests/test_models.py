"""
Unit tests for Pydantic models.
"""

import pytest
from pydantic import ValidationError

from src.pipeline.transformation.models import Action, Monster, MonsterSummary, APIResponse


class TestAction:
    """Test Action model validation."""
    
    def test_valid_action(self):
        """Test creating a valid Action."""
        action = Action(
            name="Scimitar",
            desc="Melee Weapon Attack: +4 to hit, reach 5 ft., one target."
        )
        assert action.name == "Scimitar"
        assert "Melee Weapon Attack" in action.desc
    
    def test_action_missing_fields(self):
        """Test Action validation with missing required fields."""
        with pytest.raises(ValidationError):
            Action(name="Scimitar")  # Missing desc
        
        with pytest.raises(ValidationError):
            Action(desc="Some description")  # Missing name
    
    def test_action_empty_strings(self):
        """Test Action with empty strings (should be valid)."""
        action = Action(name="", desc="")
        assert action.name == ""
        assert action.desc == ""


class TestMonster:
    """Test Monster model validation."""
    
    def test_valid_monster(self):
        """Test creating a valid Monster."""
        actions = [
            Action(name="Bite", desc="Melee attack"),
            Action(name="Claw", desc="Another attack")
        ]
        
        monster = Monster(
            name="Goblin",
            hit_points=15,
            armor_class=12,
            actions=actions
        )
        
        assert monster.name == "Goblin"
        assert monster.hit_points == 15
        assert monster.armor_class == 12
        assert len(monster.actions) == 2
        assert monster.actions[0].name == "Bite"
    
    def test_monster_without_actions(self):
        """Test Monster with no actions (should default to empty list)."""
        monster = Monster(
            name="Skeleton",
            hit_points=13,
            armor_class=13
        )
        
        assert monster.actions == []
    
    def test_monster_invalid_types(self):
        """Test Monster validation with invalid types."""
        with pytest.raises(ValidationError):
            Monster(
                name="Goblin",
                hit_points="fifteen",  # Should be int
                armor_class=12
            )
        
        with pytest.raises(ValidationError):
            Monster(
                name="Goblin",
                hit_points=15,
                armor_class="twelve"  # Should be int
            )
    
    def test_monster_missing_required_fields(self):
        """Test Monster validation with missing required fields."""
        with pytest.raises(ValidationError):
            Monster(hit_points=15, armor_class=12)  # Missing name
    
    def test_monster_serialization(self):
        """Test Monster serialization to dict."""
        monster = Monster(
            name="Dragon",
            hit_points=100,
            armor_class=18,
            actions=[Action(name="Fire Breath", desc="Breathes fire")]
        )
        
        data = monster.model_dump()
        
        assert data["name"] == "Dragon"
        assert data["hit_points"] == 100
        assert data["armor_class"] == 18
        assert len(data["actions"]) == 1
        assert data["actions"][0]["name"] == "Fire Breath"
    
    def test_monster_with_null_hit_points(self):
        """Test Monster with null hit_points (missing from API)."""
        monster = Monster(
            name="Spirit",
            hit_points=None,
            armor_class=15
        )
        
        assert monster.name == "Spirit"
        assert monster.hit_points is None
        assert monster.armor_class == 15
        
        # Test serialization preserves None
        data = monster.model_dump()
        assert data["hit_points"] is None
    
    def test_monster_with_zero_hit_points(self):
        """Test Monster with legitimate zero hit_points (different from None)."""
        monster = Monster(
            name="Construct",
            hit_points=0,
            armor_class=10
        )
        
        assert monster.name == "Construct"
        assert monster.hit_points == 0  # Zero is valid, different from None
        assert monster.armor_class == 10
        
        # Test serialization preserves zero
        data = monster.model_dump()
        assert data["hit_points"] == 0


class TestMonsterSummary:
    """Test MonsterSummary model validation."""
    
    def test_valid_monster_summary(self):
        """Test creating a valid MonsterSummary."""
        summary = MonsterSummary(
            index="goblin",
            name="Goblin",
            url="/api/monsters/goblin"
        )
        
        assert summary.index == "goblin"
        assert summary.name == "Goblin"
        assert summary.url == "/api/monsters/goblin"
    
    def test_monster_summary_missing_fields(self):
        """Test MonsterSummary validation with missing fields."""
        with pytest.raises(ValidationError):
            MonsterSummary(index="goblin", name="Goblin")  # Missing url


class TestAPIResponse:
    """Test APIResponse model validation."""
    
    def test_valid_api_response(self):
        """Test creating a valid APIResponse."""
        summaries = [
            MonsterSummary(index="goblin", name="Goblin", url="/api/monsters/goblin"),
            MonsterSummary(index="skeleton", name="Skeleton", url="/api/monsters/skeleton")
        ]
        
        response = APIResponse(
            count=2,
            results=summaries
        )
        
        assert response.count == 2
        assert len(response.results) == 2
        assert response.results[0].name == "Goblin"
    
    def test_api_response_empty_results(self):
        """Test APIResponse with empty results."""
        response = APIResponse(count=0, results=[])
        
        assert response.count == 0
        assert response.results == []
