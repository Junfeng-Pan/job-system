from typing import List
from pydantic import BaseModel, Field

class FeatureItem(BaseModel):
    name: str = Field(description="特征名称，如技能名称、学历、素质项等")
    evidence: str = Field(description="从原文中提取的直接证据文本")

class JobProfile(BaseModel):
    skills: List[FeatureItem] = Field(description="核心技能集合 (S)")
    thresholds: List[FeatureItem] = Field(description="基础门槛要求 (B)")
    professionalism: List[FeatureItem] = Field(description="职业素养要求 (Q)")
