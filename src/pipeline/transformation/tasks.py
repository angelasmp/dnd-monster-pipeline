"""
Task functions for the D&D Monster Pipeline.
"""

import logging
from typing import List, Dict, Any
from .api_client import DnDAPIClient
from .models import Monster, MonsterSummary

# Configure logger
logger = logging.getLogger(__name__)

# Create a single client instance to avoid redundancy
_client = DnDAPIClient()


def fetch_monsters_task(**context) -> List[Dict[str, Any]]:
    """
    Task to fetch monsters from D&D API.
    Fetch ALL monsters for better random selection
    """
    # Get limit from op_kwargs or context, default to None (fetch all)
    limit = context.get('limit', None)
    
    monsters_list = _client.fetch_monsters_list(limit=limit)
    
    logger.info(f"Fetched {len(monsters_list)} monsters from D&D API")
    
    # Return serialized data for XCom
    return [monster.model_dump() for monster in monsters_list]


def select_random_monsters_task(**context) -> List[Dict[str, Any]]:
    """
    Task to select random monsters from the fetched list.
    """
    # Get parameters from task configuration
    count = context.get('count', 5)  # Default to 5 if not specified
    
    # Pull data from previous task
    ti = context['ti']
    monsters_data = ti.xcom_pull(task_ids='fetch_monsters')
    
    if not monsters_data:
        raise ValueError("No monster data received from fetch_monsters task")
    
    # Convert back to MonsterSummary objects
    monsters_list = [MonsterSummary(**monster) for monster in monsters_data]
    
    # Select random monsters
    selected_monsters = _client.select_random_monsters(monsters_list, count)
    
    monster_names = [monster.name for monster in selected_monsters]
    logger.info(f"Selected {len(selected_monsters)} random monsters: {', '.join(monster_names)}")
    
    # Return serialized data for XCom
    return [monster.model_dump() for monster in selected_monsters]


def fetch_monster_details_task(**context) -> List[Dict[str, Any]]:
    """
    Task to fetch detailed information for selected monsters.
    """
    # Pull data from previous task
    ti = context['ti']
    selected_monsters_data = ti.xcom_pull(task_ids='select_random_monsters')
    
    if not selected_monsters_data:
        raise ValueError("No selected monsters data received from select_random_monsters task")
    
    # Convert back to MonsterSummary objects
    selected_monsters = [MonsterSummary(**monster) for monster in selected_monsters_data]
    
    detailed_monsters = []
    
    for monster_summary in selected_monsters:
        try:
            logger.info(f"Fetching details for: {monster_summary.name}")
            raw_data = _client.fetch_monster_details(monster_summary.url)
            monster = _client.process_monster_data(raw_data)
            detailed_monsters.append(monster)
            logger.info(f"Processed {monster.name} - HP: {monster.hit_points}")
        except Exception as e:
            logger.error(f"Failed to process {monster_summary.name}: {e}")
            continue
    
    logger.info(f"Successfully processed {len(detailed_monsters)} monsters")
    
    # Return serialized data for XCom
    return [monster.model_dump() for monster in detailed_monsters]


def save_monsters_task(**context) -> str:
    """
    Task to save monster data to JSON file.
    """
    # Get parameters from task configuration
    output_file = context.get('output_file', 'monsters.json')
    
    # Pull data from previous task
    ti = context['ti']
    monsters_data = ti.xcom_pull(task_ids='fetch_monster_details')
    
    if not monsters_data:
        raise ValueError("No monster data received from fetch_monster_details task")
    
    # Convert back to Monster objects
    monsters = [Monster(**monster) for monster in monsters_data]
    
    # Save to file
    saved_file = _client.save_monsters_to_json(monsters, output_file)
    
    return saved_file
