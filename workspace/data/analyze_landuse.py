# -*- coding: utf-8 -*-
"""
谢桥新村土地利用现状分析
分析谢桥村范围内的三调地类图斑，生成分析图层和地类分析表
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path

# 设置工作路径
workspace = Path(r"C:\Users\Administrator\Desktop\临时文件\谢桥村村界调整10-17")

# 读取数据
print("读取谢桥村界范围...")
cunjie = gpd.read_file(workspace / "谢桥村村界调整.shp", encoding='gbk')
print(f"谢桥村界要素数量：{len(cunjie)}")

print("\n读取三调地类图斑...")
dltb = gpd.read_file(workspace / "DLTB2024.shp", encoding='gbk')
print(f"地类图斑要素数量：{len(dltb)}")

# 确保坐标系一致
print("\n检查坐标系...")
print(f"村界 CRS: {cunjie.crs}")
print(f"地类 CRS: {dltb.crs}")

# 合并村界为一个整体范围
cunjie_dissolved = cunjie.dissolve()
print(f"合并后村界要素数量：{len(cunjie_dissolved)}")

# 空间裁剪 - 提取谢桥村范围内的地类图斑
print("\n进行空间裁剪分析...")
# 使用 intersect 获取与村界相交的地类图斑
clipped = gpd.overlay(dltb, cunjie_dissolved, how='intersection')
print(f"裁剪后地类图斑数量：{len(clipped)}")

# 保存分析图层
output_clipped = workspace / "谢桥村土地利用现状分析.shp"
clipped.to_file(output_clipped, encoding='gbk', driver='ESRI Shapefile')
print(f"\n分析图层已保存：{output_clipped}")

# 地类分析统计
print("\n生成地类分析表...")

# 按地类代码和名称统计面积
landuse_stats = clipped.groupby(['DLBM', 'DLMC']).agg({
    'TBMJ': 'sum',  # 图斑面积
    'Shape_Area': 'sum'  # 几何面积
}).reset_index()

# 计算面积比例
landuse_stats['总面积'] = landuse_stats['TBMJ'].sum()
landuse_stats['面积比例(%)'] = (landuse_stats['TBMJ'] / landuse_stats['总面积'] * 100).round(2)

# 按面积排序
landuse_stats = landuse_stats.sort_values('TBMJ', ascending=False).reset_index(drop=True)

# 添加序号
landuse_stats.insert(0, '序号', range(1, len(landuse_stats) + 1))

# 格式化输出
landuse_stats_output = landuse_stats[['序号', 'DLBM', 'DLMC', 'TBMJ', '面积比例(%)']].copy()
landuse_stats_output.columns = ['序号', '地类代码', '地类名称', '面积(平方米)', '比例(%)']

# 保存统计表
output_table = workspace / "谢桥村地类分析表.csv"
landuse_stats_output.to_csv(output_table, index=False, encoding='utf-8-sig')
print(f"地类分析表已保存：{output_table}")

# 打印统计结果
print("\n" + "="*80)
print("谢桥村土地利用现状分析结果")
print("="*80)
print(f"分析范围：谢桥村")
print(f"地类图斑数量：{len(clipped)}")
print(f"总面积：{landuse_stats['TBMJ'].sum():,.2f} 平方米 ({landuse_stats['TBMJ'].sum()/666.67:.2f} 亩)")
print("-"*80)
print(f"{'序号':<6}{'地类代码':<10}{'地类名称':<25}{'面积(㎡)':<15}{'比例(%)':<10}")
print("-"*80)
for _, row in landuse_stats_output.iterrows():
    print(f"{int(row['序号']):<6}{row['地类代码']:<10}{row['地类名称']:<25}{row['面积(平方米)']:<15,.2f}{row['比例(%)']:<10.2f}")
print("-"*80)
print(f"{'合计':<41}{landuse_stats['TBMJ'].sum():<15,.2f}{100.00:<10.2f}")
print("="*80)

# 生成详细统计表（包含更多字段）
detailed_stats = landuse_stats.copy()
detailed_stats['面积(亩)'] = (detailed_stats['TBMJ'] / 666.67).round(2)
detailed_stats = detailed_stats[['序号', 'DLBM', 'DLMC', 'TBMJ', '面积(亩)', '面积比例(%)']]
detailed_stats.columns = ['序号', '地类代码', '地类名称', '面积(平方米)', '面积(亩)', '比例(%)']

detailed_output = workspace / "谢桥村地类分析表详细版.csv"
detailed_stats.to_csv(detailed_output, index=False, encoding='utf-8-sig')
print(f"\n详细分析表已保存：{detailed_output}")

print("\n分析完成！")
