# Read-only DELTA presentation API for Render (Docker runtime).
# Build context = repository root. Dữ liệu (Git-ignored) được tải từ HF Dataset lúc build;
# TerminalRepository/IndicatorReferences vẫn kiểm tra hash lúc startup và fail-closed nếu sai.
FROM python:3.12-slim

ARG DATA_BASE_URL=https://huggingface.co/datasets/ngyen/delta-intelligence-data/resolve/main
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONPATH=/app/web/backend \
    DELTA_BUNDLE=/app/data/web/delta-intelligence-v2

WORKDIR /app
COPY web/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY deploy/render/data-files.txt deploy/render/fetch_data.py /tmp/
RUN python /tmp/fetch_data.py /tmp/data-files.txt /app

COPY web/backend/app /app/web/backend/app
COPY configs/product /app/configs/product

EXPOSE 10000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]
