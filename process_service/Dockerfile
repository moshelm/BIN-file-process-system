FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY /process_service/requirements.txt .

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY ./process_service ./process_service
COPY ./shared ./shared

ENV PATH="/opt/venv/bin:$PATH"


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["uvicorn", "process_service.src.main:app", "--host", "0.0.0.0", "--port", "8001"]
