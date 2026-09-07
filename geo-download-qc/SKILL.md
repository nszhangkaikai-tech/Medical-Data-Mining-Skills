---
name: geo-download-qc
description: GEO 数据下载与芯片质量评估。下载原始数据后使用 R 做灰度图、权重图、残差图、RLE、RSN、RNA 降解图评估芯片质量。
triggers:
  - "GEO下载"
  - "芯片质量"
  - "RLE"
  - "降解图"
  - "QC"
input_check:
  required:
    - "GEO 系列 accession"
    - "平台 Platform ID"
  optional:
    - "样本分组信息"
output:
  - "QC 报告"
  - "质量合格/不合格判断"
source_references:
  - video: "3.GEO数据下载和数据质量分析"
  - transcript_time: "~10-25 min"
scripts:
  - "../../课程脚本代码/GEO.txt"
next_skill:
  - "geo-deg-analysis（QC 通过后）"
---

# GEO Download & QC

## 触发条件
用户需要下载 GEO 原始数据或评估芯片质量时。

## 输入
- GEO Series accession
- Platform ID
- 样本分组（可选）

## 执行步骤
1. 下载 .CEL 或表达矩阵
2. 使用 affy 或 limma 包读取
3. 生成质量评估图：
   - 灰度图 / 权重图 / 残差图
   - RLE（相对对数表达）
   - RSN（相对标准差）
   - RNA 降解图
4. 判断质量是否合格

## 输出
- 各样本 QC 图
- 质量总结（合格/需剔除样本）

## 边界
不做差异分析、不做 annotation。
