FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn mcp requests pydantic

COPY . .

ENV PYTHONPATH=/app

CMD ["python", "main.py"]
