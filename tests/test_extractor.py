import sys
import os
import pytest
import json

# 将项目根目录添加到 sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from llm_service.extractor import JobExtractor
from llm_service.schemas import JobProfile

def test_job_extractor_structure():
    """测试抽取引擎的基本输出结构并打印结果"""
    extractor = JobExtractor()
    
    test_detail = """
    我们需要一名高级前端开发工程师。
    1. 熟练掌握 React, TypeScript 和 Webpack。
    2. 要求本科及以上学历，计算机相关专业。
    3. 具有良好的团队协作能力和抗压能力。
    """
    
    print("\n--- [测试开始] 正在调用 LLM 进行抽取 ---")
    result = extractor.extract(test_detail)
    
    # 打印格式化后的结果
    print("\n[模型输出结果]:")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    print("--- [测试结束] ---\n")
    
    # 验证返回对象类型
    assert isinstance(result, JobProfile)
    assert len(result.skills) > 0
    assert len(result.thresholds) > 0
    assert len(result.professionalism) > 0

def test_empty_input_handling():
    """测试极端情况下的容错：空输入"""
    extractor = JobExtractor()
    # 大多数现代 LLM 在面对空输入时会返回空结构的 JSON 而非抛出异常
    # 我们验证它是否返回了一个标准的 JobProfile 对象（即使列表可能为空）
    result = extractor.extract(" ")
    assert isinstance(result, JobProfile)
    print("\n[空输入测试结果]:")
    print(result.model_dump())
