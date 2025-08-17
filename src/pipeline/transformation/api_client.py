import json
import random
import logging
import requests
from typing import List, Dict, Any
from pathlib import Path

from .models import Monster, MonsterSummary, APIResponse, Action

# Configure logger
logger = logging.getLogger(__name__)


class DnDAPIClient:
    """Client for interaction with the D&D 5e API."""
    
    BASE_URL = "https://www.dnd5eapi.co/api/2014"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DnD-Monster-Pipeline/1.0'
        })
        # Set timeouts for all requests
        self.timeout = 30
    
    def fetch_monsters_list(self, limit: int = None) -> List[MonsterSummary]:
        """
        Fetch monsters from API 
        """
        url = f"{self.BASE_URL}/monsters"
        
        try:
            logger.info(f"Fetching monsters from: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            api_response = APIResponse(**response.json())
            
            # Apply limit if specified
            if limit is not None:
                limited_results = api_response.results[:limit]
                logger.info(f"Limited to first {len(limited_results)} monsters from total {len(api_response.results)} available")
                return limited_results
            else:
                logger.info(f"Fetched all {len(api_response.results)} monsters from API")
                return api_response.results
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch monsters list: {e}")
            raise Exception(f"Failed to fetch monsters list: {e}")
    
    def fetch_monster_details(self, monster_url: str) -> Dict[str, Any]:
        """Fetch detailed information for a specific monster."""
        # If URL is relative, add base URL
        if monster_url.startswith('/'):
            full_url = f"https://www.dnd5eapi.co{monster_url}"
        else:
            full_url = monster_url
        
        try:
            logger.info(f"Fetching details from: {full_url}")
            response = self.session.get(full_url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch monster details from {full_url}: {e}")
            raise Exception(f"Failed to fetch monster details from {full_url}: {e}")
    
    def select_random_monsters(self, monsters: List[MonsterSummary], count: int = 5) -> List[MonsterSummary]:
        """
        Select random monsters from the list.
        """
        if len(monsters) < count:
            logger.warning(f"Requested {count} monsters but only {len(monsters)} available. Using all available.")
            return monsters
        
        logger.info(f"Selecting {count} random monsters from {len(monsters)} available monsters")
        selected = random.sample(monsters, count)
        logger.info(f"Selected monsters: {[m.name for m in selected]}")
        return selected
    
    def process_monster_data(self, raw_data: Dict[str, Any]) -> Monster:
        """Process raw monster data."""
        try:
            # Process actions - only name and desc as per challenge
            actions = []
            if 'actions' in raw_data and raw_data['actions']:
                for action_data in raw_data['actions']:
                    action = Action(
                        name=action_data.get('name', ''),
                        desc=action_data.get('desc', '')
                    )
                    actions.append(action)
            
            # Extract armor_class from API data - if null/missing, keep as None
            armor_class = None  # Start with None
            if 'armor_class' in raw_data and raw_data['armor_class']:
                if isinstance(raw_data['armor_class'], list) and raw_data['armor_class']:
                    # Extract value from list format, keep None if missing
                    armor_class = raw_data['armor_class'][0].get('value')
                elif isinstance(raw_data['armor_class'], int):
                    armor_class = raw_data['armor_class']
            
            # Extract hit_points from API data - if null/missing, keep as None
            hit_points = raw_data.get('hit_points')  # Preserve None if missing
            
            # Create monster
            monster = Monster(
                name=raw_data.get('name', ''),
                hit_points=hit_points,
                armor_class=armor_class,
                actions=actions
            )
            
            return monster
        except Exception as e:
            raise Exception(f"Failed to process monster data: {e}")
    
    def save_monsters_to_json(self, monsters: List[Monster], filename: str = "monsters.json"):
        """Save monsters data to JSON file."""
        try:
            data = [monster.model_dump() for monster in monsters]
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved {len(monsters)} monsters to {filename}")
            return filename
        except Exception as e:
            raise Exception(f"Failed to save monsters to JSON: {e}")
