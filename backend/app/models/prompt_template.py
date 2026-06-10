from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
