# Dockerfile for WhatsApp ASK71 Bot

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    build-essential \
    libpq-dev \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Add uv to PATH (uv installer typically installs to ~/.local/bin)
ENV PATH="/root/.local/bin:${PATH}"

# Copy project files for better caching
# Copy application code
COPY . .

# Remove any existing .venv to avoid permission issues
RUN rm -rf .venv || true

# Install Python dependencies using uv
RUN uv sync



# Expose port
EXPOSE 80

RUN chmod +x start.sh

# Run the application
CMD ./start.sh

