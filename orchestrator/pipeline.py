import sys
import os
import time
from tqdm import tqdm

# 确保能找到项目根目录下的模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mysql.database import SessionLocal, Job, JobFeature
from llm_service.extractor import JobExtractor
from data_processor.feature_store import FeatureStore

class JobOrchestrator:
    """
    任务调度与控制模块 (Orchestrator)
    负责从数据库读取原始数据，调用 LLM 抽取，并存入特征表。
    """

    def __init__(self):
        self.extractor = JobExtractor()
        self.store = FeatureStore()

    def run_pipeline(self, limit: int = 10, skip_processed: bool = True):
        """
        执行完整处理流水线
        :param limit: 本次运行处理的记录上限
        :param skip_processed: 是否跳过已经在 job_features 中有记录的岗位
        """
        session = SessionLocal()
        
        print(f"--- [任务调度开始] 处理上限: {limit} ---")
        
        try:
            # 1. 获取待处理的岗位
            query = session.query(Job)
            
            if skip_processed:
                # 筛选在 job_features 表中没有关联特征的 Job
                query = query.outerjoin(JobFeature).filter(JobFeature.id == None)
            
            jobs_to_process = query.limit(limit).all()
            
            if not jobs_to_process:
                print("没有发现待处理的岗位数据。")
                return

            print(f"准备处理 {len(jobs_to_process)} 条记录...")
            
            # 2. 遍历处理 (使用 tqdm 显示进度条)
            success_count = 0
            for job in tqdm(jobs_to_process, desc="正在抽取岗位画像"):
                try:
                    # 调用 AI 抽取
                    profile = self.extractor.extract(job.raw_detail)
                    
                    # 结果入库
                    self.store.save_profile(job.id, profile)
                    
                    success_count += 1
                    
                    # 适当延迟以防触发 API 限流（根据 Qwen API 的配额调整）
                    # time.sleep(0.5) 
                    
                except Exception as e:
                    print(f"\n[错误] 处理岗位 ID {job.id} 失败: {e}")
                    continue
            
            print(f"\n--- [任务调度结束] 成功处理: {success_count} / {len(jobs_to_process)} ---")

        finally:
            session.close()

if __name__ == "__main__":
    # 示例运行：单次处理 5 条数据用于测试
    orchestrator = JobOrchestrator()
    orchestrator.run_pipeline(limit=5)
