import httpx
import json
import sys
import os

RAE_API_URL = os.getenv('RAE_API_URL', 'http://localhost:8001/v2/memories/')

def dispatch(recipe_path):
    print(f"[FENIKS] Loading recipe from {recipe_path}...")
    with open(recipe_path, 'r') as f:
        recipe_content = f.read()
    
    objective = {
        "content": f"Refactor task based on recipe: {recipe_content}",
        "metadata": {
            "project": "RAE-Feniks",
            "source": "feniks-dispatcher",
            "type": "objective"
        },
        "layer": "semantic",
        "tags": ["hive_objective", "pending", "refactor"]
    }
    
    print(f"[FENIKS] Dispatching objective to RAE-Core at {RAE_API_URL}...")
    response = httpx.post(RAE_API_URL, json=objective)
    if response.status_code == 200:
        print(f"[FENIKS] SUCCESS! Objective ID: {response.json().get('memory_id')}")
    else:
        import sys
        arg = sys.argv[1]
        if arg.startswith("--mission="):
            arg = arg.split("=")[1]
        elif arg == "--mission" and len(sys.argv) > 2:
            arg = sys.argv[2]
        dispatch(arg)
