from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
import uuid
from redis import Redis
from rq import Queue

from shared import models, schemas, database
from shared.database import get_db
from auth import oauth2_scheme, verify_password
from jose import jwt
from auth import SECRET_KEY, ALGORITHM

# Dependency to get current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
             raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

router = APIRouter(
    prefix="/sites",
    tags=["sites"],
    responses={404: {"description": "Not found"}},
)

# Redis Connection for worker
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
q = Queue('deploy', connection=redis_conn)

SITES_DIR = os.getenv("SITES_DIR", "/platform/sites")

@router.get("/", response_model=List[schemas.SiteOut])
def read_sites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    sites = db.query(models.Site).offset(skip).limit(limit).all()
    return sites

@router.post("/", response_model=schemas.SiteOut)
def create_site_metadata(site: schemas.SiteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_site = db.query(models.Site).filter(models.Site.slug == site.slug).first()
    if db_site:
        raise HTTPException(status_code=400, detail="Site slug already registered")
    
    new_site = models.Site(
        slug=site.slug,
        display_name=site.display_name,
        domain=site.domain,
        visibility=site.visibility,
        owner_id=current_user.id,
        created_at=database.datetime.utcnow(),
        status="pending"
    )
    
    if site.site_password:
        from auth import get_password_hash
        new_site.password_hash = get_password_hash(site.site_password)
        
    db.add(new_site)
    db.commit()
    db.refresh(new_site)
    return new_site

@router.post("/{slug}/upload")
def upload_site_content(slug: str, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.slug == slug).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Verify ownership or admin
    if site.owner_id != current_user.id and current_user.role != 'admin':
         raise HTTPException(status_code=403, detail="Not authorized")

    upload_dir = os.path.join(SITES_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{slug}_{uuid.uuid4().hex[:8]}.zip")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Enqueue job
    job = q.enqueue('worker.tasks.deploy_site', site.id, file_path)
    
    site.status = "deploying"
    site.deployment_message = f"Job enqueued: {job.id}"
    db.commit()
    
    return {"status": "uploaded", "job_id": job.id}

@router.get("/{slug}", response_model=schemas.SiteOut)
def read_site(slug: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.slug == slug).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@router.delete("/{slug}")
def delete_site(slug: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.slug == slug).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    if site.owner_id != current_user.id and current_user.role != 'admin':
         raise HTTPException(status_code=403, detail="Not authorized")
         
    # Enqueue deletion job? Or just delete metadata and let a cleanup job handle files?
    # For now, immediate metadata delete, maybe enqueue file cleanup
    q.enqueue('worker.tasks.delete_site_files', site.slug)
    
    db.delete(site)
    db.commit()
    return {"status": "deleted"}
