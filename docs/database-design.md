
这个文档详细描述了如何利用大语言模型（LLM）从岗位数据中提取结构化信息，并构建一个岗位画像体系 $P_{job}=(S,B,Q,G)$。

根据文档中的数据流程和 JSON 结构，建议采用**关系型数据库**进行建模。为了保证数据的灵活性（方便扩展技能、门槛等标签）并避免冗余，建议采用“主表 + 详情从表”的设计方案。

以下是具体的数据库表设计建议：

---

### 1. 岗位主表 (`jobs`)
存储岗位的基本信息以及所属行业。

| 字段名 | 类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| `id` | BigInt | 主键 ID | 自增 |
| `job_name` | Varchar(255) | 岗位名称 | 对应文档中的“岗位名称” |
| `salary_range` | Varchar(100) | 薪资范围 | 对应清洗数据中的“薪资范围” |
| `industry` | Varchar(255) | 所属行业 | 对应文档中的“所属行业” |
| `company_detail` | Text | 公司详情 | 对应清洗数据中的“公司详情” |
| `raw_detail` | Text | 原始岗位详情 | 存储 LLM 处理前的原始文本，方便溯源 |
| `created_at` | DateTime | 创建时间 | 记录入库时间 |

---

### 2. 岗位特征详情表 (`job_features`)
文档中的 `skills` (S)、`thresholds` (B) 和 `professionalism` (Q) 虽然逻辑意义不同，但其 **数据结构是完全一致的**（都包含 `name` 和 `evidence`）。为了查询效率和结构简洁，建议将它们统一存储在该表中，通过类型字段区分。


| 字段名 | 类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| `id` | BigInt | 主键 ID | 自增 |
| `job_id` | BigInt | 关联岗位 ID | 外键，关联 `jobs.id` |
| `feature_type` | Enum / TinyInt | 特征类型 | 1:技能(S), 2:门槛(B), 3:素养(Q) |
| `name` | Varchar(255) | 名称/标签 | 如 "javascript", "学历", "团队沟通" |
| `evidence` | Text | 数据证明 | **核心字段**：LLM 抽取的原文证据 |

---

### 3. 设计亮点分析

* **证据溯源：** 表结构中保留了 `evidence` 字段。这非常重要，因为 LLM 提取的内容可能存在幻觉，保留证据可以方便人工复核或在前端展示给用户，增强可信度。
* **扩展性：** 统一存储特征标签，未来如果需要增加新的维度（如“面试建议”），只需定义新的 `feature_type` 即可。
---

### 4. 存储建议 (SQL 示例)

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS `job_system` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `job_system`;

-- 岗位主表
CREATE TABLE `jobs` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_name` varchar(255) NOT NULL,
  `salary_range` varchar(100),
  `industry` varchar(255),
  `company_detail` text,
  `raw_detail` text,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 岗位特征详情表
CREATE TABLE `job_features` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_id` bigint NOT NULL,
  `feature_type` tinyint COMMENT '1:Skills, 2:Thresholds, 3:Professionalism',
  `name` varchar(255) NOT NULL,
  `evidence` text,
  CONSTRAINT `fk_job_id` FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

