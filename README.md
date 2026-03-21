# Job System - 岗位画像结构化抽取系统

这是一个基于 **LangChain** 和 **阿里云百炼 (Qwen)** 的自动化岗位画像抽取系统。它可以将非结构化的招聘需求文本（Excel/XLS）转化为包含 **核心技能 (S)**、**基础门槛 (B)** 和 **职业素养 (Q)** 的结构化数据，并持久化存储至 MySQL 数据库。

## 核心功能

*   **数据清洗**：自动处理原始 `.xls` 文件，过滤空值并提取关键字段。
*   **批量推理 (Batch API)**：支持阿里云百炼的异步批量接口，推理成本降低 50%，适合万级数据处理。
*   **结构化抽取**：利用 Pydantic 严格约束 LLM 输出格式，确保 100% 符合 JSON Schema。
*   **断点续传**：系统自动记录处理进度，支持在任务中断后从断点处继续执行。
*   **自动容错**：内置 JSON 修复逻辑，处理 LLM 输出中常见的非法转义字符。

## 项目结构

```text
├── config/              # 配置文件（LLM API、MySQL 连接）
├── data/                # 数据存放区（原始 XLS、清洗后的 CSV、批量 JSONL）
├── data_processor/      # 数据处理模块（预处理、批量请求生成）
├── llm_service/         # AI 服务层（Schema 定义、Prompt 模板、Batch API 驱动）
├── mysql/               # 数据库层（SQL 脚本、ORM 模型）
├── orchestrator/        # 控制中心（批量任务编排、结果异步入库）
└── tests/               # 单元测试
```

## 快速开始

### 1. 环境准备

```bash
# 创建并激活虚拟环境
python -m venv .venv
source .venv/Scripts/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置信息
在 `config/` 目录下根据模板填写您的信息：
*   `llm-config.yaml`: 填入阿里云 API Key。
*   `mysql-config.yaml`: 填入本地 MySQL 连接信息。

### 3. 标准操作流程

#### 第一步：数据预处理
将原始 `job_data.xls` 放入 `data/` 目录，运行：
```bash
python data_processor/preprocessor.py
```

#### 第二步：基础数据入库
首先在 MySQL 中运行 `mysql/init_db.sql` 创建表结构，然后运行：
```bash
python data_processor/job_loader.py
```

#### 第三步：发起批量推理任务
该脚本会生成请求文件并上传至阿里云，自动监控任务状态直至下载结果：
```bash
python orchestrator/batch_orchestrator.py
```

#### 第四步：画像结果入库
任务完成后，将下载回来的 JSONL 结果解析并存入特征表：
```bash
# 建议初次入库使用 --refresh 清理旧测试数据
python orchestrator/batch_ingestor.py --refresh
```

## 技术栈

*   **LLM**: Qwen-Plus (Aliyun DashScope)
*   **Framework**: LangChain, Pydantic
*   **Database**: MySQL 8.0+, SQLAlchemy, PyMySQL
*   **Data**: Pandas, Numpy, xlrd
