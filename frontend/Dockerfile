# Dockerfile pour le frontend Streamlit

FROM python:3.13-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY pyproject.toml uv.lock ./

# Installer uv et les dépendances
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-editable

# Copier le code source
COPY . .

EXPOSE 8501

# Configuration Streamlit
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_LOGGER_LEVEL=info

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD [".venv/bin/streamlit", "run", "ui/app.py"]
