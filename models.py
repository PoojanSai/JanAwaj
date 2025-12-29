
from sqlalchemy import Column, Integer, String, Text
from database import Base

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    target_email = Column(String)   # 👈 ADD THIS
    status = Column(String, default="OPEN")
