import os
import sys
import time

# 确保能找到项目根目录下的模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from llm_service.batch_service import BatchService
from data_processor.batch_request_generator import generate_batch_jsonl

class BatchOrchestrator:
    """
    批量任务编排器
    专注流程：生成请求 -> 提交 -> 监控 -> 下载
    """

    def __init__(self):
        self.batch_service = BatchService()

    def run_inference_flow(self, limit: int = None):
        """执行推理流水线（不含入库）"""
        
        # 1. 生成请求文件
        input_path = os.path.join(BASE_DIR, "data", "batch_input.jsonl")
        generate_batch_jsonl(input_path, limit=limit)
        
        if not os.path.exists(input_path):
            return

        # 2. 上传并创建任务
        file_id = self.batch_service.upload_file(input_path)
        batch_id = self.batch_service.create_batch_job(file_id)
        
        # 3. 轮询状态
        print(f"\n--- [状态监控开始] 任务 ID: {batch_id} ---")
        while True:
            batch = self.batch_service.get_batch_info(batch_id)
            status = batch.status
            print(f"[{time.strftime('%H:%M:%S')}] 当前状态: {status} "
                  f"(已完成: {batch.request_counts.completed}/{batch.request_counts.total})")
            
            if status == "completed":
                print("\n[完成] 批量推理已结束，正在下载结果...")
                result_path = os.path.join(BASE_DIR, "data", "batch_result.jsonl")
                self.batch_service.download_file(batch.output_file_id, result_path)
                print(f"结果已就绪：{result_path}")
                print("您可以运行 'python orchestrator/batch_ingestor.py' 来完成入库。")
                break
            elif status in ["failed", "expired", "cancelled"]:
                print(f"\n[终止] 任务未成功完成。状态: {status}")
                break
            
            # 每 60 秒检查一次
            time.sleep(60)

if __name__ == "__main__":
    orchestrator = BatchOrchestrator()
    # 示例运行：处理 5 条验证流程
    orchestrator.run_inference_flow(limit=None)
