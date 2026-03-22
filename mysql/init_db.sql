-- 1. 岗位主表
CREATE TABLE IF NOT EXISTS `jobs` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_name` varchar(255) NOT NULL,
  `salary_range` varchar(100),
  `industry` varchar(255),
  `company_detail` text,
  `raw_detail` text,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP
);

-- 2. 新增：完整画像 JSON 表 (1对1关系)
CREATE TABLE IF NOT EXISTS `job_profiles_json` (
  `job_id` bigint PRIMARY KEY,
  `profile_data` json NOT NULL COMMENT 'LLM生成的完整JSON数据',
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE CASCADE
);

-- 3. 岗位特征匹配表 (多对1关系)
CREATE TABLE IF NOT EXISTS `job_features` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_id` bigint NOT NULL,
  `feature_type` tinyint NOT NULL COMMENT '1:技能, 2:门槛, 3:素养, 4:路径',
  `name` varchar(255) NOT NULL,
  `evidence` text,
  FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE CASCADE,
  INDEX `idx_feature_name` (`name`)
);
