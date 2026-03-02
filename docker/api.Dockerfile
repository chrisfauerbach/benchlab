FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY benchlab/ benchlab/
COPY prompts/ prompts/
COPY config/ config/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "benchlab.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
