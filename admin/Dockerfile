FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
# We assume the build context in docker-compose involves the root, or we copy specifically.
# In the docker-compose I set:
# build: 
#   context: ./admin
# which means it cannot access ../shared unless I change the context to .. or copy shared into admin during build.
# Changing strategy: I will update docker-compose to use root context for build, OR I will just rely on mapped volumes for dev.
# But for a proper build, the context should be the root.
# Let's handle this by changing the build context in docker-compose later.
# For now, I will assume the context is the project root, so I can COPY shared /app/shared
# WAIT: If I change context to root, I need to copy admin/requirements.txt specifically.
# Let's adjust this Dockerfile to assume it is run from the PROJECT ROOT context.

# COPY admin/requirements.txt .
# RUN pip install ...
# COPY admin /app/
# COPY shared /app/shared

# However, the standard way is keeping context localized. 
# A common trick is to mount shared or use a multi-stage build or copy it in via a script.
# For simplicity in this dev environment, I will rely on the volume mount in docker-compose.
# `volumes: - ./admin:/app` will overwrite /app.
# So I need to mount shared as well in docker-compose.
# `- ./shared:/app/shared`

# So the Dockerfile is mainly for dependencies.

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
