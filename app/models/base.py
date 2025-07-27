import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def default_uuid():
    return str(uuid.uuid4())

def timestamp():
    return datetime.now(timezone.utc)
