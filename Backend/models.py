from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, Float, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

class Mark(Base):
    """One row = one student's score + attendance on a topic in one exam."""
    __tablename__ = "marks"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    exam_no: Mapped[int] = mapped_column(Integer)   # 1, 2, 3... (time order)
    score: Mapped[float] = mapped_column(Float)      # out of 100
    attendance: Mapped[float] = mapped_column(Float) # percent

class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    title: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(300))

class Paper(Base):
    __tablename__ = "question_papers"
    id: Mapped[int] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/approved/rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    questions: Mapped[list["Question"]] = relationship(cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("question_papers.id"))
    text: Mapped[str] = mapped_column(Text)
    bloom_level: Mapped[str] = mapped_column(String(20))
    marks: Mapped[int] = mapped_column(Integer)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(50))
    entity: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(Integer)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
