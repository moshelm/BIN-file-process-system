FROM python:3.13-slim AS builder

WORKDIR /build

COPY /process-service/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY ./process-service/app .


ENV PATH=/root/.local/bin:$PATH

ENV - PYTHONDONTWRITEBYTECODE=1
ENV - PYTHONUNBUFFERED=1
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]