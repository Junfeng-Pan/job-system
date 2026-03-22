import json
import os
import sys
from tqdm import tqdm

# 确保能找到项目根目录下的模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mysql.database import SessionLocal, Job, JobFeature, JobProfileJson
from llm_service.extractor import JobExtractor
from data_processor.feature_store import FeatureStore

class BatchIngestor:
    """
    批量结果入库模块
    负责解析 result.jsonl 并持久化到数据库
    """

    def __init__(self):
        self.extractor = JobExtractor() # 用于解析 JSON 字符串
        self.store = FeatureStore()

    def clear_database(self):
        """清空特征数据和 JSON 数据（保留岗位主表）"""
        session = SessionLocal()
        print("\n--- [清理] 正在清空旧画像数据 ---")
        try:
            num_json = session.query(JobProfileJson).delete()
            num_features = session.query(JobFeature).delete()
            session.commit()
            print(f"清理完成：删除了 {num_json} 条 JSON 记录和 {num_features} 条特征记录。")
        except Exception as e:
            session.rollback()
            print(f"清理失败: {e}")
        finally:
            session.close()

    def ingest_from_jsonl(self, result_path: str):
        """从 JSONL 文件读取结果并入库"""
        if not os.path.exists(result_path):
            print(f"错误: 找不到结果文件 {result_path}")
            return

        print(f"\n--- [入库开始] 正在解析: {result_path} ---")
        
        with open(result_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        success_count = 0
        error_count = 0
        
        for line in tqdm(lines, desc="处理解析结果"):
            try:
                data = json.loads(line)
                job_id = int(data["custom_id"])
                
                # 校验响应
                response = data.get("response")
                if not response or response.get("status_code") != 200:
                    print(f"\n[跳过] Job ID {job_id}: 响应状态码非 200")
                    error_count += 1
                    continue
                
                # 提取内容
                content = response["body"]["choices"][0]["message"]["content"]
                
                # --- 智能修复逻辑：仅转义那些非法的反斜杠 ---
                # 使用正则：
                # (?<!\\) -> 确保前面没有反斜杠
                # \\      -> 匹配当前反斜杠
                # (?![u"\\/bfnrt]) -> 确保后面不是合法的转义字符
                import re
                content = re.sub(r'(?<!\\)\\(?![u"\\/bfnrt])', r'\\\\', content)
                
                # 解析 JSON 为 Pydantic 对象
                profile = self.extractor.parser.parse(content)
                
                # 持久化 (FeatureStore 内部会处理 job_features 和 job_profiles_json)
                self.store.save_profile(job_id, profile)
                success_count += 1
            except Exception as e:
                print(f"\n[错误] 解析数据行失败 (Job ID: {data.get('custom_id')}): {e}")
                error_count += 1
                continue
        
        print(f"\n--- [入库结束] 成功: {success_count}, 失败: {error_count} ---")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="批量结果入库工具")
    parser.add_argument("--refresh", action="store_true", help="入库前是否清空现有数据")
    parser.add_argument("--file", type=str, default="data/batch_result.jsonl", help="结果文件路径")
    
    args = parser.parse_args()
    
    ingestor = BatchIngestor()
    
    if args.refresh:
        ingestor.clear_database()
        
    full_path = os.path.join(BASE_DIR, args.file)
    ingestor.ingest_from_jsonl(full_path)
