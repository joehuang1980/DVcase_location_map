#!/usr/bin/env python3
"""
資料分割腳本 - 將大型GeoJSON檔案分割成每日獨立檔案
用途：改善網頁載入速度，避免載入整個2.6GB檔案
"""

import geopandas as gpd
import pandas as pd
import os
import json
from pathlib import Path
import time

def split_geojson_by_date():
    """將大型GeoJSON檔案按日期分割成獨立檔案"""
    
    print("開始分割資料檔案...")
    start_time = time.time()
    
    # 檔案路徑
    input_file = "20250804xgboost_future14_case_results.geojson"
    output_dir = Path("data/daily")
    
    # 建立輸出目錄
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 讀取大型GeoJSON檔案
    print(f"正在讀取檔案: {input_file} (2.6GB)")
    gdf = gpd.read_file(input_file)
    
    # 轉換日期格式
    gdf['date'] = pd.to_datetime(gdf['date']).dt.strftime('%Y-%m-%d')
    unique_dates = sorted(gdf['date'].unique())
    
    print(f"發現 {len(unique_dates)} 個日期，共 {len(gdf)} 筆記錄")
    print(f"日期範圍: {unique_dates[0]} 到 {unique_dates[-1]}")
    
    # 按日期分割並儲存
    for i, date in enumerate(unique_dates, 1):
        daily_data = gdf[gdf['date'] == date]
        output_file = output_dir / f"{date}.geojson"
        
        # 儲存為GeoJSON格式
        daily_data.to_file(output_file, driver='GeoJSON')
        
        # 顯示進度
        file_size = output_file.stat().st_size / (1024 * 1024)  # MB
        print(f"[{i:3d}/{len(unique_dates)}] {date}: {len(daily_data):,} 筆記錄 -> {file_size:.1f}MB")
    
    # 創建日期索引檔案
    date_index = {
        "dates": unique_dates,
        "total_files": len(unique_dates),
        "date_range": {
            "start": unique_dates[0],
            "end": unique_dates[-1]
        }
    }
    
    with open(output_dir / "index.json", 'w') as f:
        json.dump(date_index, f, indent=2)
    
    end_time = time.time()
    print(f"\n分割完成！")
    print(f"總耗時: {end_time - start_time:.1f} 秒")
    print(f"輸出目錄: {output_dir.absolute()}")
    print(f"檔案總數: {len(unique_dates)} 個日期檔案 + 1 個索引檔案")
    
    # 計算節省的空間
    total_size = sum(f.stat().st_size for f in output_dir.glob("*.geojson"))
    original_size = Path(input_file).stat().st_size
    print(f"原始檔案: {original_size / (1024**3):.1f}GB")
    print(f"分割後總大小: {total_size / (1024**3):.1f}GB")
    print(f"單個檔案平均大小: {(total_size / len(unique_dates)) / (1024**2):.1f}MB")

if __name__ == "__main__":
    split_geojson_by_date()