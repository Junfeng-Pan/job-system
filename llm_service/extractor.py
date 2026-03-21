import yaml
import os
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from llm_service.schemas import JobProfile
from llm_service.prompts import get_job_extractor_prompt

class JobExtractor:
    def __init__(self, config_path: str = None):
        # 自动定位配置文件的绝对路径
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "llm-config.yaml")
            
        # 读取配置
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)["llm"]
        
        # 1. 初始化解析器
        self.parser = PydanticOutputParser(pydantic_object=JobProfile)
        
        # 2. 初始化 LLM
        self.llm = ChatOpenAI(
            api_key=self.config.get("api_key"),
            base_url=self.config["base_url"],
            model=self.config["model_name"],
            temperature=self.config["temperature"],
            max_retries=self.config["max_retries"]
        )
        
        # 3. 获取 ChatPromptTemplate
        self.prompt = get_job_extractor_prompt()
        
        # 4. 构建执行链 (将 format_instructions 注入)
        self.prompt_with_instructions = self.prompt.partial(
            format_instructions=self.parser.get_format_instructions()
        )
        
        self.chain = self.prompt_with_instructions | self.llm | self.parser

    def extract(self, job_detail: str) -> JobProfile:
        """执行结构化抽取逻辑"""
        try:
            return self.chain.invoke({"job_detail": job_detail})
        except Exception as e:
            print(f"LLM 抽取过程发生错误: {str(e)}")
            raise

if __name__ == "__main__":
    # 使用示例
    # extractor = JobExtractor()
    # result = extractor.extract("示例岗位文本...")
    pass
