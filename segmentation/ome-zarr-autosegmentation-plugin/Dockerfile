# Build stage
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv pip install --system -e .

COPY . .

# Final stage
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

WORKDIR /app/src

ENTRYPOINT ["python3", "-m", "polus.images.segmentation.ome_zarr_autosegmentation"]
CMD ["--help"]