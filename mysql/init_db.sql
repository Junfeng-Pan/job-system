-- 创建数据库
CREATE DATABASE IF NOT EXISTS `job_system` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `job_system`;

-- 1. 岗位主表
CREATE TABLE IF NOT EXISTS `jobs` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_name` varchar(255) NOT NULL COMMENT '岗位名称',
  `salary_range` varchar(100) COMMENT '薪资范围',
  `industry` varchar(255) COMMENT '所属行业',
  `company_detail` text COMMENT '公司详情',
  `raw_detail` text COMMENT '原始岗位详情文本',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 岗位特征详情表 (存储 Skills, Thresholds, Professionalism)
CREATE TABLE IF NOT EXISTS `job_features` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `job_id` bigint NOT NULL COMMENT '关联 jobs.id',
  `feature_type` tinyint NOT NULL COMMENT '1:技能(S), 2:门槛(B), 3:素养(Q)',
  `name` varchar(255) NOT NULL COMMENT '特征名称/标签',
  `evidence` text COMMENT '原文证据',
  CONSTRAINT `fk_job_id` FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
