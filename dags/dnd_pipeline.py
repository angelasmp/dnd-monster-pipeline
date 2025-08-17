from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
import os

# Get project root directory dynamically
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

default_args = {
    'owner': 'angelasmp',
    'depends_on_past': False,
    'start_date': datetime(2025, 8, 16),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Simplified DAG using BashOperator calling task functions - mais robusto
dag = DAG(
    'dnd_monster_pipeline',
    default_args=default_args,
    description='D&D Monster Pipeline - Clean Architecture',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['dnd', 'api', 'pipeline'],
)

# Base command setup for all tasks
base_cmd = f'cd {PROJECT_ROOT} && source .venv/bin/activate && export PYTHONPATH={PROJECT_ROOT}'

# Task 1: Fetch monsters using task function
fetch_monsters = BashOperator(
    task_id='fetch_monsters',
    bash_command=f'''{base_cmd} && python -c "
from src.pipeline.transformation.tasks import fetch_monsters_task
import json
print('🔄 Fetching ALL monsters from D&D API...')
result = fetch_monsters_task()  # Remove limit to fetch all monsters
print(f'✅ Task completed: Fetched {{len(result)}} monsters')
with open('/tmp/monsters_list.json', 'w') as f:
    json.dump(result, f)
"''',
    dag=dag,
)

# Task 2: Select random monsters using task function
select_random_monsters = BashOperator(
    task_id='select_random_monsters',
    bash_command=f'''{base_cmd} && python -c "
from src.pipeline.transformation.tasks import select_random_monsters_task
import json
print('🔄 Selecting random monsters...')
with open('/tmp/monsters_list.json', 'r') as f:
    monsters_data = json.load(f)
class MockTI:
    def xcom_pull(self, task_ids=None): return monsters_data
result = select_random_monsters_task(ti=MockTI(), count=5)
print(f'✅ Task completed: Selected {{len(result)}} random monsters')
with open('/tmp/selected_monsters.json', 'w') as f:
    json.dump(result, f)
"''',
    dag=dag,
)

# Task 3: Fetch monster details using task function
fetch_monster_details = BashOperator(
    task_id='fetch_monster_details',
    bash_command=f'''{base_cmd} && python -c "
from src.pipeline.transformation.tasks import fetch_monster_details_task
import json
print('🔄 Fetching detailed monster data...')
with open('/tmp/selected_monsters.json', 'r') as f:
    selected_data = json.load(f)
class MockTI:
    def xcom_pull(self, task_ids=None): return selected_data
result = fetch_monster_details_task(ti=MockTI())
print(f'✅ Task completed: Processed {{len(result)}} monsters with full details')
with open('/tmp/detailed_monsters.json', 'w') as f:
    json.dump(result, f)
"''',
    dag=dag,
)

# Task 4: Save monsters using task function
save_monsters = BashOperator(
    task_id='save_monsters',
    bash_command=f'''{base_cmd} && python -c "
from src.pipeline.transformation.tasks import save_monsters_task
import json, os
print('🔄 Saving monsters to JSON file...')
with open('/tmp/detailed_monsters.json', 'r') as f:
    detailed_data = json.load(f)
class MockTI:
    def xcom_pull(self, task_ids=None): return detailed_data
result = save_monsters_task(ti=MockTI(), output_file='monsters.json')
print(f'✅ Pipeline completed successfully: {{result}}')
# Cleanup
for f in ['/tmp/monsters_list.json', '/tmp/selected_monsters.json', '/tmp/detailed_monsters.json']:
    try: os.remove(f)
    except: pass
"''',
    dag=dag,
)

# Define task dependencies
fetch_monsters >> select_random_monsters >> fetch_monster_details >> save_monsters
