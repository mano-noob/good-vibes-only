FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY runtime_paths.py ./runtime_paths.py

RUN mkdir -p /app/data /app/logs

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host \"${API_HOST:-0.0.0.0}\" --port \"${API_PORT:-8000}\""]