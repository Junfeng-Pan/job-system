import json
import os
import sys
import yaml
from tqdm import tqdm

# 确保能找到项目根目录下的模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mysql.database import SessionLocal, Job, JobFeature
from llm_service.extractor import JobExtractor

def generate_batch_jsonl(output_path: str, limit: int = None):
    """
    生成用于阿里云批量推理的 JSONL 文件。
    1. 从数据库读取未处理的岗位详情。
    2. 使用 JobExtractor 中的 Prompt 逻辑构建 JSON 请求。
    3. 保存为 JSONL 格式。
    """
    # 1. 初始化 extractor 以复用其 Prompt 和配置逻辑
    extractor = JobExtractor()
    model_name = extractor.config["model_name"]
    # 获取包含格式指令的系统提示词
    # 注意：JobExtractor 在初始化时已经执行过 self.prompt.partial(format_instructions=...)
    # 我们需要手动提取其消息列表中的模板内容
    messages_template = extractor.prompt_with_instructions.messages
    system_prompt_template = messages_template[0].prompt.template
    user_prompt_template = messages_template[1].prompt.template
    
    # 获取格式化指令（解析器生成）
    format_instructions = extractor.parser.get_format_instructions()
    system_prompt = system_prompt_template.format(format_instructions=format_instructions)

    # 2. 从数据库查询未处理的岗位数据
    session = SessionLocal()
    print("正在从数据库查询未处理的岗位...")
    try:
        query = session.query(Job).outerjoin(JobFeature).filter(JobFeature.id == None)
        if limit:
            query = query.limit(limit)
        
        jobs_to_process = query.all()
        
        if not jobs_to_process:
            print("没有发现待处理的岗位数据。")
            return

        print(f"准备为 {len(jobs_to_process)} 条记录生成批量请求文件...")

        # 3. 构造并保存 JSONL
        with open(output_path, "w", encoding="utf-8") as f:
            for job in tqdm(jobs_to_process, desc="生成 JSONL 行"):
                # 构造符合阿里云 Batch 接口要求的单行 JSON
                # custom_id 使用 job_id 方便结果回填
                user_content = user_prompt_template.format(job_detail=job.raw_detail)
                
                request_body = {
                    "custom_id": str(job.id),
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        "temperature": 0  # 确保抽取稳定性
                    }
                }
                
                # 写入一行
                f.write(json.dumps(request_body, ensure_ascii=False) + "\n")

        print(f"\n[成功] 批量推理请求文件已保存至: {output_path}")
        print(f"提示: 请将此文件上传至阿里云百炼，并创建批量任务。")

    except Exception as e:
        print(f"生成过程发生错误: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # 示例：生成前 50 条数据的批量请求（建议先少测试几条，再生成全量的）
    output_file = os.path.join(BASE_DIR, "data", "batch_input.jsonl")
    # 如果要生成全部数据，将 limit 设为 None
    generate_batch_jsonl(output_file, limit=None)
