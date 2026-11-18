from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, SessionLocal, engine, get_db
from .models import User
from .schemas import LoginIn, TokenOut, UserCreate, UserOut, UserUpdate
from .security import create_token, hash_password, require_admin, verify_password
from .storage import delete_object, image_url, upload_profile


def serialize(user: User) -> UserOut:
    data = UserOut.model_validate(user)
    return data.model_copy(update={"image_url": image_url(user.image_key)})


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if not admin:
            db.add(User(full_name="Administrador", email=settings.admin_email.lower(), password_hash=hash_password(settings.admin_password), role="admin"))
            db.commit()
    yield


app = FastAPI(title="Administración de usuarios en AWS", lifespan=lifespan)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not user.active or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Credenciales incorrectas")
    if user.role != "admin":
        raise HTTPException(403, "El usuario no es administrador")
    return TokenOut(access_token=create_token(user))


@app.get("/api/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [serialize(u) for u in db.scalars(select(User).order_by(User.id)).all()]


@app.post("/api/users", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = User(full_name=body.full_name.strip(), email=body.email.lower(), password_hash=hash_password(body.password), role=body.role, active=body.active)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "El correo ya existe")
    db.refresh(user)
    return serialize(user)


@app.put("/api/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    changes = body.model_dump(exclude_unset=True)
    if "email" in changes:
        changes["email"] = str(changes["email"]).lower()
    if "password" in changes:
        changes["password_hash"] = hash_password(changes.pop("password"))
    for key, value in changes.items():
        setattr(user, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "El correo ya existe")
    db.refresh(user)
    return serialize(user)


@app.post("/api/users/{user_id}/image", response_model=UserOut)
def set_image(user_id: int, file: UploadFile = File(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    old_key = user.image_key
    user.image_key = upload_profile(file, user_id)
    db.commit()
    db.refresh(user)
    delete_object(old_key)
    return serialize(user)


@app.delete("/api/users/{user_id}", status_code=204)
def remove_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise HTTPException(409, "No puede eliminar su propia cuenta")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    key = user.image_key
    db.delete(user)
    db.commit()
    delete_object(key)
