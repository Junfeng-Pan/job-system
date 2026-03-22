from mysql.database import SessionLocal, JobFeature, JobProfileJson
from llm_service.schemas import JobProfile
import json

class FeatureStore:
    """负责将 LLM 提取的画像数据持久化到 MySQL"""

    def save_profile(self, job_id: int, profile: JobProfile):
        """
        保存画像数据：同时保存到特征表(用于匹配)和 JSON 表(用于展示)
        """
        session = SessionLocal()
        try:
            # 1. 保存到 job_profiles_json 表 (1对1)
            # 转换为 dict 存入 JSON 字段
            profile_dict = profile.model_dump()
            
            # 检查是否已存在（Upsert 逻辑）
            existing_json = session.query(JobProfileJson).filter_by(job_id=job_id).first()
            if existing_json:
                existing_json.profile_data = profile_dict
            else:
                new_json = JobProfileJson(job_id=job_id, profile_data=profile_dict)
                session.add(new_json)

            # 2. 保存到 job_features 表 (多对1)
            # 先删除该岗位旧的特征，实现覆盖更新
            session.query(JobFeature).filter_by(job_id=job_id).delete()
            
            features_to_add = []
            
            # 处理 Skills (Type 1)
            for s in profile.skills:
                features_to_add.append(JobFeature(job_id=job_id, feature_type=1, name=s.name, evidence=s.evidence))
            
            # 处理 Thresholds (Type 2)
            for b in profile.thresholds:
                features_to_add.append(JobFeature(job_id=job_id, feature_type=2, name=b.name, evidence=b.evidence))
                
            # 处理 Professionalism (Type 3)
            for q in profile.professionalism:
                features_to_add.append(JobFeature(job_id=job_id, feature_type=3, name=q.name, evidence=q.evidence))

            if features_to_add:
                session.bulk_save_objects(features_to_add)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"保存特征失败 (Job ID {job_id}): {e}")
        finally:
            session.close()
