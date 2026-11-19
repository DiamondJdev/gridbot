FROM ghcr.io/astral-sh/uv:0.9.5 AS uv
FROM python:3.12-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /workspace
COPY pyproject.toml uv.lock .python-version ./
COPY core/ core/
COPY runner/ runner/
RUN uv sync --locked --no-dev --no-editable --no-cache
COPY assets/ assets/
COPY config/ config/
COPY scenarios/ scenarios/
ENV PATH="/workspace/.venv/bin:$PATH"
USER nobody
CMD ["gridbot-run", "scenarios/drive-01.json", "--serve", "--host", "0.0.0.0", "--port", "8765"]
