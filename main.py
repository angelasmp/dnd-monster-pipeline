#!/usr/bin/env python3
"""
D&D Monster Pipeline - Challenge Implementation
===============================================

Author: angelasmp
"""

import sys
import logging
from pathlib import Path

# Import task functions (elimina redundância)
from src.pipeline.transformation.tasks import (
    fetch_monsters_task,
    select_random_monsters_task, 
    fetch_monster_details_task,
    save_monsters_task
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Main entrypoint for direct pipeline execution using task functions."""
    logger.info("D&D Monster Pipeline - Direct Execution")
    logger.info("=" * 50)
    logger.info("Using same task functions as Airflow DAG")
    logger.info("=" * 50)
    
    # Check if output already exists (idempotency)
    output_file = Path('monsters.json')
    if output_file.exists():
        logger.info("monsters.json already exists - pipeline is idempotent")
        logger.info("Skipping execution to avoid re-fetching data")
        logger.info(f"File size: {output_file.stat().st_size} bytes")
        logger.info("Delete monsters.json to force re-execution")
        return 0
    
    try:
        # Step 1: Fetch ALL monsters using task function (no limit for true randomness)
        monsters_data = fetch_monsters_task()  # Remove limit=20 to fetch all monsters
        
        # Step 2: Select random monsters using task function
        class MockTI:
            def xcom_pull(self, task_ids=None): return monsters_data
        selected_data = select_random_monsters_task(ti=MockTI(), count=5)
        
        # Step 3: Fetch detailed data using task function
        class MockTI2:
            def xcom_pull(self, task_ids=None): return selected_data
        detailed_data = fetch_monster_details_task(ti=MockTI2())
        
        # Step 4: Save to JSON using task function
        class MockTI3:
            def xcom_pull(self, task_ids=None): return detailed_data
        saved_file = save_monsters_task(ti=MockTI3(), output_file='monsters.json')
        
        # Success summary
        logger.info(f"\n Challenge completed successfully!")
        logger.info(f"Generated {len(detailed_data)} monsters in {saved_file}")
        return 0
        
    except Exception as e:
        logger.error(f" Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
