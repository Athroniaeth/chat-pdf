FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the system dependencies
RUN apt-get update

# Set the working directory
WORKDIR /app

# Add the lock file to the image (and necessary files for uv sync)
COPY uv.lock /app/uv.lock

# UV need of this files to sync the dependencies
COPY README.md /app/README.md
COPY pyproject.toml /app/pyproject.toml
RUN mkdir /app/src/rag -p
RUN touch /app/src/rag/__init__.py

# Sync the Python dependencies
RUN uv sync --frozen --all-extras  --no-dev

# Add the api and static files
COPY ./src /app/src/
COPY public /app/public/
COPY .chainlit /app/.chainlit/

# Expose the port
EXPOSE 8000

# Run the Python application
CMD ["uv", "run", "src/rag"]