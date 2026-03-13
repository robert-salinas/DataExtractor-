FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install .

COPY . .

ENV PYTHONPATH=/app
ENV ALLOWED_ORIGINS=http://localhost:8001
EXPOSE 8001
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
