FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules (assumes build context is root or we handle it via volume in dev)
# For production build, context must be root.
# COPY shared /app/shared
# COPY worker /app/

COPY . .

# Default command to run RQ worker
# We need to point to where the tasks are defined.
# If tasks are in `tasks.py`, we run `rq worker -u $REDIS_URL deploy`
CMD ["rq", "worker", "--url", "redis://redis:6379/0", "deploy"]
