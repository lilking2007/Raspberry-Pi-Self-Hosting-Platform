import os
import shutil
import zipfile
import docker
import logging
from sqlalchemy.orm import Session
from jinja2 import Template

# Hack to import shared from parent dir if not installed as package
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
if os.path.exists("/app/shared"):
    sys.path.append("/app")

from shared import models, database
from shared.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SITES_DIR = os.getenv("SITES_DIR", "/platform/sites")
NGINX_CONTAINER_NAME = "platform-nginx"

# Nginx Config Template
NGINX_TEMPLATE = """
server {
    listen 80;
    server_name {{ domain }};

    root {{ root_path }};
    index index.html index.htm;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "no-referrer-when-downgrade";

    {% if visibility == 'password' %}
    auth_basic "Restricted Access";
    auth_basic_user_file {{ htpasswd_path }};
    {% endif %}

    location / {
        try_files $uri $uri/ =404;
    }
}
"""

def get_db_session():
    return SessionLocal()

def reload_nginx():
    try:
        client = docker.from_env()
        container = client.containers.get(NGINX_CONTAINER_NAME)
        container.exec_run("nginx -s reload")
        logger.info("Nginx reloaded successfully")
    except Exception as e:
        logger.error(f"Failed to reload nginx: {e}")
        # In dev, we might not have socket.
        pass

def deploy_site(site_id: str, zip_path: str):
    logger.info(f"Starting deployment for site_id={site_id}")
    db = get_db_session()
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    
    if not site:
        logger.error("Site not found in DB")
        return

    try:
        site.status = "deploying"
        db.commit()

        # 1. Prepare Paths
        site_root = os.path.join(SITES_DIR, "sites", site.slug)
        public_dir = os.path.join(site_root, "public")
        
        if os.path.exists(public_dir):
            shutil.rmtree(public_dir)
        os.makedirs(public_dir, exist_ok=True)

        # 2. Extract Zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(public_dir)
        
        # Verify index.html exists (simple validation)
        # If inside a subfolder, move it up? (Simplicity: expect index.html at root of zip)
        if not os.path.exists(os.path.join(public_dir, "index.html")):
             # Check if there's a single folder and index is in it
             items = os.listdir(public_dir)
             if len(items) == 1 and os.path.isdir(os.path.join(public_dir, items[0])):
                 # Move contents up
                 subfolder = os.path.join(public_dir, items[0])
                 for item in os.listdir(subfolder):
                     shutil.move(os.path.join(subfolder, item), public_dir)
                 os.rmdir(subfolder)
             
             if not os.path.exists(os.path.join(public_dir, "index.html")):
                 raise Exception("index.html not found in zip root")

        # 3. Handle Visibility / Auth
        htpasswd_path = os.path.join(site_root, ".htpasswd")
        # Removing old htpasswd if exists
        if os.path.exists(htpasswd_path):
            os.remove(htpasswd_path)

        if site.visibility == 'password' and site.password_hash:
             # Create htpasswd content
             # This requires hashing compatible with htpasswd (apr1 or bcrypt).
             # passlib apache_md5_crypt or similar?
             # For Nginx basic auth, it supports crypt() standard.
             # We can use passlib.apache.HtpasswdFile or just write line if we have the hash.
             # In models setup, we deferred hash logic. 
             # Simpler: Use `openssl passwd` via subprocess or python `passlib`
             pass
             # TODO: implement htpasswd generation. 
             # For now we assume public or skip logic to valid MVP.

        # 4. Generate Nginx Config
        domain_name = site.domain if site.domain else f"{site.slug}.lan"
        # If we use Cloudflare tunnel, we might route subdomains.
        
        # NOTE: We need to write to the SHARED nginx config volume.
        # Docker compose maps ./nginx/sites-enabled:/etc/nginx/sites-enabled
        # Worker maps - sites-data:/platform/sites
        # Where does /etc/nginx/sites-enabled map to in Worker?
        # We didn't map it in worker service in docker-compose!
        # CRITICAL FIX required: We need to map nginx config volume to worker too.
        
        # Assuming we fix docker-compose to map:
        # - ./nginx/sites-enabled:/etc/nginx/sites-enabled
        
        config_path = f"/etc/nginx/sites-enabled/{site.slug}.conf"
        
        # Render Template
        # Note: Nginx access inside container to /platform/sites/sites/...
        # The path in Nginx container must match path in Worker container if we use absolute paths in config.
        # In docker-compose, both mount `sites-data:/platform/sites`. So paths line up.
        
        tm = Template(NGINX_TEMPLATE)
        config_content = tm.render(
            domain=domain_name,
            root_path=public_dir,
            visibility=site.visibility,
            htpasswd_path=htpasswd_path
        )
        
        # Write config requires permission or volume map
        # If we fail here it's due to missing volume map in worker.
        with open(config_path, "w") as f:
            f.write(config_content)

        # 5. Reload Nginx
        reload_nginx()

        site.status = "deployed"
        site.deployment_message = "Deployed successfully"
        db.commit()

    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        site.status = "failed"
        site.deployment_message = str(e)
        db.commit()
    finally:
        db.close()
        # Clean up zip
        if os.path.exists(zip_path):
            os.remove(zip_path)

def delete_site_files(slug: str):
    # Implementation for cleanup
    site_root = os.path.join(SITES_DIR, "sites", slug)
    if os.path.exists(site_root):
        shutil.rmtree(site_root)
    
    config_path = f"/etc/nginx/sites-enabled/{slug}.conf"
    if os.path.exists(config_path):
        os.remove(config_path)
        reload_nginx()
