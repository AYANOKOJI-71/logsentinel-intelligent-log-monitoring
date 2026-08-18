FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY apps ./apps
RUN pip install --no-cache-dir ".[streaming,search]"
EXPOSE 4300
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "4300"]
