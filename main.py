# main.py (Phoenix Service)
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="RAE-Phoenix Architect API")

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "architect"}

@app.post("/design")
def design_task(task: dict):
    return {"status": "task_received", "action": "planning"}

if __name__ == "__main__":
    print("🏗️ RAE-Phoenix Architect ONLINE")
    uvicorn.run(app, host="0.0.0.0", port=8000)
