
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
| `industry` | Varchar(255) | 所属行业 | 对应文档中的“所属行业” |
| `raw_detail` | Text | 原始岗位详情 | 存储 LLM 处理前的原始文本，方便溯源 |
| `created_at` | DateTime | 创建时间 | 记录入库时间 |

---

### 2. 岗位特征详情表 (`job_features`)
文档中的 `skills` (S)、`thresholds` (B) 和 `professionalism` (Q) 虽然逻辑意义不同，但其 **数据结构是完全一致的**（都包含 `name` 和 `evidence`）。为了查询效率和结构简洁，建议将它们统一存储在该表中，通过类型字段区分。


| 字段名 | 类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| `id` | BigInt | 主键 ID | 自增 |
| `job_id` | BigInt | 关联岗位 ID | 外键，关联 `jobs.id` |
| `feature_type` | Enum / TinyInt | 特征类型 | 1:技能(S), 2:门槛(B), 3:素养(Q), 4:路径(G) |
| `name` | Varchar(255) | 名称/标签 | 如 "javascript", "学历", "团队沟通" |
| `evidence` | Text | 数据证明 | **核心字段**：LLM 抽取的原文证据 |

---

### 3. 设计亮点分析

* **证据溯源：** 表结构中保留了 `evidence` 字段。这非常重要，因为 LLM 提取的内容可能存在幻觉，保留证据可以方便人工复核或在前端展示给用户，增强可信度。
* **扩展性：** 文档中提到了 $G$（发展路径），虽然示例 JSON 中暂未包含，但通过 `job_features` 表中的 `feature_type` 字段，可以非常容易地添加 $G$ 的数据而无需修改表结构。
---

### 4. 存储建议 (SQL 示例)

```sql
CREATE TABLE `jobs` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_name` varchar(255) NOT NULL,
  `industry` varchar(255),
  `raw_detail` text,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE `job_features` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_id` bigint NOT NULL,
  `feature_type` tinyint COMMENT '1:Skills, 2:Thresholds, 3:Professionalism, 4:Growth',
  `name` varchar(255) NOT NULL,
  `evidence` text
);
```


## 方案补充

如果业务的很多查询场景是“通过 `job_id` 获取该岗位的全部画像详情”用于前端展示，那么之前那种将特征拆分成几十行的“高度范式化”设计，确实会在查询时产生不可忽视的 `JOIN` 开销，效率不如单表直查。

### 完善后的数据库表结构设计（三表模式）

我们保留 `jobs` 主表和 `job_features` 从表，并新增一张 `job_profiles_json` 表来专门存储大模型输出的完整 JSON。

#### 1. 岗位主表 (`jobs`)
保持纯粹，只存基础元数据和原始文本。

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | BigInt | 主键 ID (自增) |
| `job_name` | Varchar(255) | 岗位名称 |
| `industry` | Varchar(255) | 所属行业 |
| `raw_detail` | Text | 原始岗位详情文本 |
| `created_at` | DateTime | 创建时间 |

#### 2. 画像 JSON 存储表 (`job_profiles_json`) -> **【新增】**
专门用于高并发的详情展示。与 `jobs` 表是 **1 对 1** 的关系。

| 字段名 | 类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| `job_id` | BigInt | 关联岗位 ID | 主键，同时也是外键关联 `jobs.id` |
| `profile_data`| JSON | LLM 抽取的完整画像 JSON | 包含完整的 S, B, Q 数据结构 |
| `updated_at` | DateTime | 更新时间 | 更新时间|

#### 3. 岗位特征匹配表 (`job_features`) -> **【保留原始设计】**
专门用于复杂的特征检索、聚合统计和匹配算法。与 `jobs` 表是 **多对 1** 的关系。

| 字段名 | 类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| `id` | BigInt | 主键 ID | 自增 |
| `job_id` | BigInt | 关联岗位 ID | 外键，关联 `jobs.id` |
| `feature_type`| TinyInt | 特征类型 | 1:技能(S), 2:门槛(B), 3:素养(Q), 4:路径(G) |
| `name` | Varchar(255)| 名称/标签 | 用于条件匹配，建议对此字段加索引 |
| `evidence` | Text | 数据证明 | |

---

### 对应的 SQL 创建语句

```sql
-- 1. 岗位主表
CREATE TABLE `jobs` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_name` varchar(255) NOT NULL,
  `industry` varchar(255),
  `raw_detail` text,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP
);

-- 2. 新增：完整画像 JSON 表 (注意这里把 job_id 直接作为主键)
CREATE TABLE `job_profiles_json` (
  `job_id` bigint PRIMARY KEY,
  `profile_data` json NOT NULL COMMENT 'LLM生成的完整JSON数据',
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE CASCADE
);

-- 3. 保留：拆分的特征表 (增加了一个普通索引加快匹配速度)
CREATE TABLE `job_features` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_id` bigint NOT NULL,
  `feature_type` tinyint NOT NULL COMMENT '1:技能, 2:门槛, 3:素养',
  `name` varchar(255) NOT NULL,
  `evidence` text,
  FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE CASCADE,
  INDEX `idx_feature_name` (`name`) -- 为后续匹配算法预留的索引
);
```

### 架构上的优势总结

1. **职责极其清晰**：`jobs` 负责列表展示，`job_profiles_json` 负责详情页渲染，`job_features` 负责后台推荐算法。
2. **极佳的扩展性**：如果有一天前端页面需要展示 LLM 抽取的某些额外字段（比如薪资预估、工作地），你只需要修改 JSON 结构，完全不需要触碰底层用于匹配的 `job_features` 表结构。
