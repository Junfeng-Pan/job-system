import pandas as pd
import numpy as np
import os
import sys

# 确保能找到 mysql 模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mysql.database import SessionLocal, Job

def load_jobs_from_csv(csv_path: str):
    """读取清洗后的 CSV 并存入数据库"""
    if not os.path.exists(csv_path):
        print(f"错误: 找不到文件 {csv_path}")
        return

    # 读取数据
    df = pd.read_csv(csv_path)
    
    # 核心修复：转换为纯 Python 字典列表，并确保 NaN 被替换为 None
    # 使用 to_dict('records') 可以完全脱离 Pandas 的数据类型自动转换逻辑
    records = df.replace({np.nan: None}).to_dict(orient='records')
    
    session = SessionLocal()
    
    print(f"--- [岗位入库] 开始处理 {len(records)} 条记录 ---")
    
    try:
        new_jobs = []
        for row in records:
            job = Job(
                job_name=row.get('岗位名称'),
                salary_range=row.get('薪资范围'),
                industry=row.get('所属行业'),
                company_detail=row.get('公司详情'),
                raw_detail=row.get('岗位详情')
            )
            new_jobs.append(job)
        
        session.bulk_save_objects(new_jobs)
        session.commit()
        print(f"成功导入 {len(new_jobs)} 条岗位信息到 jobs 表。")
    except Exception as e:
        session.rollback()
        print(f"导入失败: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    csv_file = os.path.join(BASE_DIR, "data", "cleaned_job_data.csv")
    load_jobs_from_csv(csv_file)
