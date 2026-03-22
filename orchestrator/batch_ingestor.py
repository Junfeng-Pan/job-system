import json
import os
import sys
from tqdm import tqdm

# 确保能找到项目根目录下的模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mysql.database import SessionLocal, Job, JobFeature
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
        """清空特征数据（保留岗位主表，以防结果文件失效）"""
        session = SessionLocal()
        print("\n--- [清理] 正在清空 job_features 表中的旧特征 ---")
        try:
            num_features = session.query(JobFeature).delete()
            session.commit()
            print(f"清理完成：删除了 {num_features} 条画像特征记录。岗位主表已保留。")
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
                
                # --- 增强版修复逻辑：处理反斜杠 ---
                # 1. 保护已经正确转义的引号 \" -> 暂时替换为特殊占位符
                content = content.replace('\\"', '___DOUBLE_QUOTE_ESC___')
                # 2. 将剩下的所有反斜杠转义（解决 Vue2\3 -> Vue2\\3）
                content = content.replace('\\', '\\\\')
                # 3. 还原保护的引号 \"
                content = content.replace('___DOUBLE_QUOTE_ESC___', '\\"')
                # 4. 额外处理：如果 LLM 输出中包含真正的换行符，也需要转义，否则 json.loads 会报错
                content = content.replace('\n', '\\n').replace('\r', '\\r')
                
                # 由于我们之前手工转义了 \n，但 parser 期望的是一个干净的 JSON 字符串
                # 如果 content 本身已经是包裹在 {} 中的 JSON，手工转义换行可能会干扰解析
                # 我们重新整理一下：最核心的是处理 \" 和孤立的 \
                
                # 重新精简逻辑：
                content = response["body"]["choices"][0]["message"]["content"]
                # 保护合法转义
                content = content.replace('\\"', '___DQ___').replace('\\n', '___N___')
                # 转义孤立反斜杠
                content = content.replace('\\', '\\\\')
                # 还原
                content = content.replace('___DQ___', '\\"').replace('___N___', '\\n')
                
                # 解析 JSON 为 Pydantic 对象
                profile = self.extractor.parser.parse(content)
                
                # 持久化
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
