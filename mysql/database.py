from sqlalchemy import create_engine, Column, BigInteger, String, Text, Integer, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import yaml
import os

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_name = Column(String(255), nullable=False)
    salary_range = Column(String(100))
    industry = Column(String(255))
    company_detail = Column(Text)
    raw_detail = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # 关联特征
    features = relationship("JobFeature", back_populates="job", cascade="all, delete-orphan")

class JobFeature(Base):
    __tablename__ = 'job_features'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    feature_type = Column(Integer, nullable=False)  # 1:Skills, 2:Thresholds, 3:Professionalism
    name = Column(String(255), nullable=False)
    evidence = Column(Text)
    
    job = relationship("Job", back_populates="features")

def get_engine():
    """从配置文件加载参数并创建引擎"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "mysql-config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)['mysql']
    
    db_url = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config['charset']}"
    return create_engine(db_url, echo=False)

SessionLocal = sessionmaker(bind=get_engine())
