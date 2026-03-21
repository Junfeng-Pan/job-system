import os
import sys
from pathlib import Path
from openai import OpenAI
import yaml
import logging

# 确保能找到项目根目录下的模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 开启 HTTPX 详细日志（如果需要深度 Debug，请取消注释下一行）
# logging.basicConfig(level=logging.DEBUG)

class BatchService:
    """封装阿里云百炼 Batch API 操作"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(BASE_DIR, "config", "llm-config.yaml")
        
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)["llm"]
        
        self.client = OpenAI(
            api_key=self.config.get("api_key"),
            base_url=self.config["base_url"]
        )

    def upload_file(self, file_path: str) -> str:
        """上传 JSONL 文件，返回 file_id"""
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        print(f"--- [上传开始] 文件: {file_path} ---")
        print(f"--- [Debug] 文件大小: {file_size:.2f} MB ---")
        
        # 如果文件超过 50 MB，上传确实会需要几分钟甚至更久（取决于您的上行带宽）
        if file_size > 50:
            print("提示: 文件较大，上传过程没有进度条，请耐心等待或开启 httpx 日志观察流量...")

        file_object = self.client.files.create(
            file=Path(file_path),
            purpose="batch"
        )
        print(f"上传成功，文件 ID: {file_object.id}")
        return file_object.id

    def create_batch_job(self, input_file_id: str) -> str:
        """创建批量处理任务，返回 batch_id"""
        print(f"正在创建 Batch 任务 (Input: {input_file_id})...")
        batch = self.client.batches.create(
            input_file_id=input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "ds_name": "Job_Profile_Batch_Extraction",
                "ds_description": "批量提取岗位画像特征"
            }
        )
        print(f"任务已创建，ID: {batch.id}")
        return batch.id

    def get_batch_info(self, batch_id: str):
        """获取任务详细状态"""
        return self.client.batches.retrieve(batch_id)

    def download_file(self, file_id: str, save_path: str):
        """下载结果文件"""
        print(f"正在下载结果文件 (ID: {file_id})...")
        content = self.client.files.content(file_id)
        content.write_to_file(save_path)
        print(f"结果已保存至: {save_path}")
