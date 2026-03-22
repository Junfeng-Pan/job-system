import pandas as pd
import os

def preprocess_job_data(input_path: str, output_path: str):
    """
    预处理岗位数据：
    1. 只保留：岗位名称、薪资范围、所属行业、岗位详情、公司详情
    2. 剔除：岗位名称 或 岗位详情 为空的数据
    """
    print(f"--- [开始预处理] 读取文件: {input_path} ---")
    
    if not os.path.exists(input_path):
        print(f"错误: 找不到输入文件 {input_path}")
        return

    # 加载 Excel 数据
    try:
        # xls 格式需要 xlrd 引擎
        df = pd.read_excel(input_path)
    except Exception as e:
        print(f"读取 Excel 失败: {e}")
        return

    # 1. 定义目标字段映射（确保与 Excel 中的表头一致，如果不一致请根据实际调整）
    target_columns = ["岗位名称", "薪资范围", "所属行业", "岗位详情", "公司详情"]
    
    # 检查字段是否存在
    existing_cols = [col for col in target_columns if col in df.columns]
    missing_cols = set(target_columns) - set(df.columns)
    
    if missing_cols:
        print(f"警告: 原始数据中缺失以下字段: {missing_cols}")
    
    # 只保留存在的对应字段
    df_cleaned = df[existing_cols].copy()

    # 2. 剔除“岗位名称”或“岗位详情”为空的行
    # 假设这两个字段在 Excel 中的准确名称是“岗位名称”和“岗位详情”
    critical_cols = ["岗位名称", "岗位详情"]
    valid_critical = [col for col in critical_cols if col in df_cleaned.columns]
    
    initial_count = len(df_cleaned)
    df_cleaned = df_cleaned.dropna(subset=valid_critical, how='any')
    
    # 进一步处理空字符串（如果是文本格式的空值）
    for col in valid_critical:
        df_cleaned = df_cleaned[df_cleaned[col].astype(str).str.strip() != ""]
    
    # --- 新增逻辑：剔除“岗位详情”除去空白符后字数过少（少于 10 个字符）的行 ---
    if "岗位详情" in df_cleaned.columns:
        # 使用正则表达式 \s+ 匹配并移除所有空白符（空格、换行、制表符等）后再计算长度
        df_cleaned = df_cleaned[df_cleaned["岗位详情"].astype(str).str.replace(r'\s+', '', regex=True).str.len() >= 10]
    
    final_count = len(df_cleaned)
    
    print(f"清洗完成: 原始数据 {initial_count} 条 -> 有效数据 {final_count} 条 (剔除 {initial_count - final_count} 条)")

    # 3. 保存结果
    df_cleaned.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"结果已保存至: {output_path}")

if __name__ == "__main__":
    # 动态获取路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(BASE_DIR, "data", "job_data.xls")
    output_file = os.path.join(BASE_DIR, "data", "cleaned_job_data.csv")
    
    preprocess_job_data(input_file, output_file)
