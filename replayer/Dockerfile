FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY replay.py .

# -u = unbuffered, so logs appear live in `docker compose logs`
CMD ["python", "-u", "replay.py"]
