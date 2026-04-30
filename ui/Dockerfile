FROM python:3.11-slim AS builder

WORKDIR /app

COPY ./ui/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

RUN mkdir -p uploads && chmod 777 uploads


FROM python:3.11-slim 

WORKDIR /app


COPY --from=builder /root/.local /root/.local

COPY --from=builder /app/uploads ./uploads

COPY ./ui/app .

ENV PATH=/root/.local/bin:$PATH
ENV - PYTHONDONTWRITEBYTECODE=1
ENV - PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]