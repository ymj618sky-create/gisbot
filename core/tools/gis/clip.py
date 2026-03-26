"""Clip analysis tools - 裁剪分析工具."""

import json
import os
from pathlib import Path
from typing import Any
from core.tools.base import Tool, GISError, EmptyResultError


class ClipTool(Tool):
    """Clip features by another layer (裁剪分析)."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "clip_analysis"

    @property
    def description(self) -> str:
        return "Clip input features by clip features (裁剪分析). Input files are paths, output is saved to file."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_file": {
                    "type": "string",
                    "description": "Input file path (to be clipped)"
                },
                "clip_file": {
                    "type": "string",
                    "description": "Clip file path (clip boundary)"
                },
                "output_file": {
                    "type": "string",
                    "description": "Output file path"
                }
            },
            "required": ["input_file", "clip_file", "output_file"]
        }

    async def execute(self, input_file: str, clip_file: str, output_file: str, **kwargs) -> str:
        try:
            import geopandas as gpd
            import pandas as pd
            
            # Resolve paths
            input_path = Path(input_file)
            clip_path = Path(clip_file)
            output_path = Path(output_file)
            
            if not input_path.is_absolute():
                input_path = self.workspace / input_path
            if not clip_path.is_absolute():
                clip_path = self.workspace / clip_path
            if not output_path.is_absolute():
                output_path = self.workspace / output_path
            
            print(f"Input: {input_path}")
            print(f"Clip: {clip_path}")
            print(f"Output: {output_path}")
            
            # Read input data
            print("Reading input file...")
            input_gdf = gpd.read_file(str(input_path))
            print(f"  Features: {len(input_gdf)}")
            
            # Read clip data
            print("Reading clip file...")
            clip_gdf = gpd.read_file(str(clip_path))
            print(f"  Features: {len(clip_gdf)}")
            
            # Ensure same CRS
            if input_gdf.crs != clip_gdf.crs:
                print(f"Reprojecting input to clip CRS...")
                input_gdf = input_gdf.to_crs(clip_gdf.crs)
            
            # Union clip geometries
            print("Creating clip boundary...")
            clip_boundary = clip_gdf.unary_union
            
            # Clip
            print("Clipping features...")
            clipped_gdf = gpd.clip(input_gdf, clip_boundary)
            print(f"  Clipped features: {len(clipped_gdf)}")
            
            # Add clipped area field
            print("Calculating areas...")
            clipped_gdf['CLIP_MJ'] = clipped_gdf.geometry.area
            
            # Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Saving to {output_path}...")
            
            # Determine output format based on extension
            ext = output_path.suffix.lower()
            if ext == '.geojson':
                clipped_gdf.to_file(str(output_path), driver='GeoJSON')
            elif ext == '.gpkg':
                clipped_gdf.to_file(str(output_path), driver='GPKG')
            else:
                clipped_gdf.to_file(str(output_path), encoding='gbk')
            
            # Calculate statistics
            print("Calculating statistics...")
            if 'DLBM' in clipped_gdf.columns and 'DLMC' in clipped_gdf.columns:
                stats = clipped_gdf.groupby(['DLBM', 'DLMC']).agg({
                    'CLIP_MJ': ['sum', 'count']
                }).reset_index()
                stats.columns = ['DLBM', 'DLMC', 'MJ_HJ', 'TB_COUNT']
                stats['MJ_HM2'] = stats['MJ_HJ'] / 10000
                stats['MJ_MU'] = stats['MJ_HJ'] / 666.67
                total_area = stats['MJ_HJ'].sum()
                stats['ZB'] = (stats['MJ_HJ'] / total_area * 100).round(2)
                stats = stats.sort_values('MJ_HJ', ascending=False).reset_index(drop=True)
                
                # Add total row
                total_row = pd.DataFrame({
                    'DLBM': ['总计'],
                    'DLMC': [''],
                    'MJ_HJ': [total_area],
                    'TB_COUNT': [len(clipped_gdf)],
                    'MJ_HM2': [total_area / 10000],
                    'MJ_MU': [total_area / 666.67],
                    'ZB': [100.0]
                })
                stats = pd.concat([stats, total_row], ignore_index=True)
                
                # Save stats
                stats_csv = output_path.parent / f"{output_path.stem}_stats.csv"
                stats.to_csv(stats_csv, index=False, encoding='utf-8-sig')
                print(f"Stats saved to {stats_csv}")
                
                # Also save as Excel
                stats_xlsx = output_path.parent / f"{output_path.stem}_stats.xlsx"
                stats.to_excel(stats_xlsx, index=False, sheet_name='地类分析')
                print(f"Stats saved to {stats_xlsx}")
            
            result = f"✅ Clip completed!\n\n"
            result += f"📊 Input features: {len(input_gdf)}\n"
            result += f"📊 Clipped features: {len(clipped_gdf)}\n"
            result += f"📁 Output: {output_path}\n"
            
            if 'DLBM' in clipped_gdf.columns:
                result += f"\n📈 Statistics saved:\n"
                result += f"   - {output_path.parent / f'{output_path.stem}_stats.csv'}\n"
                result += f"   - {output_path.parent / f'{output_path.stem}_stats.xlsx'}\n"
            
            return result
            
        except Exception as e:
            import traceback
            return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
