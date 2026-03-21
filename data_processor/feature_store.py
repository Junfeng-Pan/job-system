import sys
import os

# 确保能找到项目根目录下的模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mysql.database import SessionLocal, JobFeature
from llm_service.schemas import JobProfile

class FeatureStore:
    """负责将 LLM 提取的画像存入数据库"""

    @staticmethod
    def save_profile(job_id: int, profile: JobProfile):
        """
        保存单个岗位的画像特征
        :param job_id: 关联的 jobs.id
        :param profile: LLM 提取的 JobProfile Pydantic 对象
        """
        session = SessionLocal()
        try:
            features = []
            
            # 1. 存入 Skills (Type: 1)
            for s in profile.skills:
                features.append(JobFeature(job_id=job_id, feature_type=1, name=s.name, evidence=s.evidence))
                
            # 2. 存入 Thresholds (Type: 2)
            for t in profile.thresholds:
                features.append(JobFeature(job_id=job_id, feature_type=2, name=t.name, evidence=t.evidence))
                
            # 3. 存入 Professionalism (Type: 3)
            for p in profile.professionalism:
                features.append(JobFeature(job_id=job_id, feature_type=3, name=p.name, evidence=p.evidence))
            
            if features:
                session.bulk_save_objects(features)
                session.commit()
                # print(f"已为 Job ID {job_id} 保存 {len(features)} 条特征。")
            
        except Exception as e:
            session.rollback()
            print(f"保存特征失败 (Job ID {job_id}): {e}")
        finally:
            session.close()
