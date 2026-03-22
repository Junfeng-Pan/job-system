import pandas as pd
import os
import re

def aggregate_top_jobs(csv_path, output_dir, top_n=10):
    """
    筛选频率最高的岗位并聚合其详情
    """
    if not os.path.exists(csv_path):
        print(f"错误: 找不到文件 {csv_path}")
        return

    # 1. 读取数据
    df = pd.read_csv(csv_path)
    
    # 2. 统计岗位频率
    print(f"正在分析岗位频率...")
    job_counts = df['岗位名称'].value_counts()
    top_jobs = job_counts.head(top_n).index.tolist()
    
    print(f"筛选出的 Top {top_n} 岗位如下：")
    for i, job in enumerate(top_jobs, 1):
        print(f"{i}. {job} (数量: {job_counts[job]})")

    # 3. 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建目录: {output_dir}")

    # 4. 提取并保存详情
    for job_name in top_jobs:
        # 过滤该岗位的所有数据
        job_details = df[df['岗位名称'] == job_name]['岗位详情'].dropna().tolist()
        
        # 文件名脱敏（去除非法字符）
        safe_filename = re.sub(r'[\\/:*?"<>|]', '_', job_name) + ".txt"
        file_path = os.path.join(output_dir, safe_filename)
        
        # 聚合文本 (使用精简分隔符以节省 Token)
        separator = "\n---\n"
        content = separator.join(job_details)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"JOB_CATEGORY: {job_name}\n")
            f.write(f"SAMPLE_SIZE: {len(job_details)}\n")
            f.write(separator)
            f.write(content)
        
        print(f"已生成: {file_path}")

if __name__ == "__main__":
    # 路径配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CSV_PATH = os.path.join(BASE_DIR, "data", "cleaned_job_data.csv")
    OUTPUT_DIR = os.path.join(BASE_DIR, "data", "top10_jobs")
    
    aggregate_top_jobs(CSV_PATH, OUTPUT_DIR)
