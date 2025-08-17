# 🐉 D&D Monster Pipeline Challenge

A simple **data pipeline** that fetches monster data from the D&D 5e API using Apache Airflow orchestration.

---

## 🎯 Challenge Summary

Create an **orchestrated data pipeline** that:

1. Fetches **ALL monster data** from the [DnD API](https://www.dnd5eapi.co/api/2014/) (334 monsters available)
2. Selects 5 **random monsters** from the entire dataset (examples may include):
   - **Goblin**
   - **Skeleton** 
   - **Barbed Devil**
   - **Dretch**
   - **Warhorse**
   - **Or any other monsters** from the full collection
3. Extracts only the following fields using `url` attribute to fetch details:
   - `name`
   - `hit_points`
   - `armor_class`
   - `actions` (only the name and description of each)
4. Outputs the final data as a structured JSON file

---

## 📦 Structure

```
├── src/pipeline/          # Core pipeline code
├── dags/                  # Airflow DAG
├── main.py                # Run directly
├── Dockerfile             # Container
└── monsters.json          # Output
```

---

## 🚀 Run Options

### 1. Install Dependencies
```bash
# Create virtual environment 
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Direct (Fastest)
```bash
# If using virtual environment:
source .venv/bin/activate && python main.py

# Or direct:
python3 main.py
```

### 3. Airflow (Full Pipeline)
```bash
# Setup everything (DB, user, services)
./setup_airflow.sh

# Access UI: http://localhost:8080
# Login: admin / admin
# Run DAG: dnd_monster_pipeline

# Stop services
./stop_airflow.sh

# Complete reset (if needed)
./reset_airflow.sh
```

**Pipeline Architecture:**
The DAG consists of 4 individual tasks:
1. **fetch_monsters**: Fetches first 20 monsters from D&D API
2. **select_random_monsters**: Selects 5 random monsters
3. **fetch_monster_details**: Gets detailed data for each monster
4. **save_monsters**: Saves final JSON output

**Note**: The setup script automatically creates the admin user with credentials `admin/admin`. If you encounter any login issues, use `./reset_airflow.sh` followed by `./setup_airflow.sh` to start completely fresh.

### 4. Docker Container
```bash
# Build and run (saves monsters.json to repository)
docker build -t dnd-monster-pipeline .
docker run --rm -v "$(pwd):/app" dnd-monster-pipeline
```

### 5. Unit Tests
```bash
# Run all tests
./run_tests.sh

# Or manually with pytest
pytest tests/ -v

# Test coverage includes:
# - Pydantic models validation
# - API client functionality  
# - Task functions
# - Integration tests
# - Error handling
```

---

## 📊 Example Output

```json
[
  {
    "name": "Goblin",
    "hit_points": 7,
    "armor_class": 15,
    "actions": [
      {
        "name": "Scimitar",
        "desc": "Melee Weapon Attack: +4 to hit..."
      }
    ]
  }
]
```

---

## 📝 Notes

- **Python Requirements**: Python 3.9+ with pip (virtual environment recommended)
- **Airflow Setup**: Run `airflow db init` and create admin user before starting services
- **Database**: SQLite database will be created automatically in `airflow_home/`
- **DAGs folder**: Contains our pipeline DAG (`dnd_pipeline.py`)
- **Login Credentials**: admin/admin (created during setup)
- **Docker**: Use volume mount `-v "$(pwd):/app"` to save output to repository
- **Idempotent**: Pipeline skips re-execution if `monsters.json` already exists

## 🛠️ Helper Scripts

- **`./setup_airflow.sh`** - Automated Airflow setup (recommended)
- **`./stop_airflow.sh`** - Clean shutdown of Airflow services
- **`./reset_airflow.sh`** - Completely resets the Airflow environment
- **`./run_tests.sh`** - Run unit tests with pytest

---

**Status**: ✅ Complete & Ready
