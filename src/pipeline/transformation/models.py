from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Action(BaseModel):
    """Model for monster action"""
    name: str
    desc: str  
    
    model_config = ConfigDict(populate_by_name=True)


class Monster(BaseModel):
    """Model for monster data"""
    name: str
    hit_points: Optional[int] = None  # Can be None if missing/null in API
    armor_class: Optional[int] = None  # Can be None if missing/null in API
    actions: List[Action] = []
    
    model_config = ConfigDict(populate_by_name=True)


class MonsterSummary(BaseModel):
    """Model for API monster list response."""
    index: str
    name: str
    url: str


class APIResponse(BaseModel):
    """Model for API response."""
    count: int
    results: List[MonsterSummary]
