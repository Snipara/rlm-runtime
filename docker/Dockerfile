# RLM Runtime Docker Image
# Used for isolated REPL execution

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd --gid 1000 rlm && \
    useradd --uid 1000 --gid rlm --shell /bin/bash --create-home rlm

# Install minimal dependencies for common data processing
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    pyyaml \
    toml

# Create workspace directory
WORKDIR /workspace

# Switch to non-root user
USER rlm

# Default command (can be overridden)
CMD ["python"]
