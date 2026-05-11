# Deployment Guide

This document covers deployment strategies, Docker usage, CI/CD, and production considerations for Snipara Sandbox.

## Table of Contents

- [Overview](#overview)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Serverless Deployment](#serverless-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Production Checklist](#production-checklist)
- [Monitoring](#monitoring)
- [Scaling](#scaling)

---

## Overview

Snipara Sandbox can be deployed in various environments:

| Environment | Use Case | Isolation |
|-------------|----------|-----------|
| Local | Development | Limited |
| Docker | Production, untrusted code | Full |
| WebAssembly | Serverless, browser | Full |

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│  Snipara Sandbox Pod  │  │  Snipara Sandbox Pod  │  │  Snipara Sandbox Pod  │
│  (Docker) │  │  (Docker) │  │  (Docker) │
└───────────┘  └───────────┘  └───────────┘
        │             │             │
        └─────────────┼─────────────┘
                      ▼
        ┌───────────────────────────────┐
        │     Shared Storage (Logs)     │
        └───────────────────────────────┘
```

---

## Docker Deployment

### Basic Docker Setup

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Snipara Sandbox
RUN pip install snipara-sandbox[docker,mcp]

# Copy entrypoint
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["mcp-serve"]
```

```bash
# Build image
docker build -t snipara-sandbox:latest .

# Run container
docker run -d \
  --name snipara-sandbox \
  -p 8080:8080 \
  -e SNIPARA_SANDBOX_MODEL=gpt-4o \
  -e SNIPARA_SANDBOX_ENVIRONMENT=docker \
  -v snipara-sandbox-logs:/app/logs \
  snipara-sandbox:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  snipara-sandbox:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SNIPARA_SANDBOX_MODEL=gpt-4o
      - SNIPARA_SANDBOX_ENVIRONMENT=docker
      - SNIPARA_SANDBOX_LOG_DIR=/app/logs
      - SNIPARA_SANDBOX_DOCKER_MEMORY=1g
      - SNIPARA_SANDBOX_DOCKER_CPUS=2.0
      - SNIPARA_API_KEY=${SNIPARA_API_KEY}
      - SNIPARA_PROJECT_SLUG=${SNIPARA_PROJECT_SLUG}
    volumes:
      - snipara-sandbox-logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    healthcheck:
      test: ["CMD", "snipara-sandbox", "doctor"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  snipara-sandbox-logs:
```

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f snipara-sandbox

# Stop services
docker-compose down
```

### Production Docker Image

```dockerfile
# Production-optimized Dockerfile
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Build and install Snipara Sandbox
RUN pip install --no-cache-dir \
    --prefix=/install \
    snipara-sandbox[docker,mcp,visualizer]

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /install /usr/local

# Create non-root user
RUN useradd -m snipara && chown -R snipara:snipara /app
USER snipara

# Default environment
ENV SNIPARA_SANDBOX_ENVIRONMENT=docker \
    SNIPARA_SANDBOX_LOG_DIR=/app/logs \
    SNIPARA_SANDBOX_DOCKER_MEMORY=512m \
    SNIPARA_SANDBOX_DOCKER_CPUS=1.0

# Create log directory
RUN mkdir -p /app/logs && chown snipara:snipara /app/logs

EXPOSE 8080

CMD ["mcp-serve"]
```

---

## Kubernetes Deployment

### Deployment Config

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: snipara-sandbox
  labels:
    app: snipara-sandbox
spec:
  replicas: 3
  selector:
    matchLabels:
      app: snipara-sandbox
  template:
    metadata:
      labels:
        app: snipara-sandbox
    spec:
      serviceAccountName: snipara-sandbox
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: snipara-sandbox
        image: snipara-sandbox:latest
        ports:
        - containerPort: 8080
        env:
        - name: SNIPARA_SANDBOX_MODEL
          value: "gpt-4o"
        - name: SNIPARA_SANDBOX_ENVIRONMENT
          value: "docker"
        - name: SNIPARA_SANDBOX_LOG_DIR
          value: "/app/logs"
        - name: SNIPARA_API_KEY
          valueFrom:
            secretKeyRef:
              name: snipara-sandbox-secrets
              key: snipara-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        livenessProbe:
          exec:
            command: ["snipara-sandbox", "doctor"]
          initialDelaySeconds: 30
          periodSeconds: 60
        readinessProbe:
          exec:
            command: ["snipara-sandbox", "doctor"]
          initialDelaySeconds: 10
          periodSeconds: 30
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: snipara-sandbox-logs-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: snipara-sandbox-service
spec:
  selector:
    app: snipara-sandbox
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

### HPA (Horizontal Pod Autoscaler)

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: snipara-sandbox-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: snipara-sandbox
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Serverless Deployment

### AWS Lambda

```python
# lambda/handler.py
import json
from snipara_sandbox import SniparaSandbox
import asyncio

# Cold start initialization
sandbox = SniparaSandbox(
    model="gpt-4o-mini",
    environment="docker",
)

async def handler(event, context):
    """Lambda handler for Snipara Sandbox."""
    try:
        prompt = event.get("prompt", "")
        result = await sandbox.completion(prompt)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "response": result.response,
                "trajectory_id": str(result.trajectory_id),
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

# For Lambda with Docker
# Use AWS Lambda Container Image Support
```

### Google Cloud Functions

```python
# main.py
from snipara_sandbox import SniparaSandbox
import asyncio

sandbox = None

def init_sandbox():
    global sandbox
    if sandbox is None:
        sandbox = SniparaSandbox(
            model="gpt-4o-mini",
            environment="docker",
        )

def completion(request):
    init_sandbox()

    request_json = request.get_json(silent=True)
    prompt = request_json.get("prompt", "")

    result = asyncio.run(sandbox.completion(prompt))

    return {"response": result.response}
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: Deployment environment
        required: true
        default: staging
        type: choice
        options:
        - staging
        - production

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
        pip install snipara-sandbox[docker]

    - name: Run tests
      run: pytest

    - name: Lint
      run: |
        ruff check src/
        mypy src/

    - name: Build Docker image
      run: |
        docker build -t snipara-sandbox:${{ github.sha }} .
        docker tag snipara-sandbox:${{ github.sha }} snipara-sandbox:latest

  deploy-staging:
    needs: test
    if: github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'staging'
    runs-on: ubuntu-latest
    environment: staging
    steps:
    - name: Deploy to staging
      run: |
        # Push to registry
        docker push registry.example.com/snipara-sandbox:${{ github.sha }}

        # Update Kubernetes
        kubectl set image deployment/snipara-sandbox \
          snipara-sandbox=registry.example.com/snipara-sandbox:${{ github.sha }} \
          -n staging

  deploy-production:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
    - name: Deploy to production
      run: |
        # Wait for staging validation
        echo "Deployment to production requires manual approval"
        # This would typically use a manual approval step in GitHub Actions
```

---

## Production Checklist

### Security

- [ ] Use API keys from secrets manager
- [ ] Enable Docker network isolation (`docker_network_disabled=true`)
- [ ] Restrict file access with `allowed_paths`
- [ ] Use non-root user in containers
- [ ] Enable TLS for MCP server
- [ ] Rotate API keys regularly
- [ ] Audit logs for sensitive data

### Performance

- [ ] Set appropriate `max_depth` and `token_budget`
- [ ] Configure `max_parallel` based on workload
- [ ] Use Docker memory limits to prevent OOM
- [ ] Enable logging for debugging
- [ ] Monitor token usage and costs
- [ ] Use caching where appropriate

### Reliability

- [ ] Set appropriate timeouts
- [ ] Configure retry logic for API calls
- [ ] Set up health checks
- [ ] Configure log rotation
- [ ] Set up alerts for errors
- [ ] Backup trajectory logs

### Monitoring

```bash
# Key metrics to monitor
- Request latency (p50, p95, p99)
- Error rate
- Token usage per request
- Cost per day
- Container memory/CPU
- Queue depth (if async)
```

---

## Monitoring

### Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, start_http_server

# Start metrics server
start_http_server(8000)

# Define metrics
REQUEST_COUNT = Counter('snipara_sandbox_requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('snipara_sandbox_request_duration_seconds', 'Request latency')
TOKEN_USAGE = Histogram('snipara_sandbox_tokens_used_total', 'Tokens per request')
COST_USAGE = Counter('snipara_sandbox_cost_usd_total', 'Total cost in USD')
```

### Health Checks

```bash
# Check health
curl http://localhost:8080/health

# Response
{
  "status": "healthy",
  "version": "2.0.0",
  "components": {
    "llm": "healthy",
    "repl": "healthy",
    "storage": "healthy"
  }
}
```

### Logging

```python
# Structured logging with structlog
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.RealLogger,
)

log = structlog.get_logger()
```

---

## Scaling

### Horizontal Scaling

1. **Load Balancer** - Distribute requests across Snipara Sandbox pods
2. **Stateless Design** - No shared state between requests
3. **Shared Storage** - Use S3 or similar for trajectory logs
4. **Connection Pooling** - For database-backed features

### Vertical Scaling

1. **Increase Memory** - For larger code execution
2. **Increase CPU** - For parallel tool execution
3. **GPU Support** - If using GPU-accelerated models

### Request Queuing

```python
# Use a queue for high-load scenarios
import asyncio
from redis import Redis
from rq import Queue

redis = Redis()
queue = Queue('snipara-sandbox-tasks', connection=redis)

def process_completion(prompt, **kwargs):
    sandbox = SniparaSandbox(**kwargs)
    result = asyncio.run(sandbox.completion(prompt))
    return result

# Enqueue task
job = queue.enqueue(
    process_completion,
    "Your prompt here",
    model="gpt-4o-mini",
)
```
