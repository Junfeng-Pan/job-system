import yaml
import os
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# 加载配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "mysql-config.yaml")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)["mysql"]

DATABASE_URL = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset=utf8mb4"

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_name = Column(String(255), nullable=False)
    salary_range = Column(String(100))
    industry = Column(String(255))
    company_detail = Column(Text)
    raw_detail = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    # 关联关系
    features = relationship("JobFeature", back_populates="job", cascade="all, delete-orphan")
    profile_json = relationship("JobProfileJson", back_populates="job", uselist=False, cascade="all, delete-orphan")

class JobProfileJson(Base):
    __tablename__ = 'job_profiles_json'
    job_id = Column(BigInteger, ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True)
    profile_data = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    job = relationship("Job", back_populates="profile_json")

class JobFeature(Base):
    __tablename__ = 'job_features'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    feature_type = Column(Integer, nullable=False) # 1:S, 2:B, 3:Q, 4:G
    name = Column(String(255), nullable=False)
    evidence = Column(Text)

    job = relationship("Job", back_populates="features")

    __table_args__ = (
        Index('idx_feature_name', 'name'),
    )

from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
