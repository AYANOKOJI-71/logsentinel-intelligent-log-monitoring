FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY apps ./apps
RUN pip install --no-cache-dir ".[streaming,search]"
CMD ["python", "-m", "apps.worker.run"]
