FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Python package and dependencies first for layer caching.
COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

COPY thebe_core/ ./thebe_core/
COPY verticals/ ./verticals/
COPY migrations/ ./migrations/
COPY alembic.ini .
COPY docs/ ./docs/
COPY scripts/docker-entrypoint.sh /app/docker-entrypoint.sh

# Seed and uploads write under data/. Create those dirs before dropping root.
RUN groupadd -r creatortrust && useradd -r -g creatortrust creatortrust \
    && mkdir -p /app/data/uploads /app/data/packages \
    && chown -R creatortrust:creatortrust /app/data \
    && chmod 755 /app/docker-entrypoint.sh
USER creatortrust

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
CMD ["uvicorn", "thebe_core.api:app", "--host", "0.0.0.0", "--port", "8000"]
