FROM python:3.11-slim AS builder

WORKDIR /app

COPY ./ui/requirements.txt .

RUN mkdir -p uploads && chmod 777 uploads

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim 

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv

COPY --from=builder /app/uploads ./uploads

COPY ./ui ./ui
COPY ./shared ./shared

ENV - PYTHONDONTWRITEBYTECODE=1
ENV - PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "ui.src.main"]
