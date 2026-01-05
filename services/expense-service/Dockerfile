FROM python:3.11-slim 

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 

WORKDIR /app 

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    netcat-openbsd \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv 
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt . 
RUN uv pip install --system -r requirements.txt

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY . . 

EXPOSE 8002

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["uvicorn", "tracker.main:app", "--host", "0.0.0.0", "--port", "8002"]
# CMD ["uvicorn", "tracker.main:app", "--host", "0.0.0.0", "--port", "8000" "--reload"]  # --reload only in development