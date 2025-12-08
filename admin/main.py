from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import sys
import os

# Ensure we can import from shared
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# With volume mapping shared might be in /app/shared or ../shared depending on how we run.
# In Docker with my proposed volume map: /app/shared. 
# But locally I am in /admin.
# Let's try to handle both or just assume /app/shared in docker.
if os.path.exists("/app/shared"):
    sys.path.append("/app")

from shared import models, schemas, database
from shared.database import engine, get_db
from auth import verify_password, create_access_token, get_password_hash

# Create Database Tables (if not exist)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pi Platform Admin")

from auth import oauth2_scheme

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Simple decode, in real app move to deps
    from jose import JWTError, jwt
    from auth import SECRET_KEY, ALGORITHM
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
             raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check existing
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

from routers import sites

app.include_router(sites.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Raspberry Pi Platform Admin API"}
