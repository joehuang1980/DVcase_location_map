# %%
# %%
# Environment: Conda shap in DELL/ python=3.6
# PARALLEL PROCESSING VERSION - Optimized for multi-core processing
# Key improvements:
# 1. Multiprocessing for date-wise calculations
# 2. Optimized spatial intersection calculations
# 3. Performance comparison utilities
# 4. Memory-efficient processing
import pandas as pd
import os
os.environ['CUDA_VISIBLE_DEVICES'] = f"0"
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['Microsoft JhengHei']
plt.rcParams['font.family']='sans-serif' 
plt.rcParams['axes.unicode_minus'] = False
import geopandas as gpd
from shapely.geometry import Point

# %%
# Specify the file path
file_path = '/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/台南最小統計區圖/G97_67000_U0200_2015.shp'
encoding = 'big5'
# Read the shapefile
data = gpd.read_file(file_path,  encoding=encoding)

#僅界定出台南市市中心九區的部份
townlist=['東區', '南區', '北區', '安平區', '安南區', '中西區', '永康區', '歸仁區', '仁德區']
TNdata=data.loc[data['TOWN'].isin(townlist)]

df_cases=pd.read_csv('/home/joe/Documents/GIS地圖/登革熱病例資料/20241008/Dengue_Daily.csv')
df_cases

df_cases=df_cases[['發病日',  '性別', '年齡層', '居住縣市', '居住鄉鎮', '居住村里', '最小統計區',
       '最小統計區中心點X', '最小統計區中心點Y', '是否境外移入', '確定病例數']]

# 使用 buffer 方法向外擴展 500 公尺
TNdata2=TNdata.set_crs('epsg:3826', allow_override=True)
TNdata2['expanded_geometry'] = TNdata2['geometry'].buffer(500)
expanded_TNdata2=TNdata2.set_geometry('expanded_geometry')

df_cases['發病日']=pd.to_datetime(df_cases['發病日'])
df_TNcases=df_cases.loc[df_cases['居住縣市']=='台南市']
df_TNcases

df_TNcases2019=df_TNcases.loc[df_TNcases['發病日'].dt.year>=2019]
df_TNcases2019=df_TNcases2019.reset_index(drop=True)
df_TNcases2019

#建立從2019至今的日期
date_range=pd.date_range(start='2019-01-01', end='2024-10-08', freq='D')

#建立一個空的DataFrame
df_TNcase_accum=pd.DataFrame(index=date_range)

# %%
expanded_TNdata2

# %%
#劃出expanded_TNdata2
fig, ax = plt.subplots(figsize=(10, 10))
expanded_TNdata2.plot(ax=ax, color='lightgrey', edgecolor='black')
# 設定圖表標題
ax.set_title('台南市最小統計區 (擴展500公尺)', fontsize=16)
# 設定x軸和y軸標籤
ax.set_xlabel('經度', fontsize=14)
ax.set_ylabel('緯度', fontsize=14)          
# 顯示圖例
plt.legend(['最小統計區'], loc='upper right', fontsize=12)
# 顯示圖表
plt.show()

# %%
#先測試2023/8/1的病例預測
df_pred=pd.read_csv('/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/xgboost/20250808xgboost_future14_case_results.csv')


# %%
df_pred_Aug01=df_pred.loc[df_pred['date']=='2023-06-20']
#將預測病例結果與最小統計區分別依據'townvill'與"CODEBASE"合併
df_pred_Aug01 = df_pred_Aug01.merge(expanded_TNdata2, left_on='townvill', right_on='CODEBASE', how='left')


# %%
df_pred_Aug01_expanded = df_pred_Aug01.set_geometry('geometry')
#劃出預測病例結果
fig, ax = plt.subplots(figsize=(30, 30))
df_pred_Aug01_expanded.plot(ax=ax, color='lightgrey', edgecolor='black')
#'case_lag_future_14'填上淡藍色, predicted_case_lag_future_14_binary填上紅色
df_pred_Aug01_expanded.plot(ax=ax, column='predicted_case_lag_future_14_binary', cmap='OrRd', legend=True, markersize=50, alpha=0.7)
df_pred_Aug01_expanded.plot(ax=ax, column='case_lag_future_14', cmap='Blues', legend=True, markersize=50, alpha=0.3)
ax.set_title('2023年8月1日台南市預測病例分布', fontsize=16)
# 設定x軸和y軸標籤
ax.set_xlabel('經度', fontsize=14)
ax.set_ylabel('緯度', fontsize=14)
# 顯示圖例
plt.legend(['最小統計區', '預測病例'], loc='upper right', fontsize=12)
# 設定圖表大小
# 設定圖表邊距

# 顯示圖表
plt.show()

# %%
df_pred2 = df_pred.merge(expanded_TNdata2, left_on='townvill', right_on='CODEBASE', how='left')
gdf=df_pred2.set_geometry('geometry')

# %%
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon
from multiprocessing import Pool, cpu_count
from functools import partial
import time

# 方法1: 使用空间连接计算每个geometry区域内的case平均值
def calculate_case_mean_by_geometry(gdf, target_geom_col='geometry', case_col='case'):
    """
    计算每个geometry区域内所有polygons的case平均值
    
    Parameters:
    -----------
    gdf : GeoDataFrame
        包含geometry, expanded_geometry, case列的数据
    target_geom_col : str
        目标几何列名，默认为'geometry'
    case_col : str
        案例数值列名，默认为'case'
    
    Returns:
    --------
    GeoDataFrame : 包含原始geometry和计算的case平均值
    """
    
    # 创建两个临时dataframe，一个用于目标区域，一个用于数据源
    target_gdf = gdf[[target_geom_col]].copy()
    target_gdf = target_gdf.rename(columns={target_geom_col: 'geometry'})
    target_gdf['target_id'] = range(len(target_gdf))
    
    source_gdf = gdf[['geometry', case_col]].copy()
    source_gdf['source_id'] = range(len(source_gdf))
    
    # 进行空间连接：找到每个target geometry包含或相交的所有source polygons
    spatial_join = gpd.sjoin(target_gdf, source_gdf, 
                            how='left', predicate='intersects')
    
    # 按target_id分组计算case平均值
    case_means = spatial_join.groupby('target_id')[case_col].mean().reset_index()
    case_means = case_means.rename(columns={case_col: f'{case_col}_mean'})
    
    # 合并回原始数据
    result = target_gdf.merge(case_means, on='target_id', how='left')
    result = result.drop(columns=['target_id'])
    
    return result

# 方法2: 使用expanded_geometry进行空间聚合
def calculate_case_mean_by_expanded_geometry(gdf, expanded_geom_col='expanded_geometry', 
                                           case_col='case'):
    """
    使用expanded_geometry计算空间聚合的case平均值
    考虑重叠区域的权重分配
    """
    
    # 创建目标区域dataframe
    target_gdf = gdf[['geometry', expanded_geom_col]].copy()
    target_gdf['target_id'] = range(len(target_gdf))
    target_gdf = target_gdf.rename(columns={expanded_geom_col: 'geometry'})
    
    # 创建源数据dataframe
    source_gdf = gdf[['geometry', case_col]].copy()
    source_gdf['source_id'] = range(len(source_gdf))
    
    # 空间连接
    spatial_join = gpd.sjoin(target_gdf, source_gdf, 
                            how='left', predicate='intersects')
    
    # 计算平均值
    case_means = spatial_join.groupby('target_id')[case_col].mean().reset_index()
    case_means = case_means.rename(columns={case_col: f'{case_col}_expanded_mean'})
    
    # 合并结果
    result = gdf.merge(case_means, left_index=True, right_on='target_id', how='left')
    result = result.drop(columns=['target_id'])
    
    return result

# 方法3: 考虑面积权重的加权平均 (优化版本)
def calculate_weighted_case_mean_optimized(gdf, target_geom_col='geometry', 
                                         case_col='case'):
    """
    优化的基于相交面积计算加权平均值
    使用向量化操作提高性能
    """
    results = []
    geometries = gdf.geometry.values
    case_values = gdf[case_col].values
    
    for idx, row in gdf.iterrows():
        target_geom = row[target_geom_col]
        
        # 使用向量化操作找到相交的geometries
        try:
            intersections = [geom.intersection(target_geom) for geom in geometries]
            intersection_areas = np.array([inter.area if hasattr(inter, 'area') else 0 
                                         for inter in intersections])
            
            # 过滤掉面积为0的相交
            valid_mask = intersection_areas > 1e-10
            
            if not np.any(valid_mask):
                weighted_mean = np.nan
            else:
                valid_areas = intersection_areas[valid_mask]
                valid_cases = case_values[valid_mask]
                
                # 计算加权平均
                total_weight = valid_areas.sum()
                if total_weight > 0:
                    weighted_mean = (valid_cases * valid_areas).sum() / total_weight
                else:
                    weighted_mean = valid_cases.mean()
        except Exception as e:
            print(f"Error processing geometry at index {idx}: {e}")
            weighted_mean = np.nan
        
        results.append(weighted_mean)
    
    return results

# 保持原版本以备兼容性
def calculate_weighted_case_mean(gdf, target_geom_col='geometry', 
                               case_col='case'):
    """
    基于相交面积计算加权平均值
    适用于需要考虑重叠程度的情况
    """
    
    results = []
    
    for idx, row in gdf.iterrows():
        target_geom = row[target_geom_col]
        
        # 找到与目标geometry相交的所有polygons
        intersecting_mask = gdf.geometry.intersects(target_geom)
        intersecting_gdf = gdf[intersecting_mask].copy()
        
        if len(intersecting_gdf) == 0:
            weighted_mean = np.nan
        else:
            # 计算相交面积作为权重
            intersecting_gdf['intersection_area'] = intersecting_gdf.geometry.apply(
                lambda geom: geom.intersection(target_geom).area
            )
            
            # 计算加权平均
            total_weight = intersecting_gdf['intersection_area'].sum()
            if total_weight > 0:
                weighted_mean = (intersecting_gdf[case_col] * 
                               intersecting_gdf['intersection_area']).sum() / total_weight
            else:
                weighted_mean = intersecting_gdf[case_col].mean()
        
        results.append(weighted_mean)
    
    return results

# 主要执行函数
def process_spatial_case_aggregation(gdf, method='simple'):
    """
    主要处理函数
    
    Parameters:
    -----------
    gdf : GeoDataFrame
        输入数据
    method : str
        计算方法 ('simple', 'expanded', 'weighted')
    """
    
    if method == 'simple':
        # 简单空间相交平均值
        result = calculate_case_mean_by_geometry(gdf)
        
    elif method == 'expanded':
        # 使用expanded_geometry计算
        result = calculate_case_mean_by_expanded_geometry(gdf)
        
    elif method == 'weighted':
        # 面积加权平均值
        gdf_copy = gdf.copy()
        gdf_copy['case_weighted_mean'] = calculate_weighted_case_mean(gdf)
        result = gdf_copy
    
    return result

# 使用示例
"""
# 假设您的数据是这样的：
# gdf = gpd.read_file('your_shapefile.shp')

# 方法1: 简单平均值
result1 = process_spatial_case_aggregation(gdf, method='simple')

# 方法2: 使用expanded_geometry
result2 = process_spatial_case_aggregation(gdf, method='expanded')

# 方法3: 面积加权平均值（推荐用于有重叠的情况）
result3 = process_spatial_case_aggregation(gdf, method='weighted')

# 查看结果
print("简单平均值结果:")
print(result1[['case_mean']].head())

print("\n使用expanded_geometry结果:")
print(result2[['case_expanded_mean']].head())

print("\n面积加权平均值结果:")
print(result3[['case_weighted_mean']].head())
"""

# %%
# Parallel processing function for each date
def process_date_parallel(date_data, use_optimized=True):
    """Process spatial aggregation for a single date"""
    date, gdf_temp = date_data
    print(f"Processing 日期: {date}, 共有 {len(gdf_temp)} 筆資料")
    
    if not gdf_temp.empty:
        gdf_temp = gdf_temp.copy()
        
        # Choose optimized or original function
        calc_func = calculate_weighted_case_mean_optimized if use_optimized else calculate_weighted_case_mean
        
        gdf_temp['case_weighted_mean'] = calc_func(
            gdf_temp, target_geom_col='geometry', case_col='case_lag_future_14'
        )
        gdf_temp['pred_weighted_mean'] = calc_func(
            gdf_temp, target_geom_col='geometry', case_col='predicted_case_lag_future_14'
        )
        return gdf_temp
    return None

# Parallel processing implementation
def process_all_dates_parallel(gdf, n_processes=None, use_optimized=True):
    """Process all dates in parallel"""
    if n_processes is None:
        n_processes = min(cpu_count(), len(gdf['date'].unique()))
    
    print(f"Using {n_processes} processes for parallel computation")
    print(f"Using {'optimized' if use_optimized else 'original'} calculation method")
    
    # Prepare date groups
    unique_dates = gdf['date'].unique()
    date_groups = [(date, gdf[gdf['date'] == date]) for date in unique_dates]
    
    start_time = time.time()
    
    # Create partial function with optimized parameter
    process_func = partial(process_date_parallel, use_optimized=use_optimized)
    
    # Process in parallel
    with Pool(processes=n_processes) as pool:
        results = pool.map(process_func, date_groups)
    
    # Filter out None results and concatenate
    gdflist = [result for result in results if result is not None]
    
    if gdflist:
        result = pd.concat(gdflist, ignore_index=True)
        processing_time = time.time() - start_time
        print(f"Parallel processing completed in {processing_time:.2f} seconds")
        print(f"Average processing time per date: {processing_time/len(unique_dates):.2f} seconds")
        return result
    else:
        print("No data to process")
        return pd.DataFrame()

# Performance comparison function (optional)
def compare_methods(gdf, sample_size=None):
    """Compare serial vs parallel processing performance"""
    if sample_size and len(gdf['date'].unique()) > sample_size:
        sample_dates = np.random.choice(gdf['date'].unique(), sample_size, replace=False)
        gdf_sample = gdf[gdf['date'].isin(sample_dates)]
    else:
        gdf_sample = gdf
    
    print(f"Performance comparison with {len(gdf_sample['date'].unique())} dates")
    
    # Serial processing
    print("\n--- Serial Processing ---")
    start_time = time.time()
    gdflist_serial = []
    for date in gdf_sample['date'].unique():
        gdf_temp = gdf_sample[gdf_sample['date'] == date]
        if not gdf_temp.empty:
            gdf_temp = gdf_temp.copy()
            gdf_temp['case_weighted_mean'] = calculate_weighted_case_mean(
                gdf_temp, target_geom_col='geometry', case_col='case_lag_future_14'
            )
            gdf_temp['pred_weighted_mean'] = calculate_weighted_case_mean(
                gdf_temp, target_geom_col='geometry', case_col='predicted_case_lag_future_14'
            )
            gdflist_serial.append(gdf_temp)
    serial_time = time.time() - start_time
    print(f"Serial processing time: {serial_time:.2f} seconds")
    
    # Parallel processing
    print("\n--- Parallel Processing ---")
    parallel_start = time.time()
    parallel_result = process_all_dates_parallel(gdf_sample, use_optimized=True)
    parallel_time = time.time() - parallel_start
    
    if serial_time > 0 and parallel_time > 0:
        speedup = serial_time / parallel_time
        print(f"\nSpeed improvement: {speedup:.2f}x faster")
        print(f"Serial: {serial_time:.2f}s, Parallel: {parallel_time:.2f}s")
    
    return parallel_result

# Choose processing method
def run_spatial_aggregation(gdf, method='parallel', compare_performance=False, sample_size=5):
    """
    Main function to run spatial aggregation
    
    Parameters:
    -----------
    gdf : GeoDataFrame
        Input geodataframe
    method : str
        'parallel' or 'serial'
    compare_performance : bool
        Whether to run performance comparison first
    sample_size : int
        Sample size for performance comparison
    """
    
    if compare_performance:
        print("Running performance comparison...")
        compare_methods(gdf, sample_size)
        print("\n" + "="*50)
    
    print(f"Running {method} spatial aggregation on full dataset...")
    
    if method == 'parallel':
        result = process_all_dates_parallel(gdf, use_optimized=True)
    else:
        # Serial processing (original method)
        gdflist = []
        start_time = time.time()
        for date in gdf['date'].unique():
            gdf_temp = gdf[gdf['date'] == date]
            print(f"日期: {date}, 共有 {len(gdf_temp)} 筆資料")
            if not gdf_temp.empty:
                gdf_temp = gdf_temp.copy()
                gdf_temp['case_weighted_mean'] = calculate_weighted_case_mean(
                    gdf_temp, target_geom_col='geometry', case_col='case_lag_future_14'
                )
                gdf_temp['pred_weighted_mean'] = calculate_weighted_case_mean(
                    gdf_temp, target_geom_col='geometry', case_col='predicted_case_lag_future_14'
                )
                gdflist.append(gdf_temp)
        result = pd.concat(gdflist, ignore_index=True) if gdflist else pd.DataFrame()
        print(f"Serial processing completed in {time.time() - start_time:.2f} seconds")
    
    return result

# Execute processing
if __name__ == "__main__":
    print("Starting spatial aggregation...")
    
    # Option 1: Run with performance comparison (recommended for first time)
    # result = run_spatial_aggregation(gdf, method='parallel', compare_performance=True, sample_size=3)
    
    # Option 2: Run parallel processing directly (faster)
    result = run_spatial_aggregation(gdf, method='parallel', compare_performance=False)
    
    # Save results
    result.to_csv('/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/xgboost/20250808xgboost_future14_case_results_aggregated.csv', index=False)
    print("Results saved to CSV file")


# %%
#指定日期
date='2023-07-01'
result2=result.loc[result['date'] == date]
result2 = result2.set_geometry('geometry')

#劃出預測病例結果
fig, ax = plt.subplots(figsize=(30, 30))
result2.plot(ax=ax, color='lightgrey', edgecolor='black')
#'case_weighted_mean'填上淡藍色, pred_weighted_mean填上紅色
result2.plot(ax=ax, column='pred_weighted_mean', cmap='OrRd', legend=True, markersize=50, alpha=0.5)
result2.plot(ax=ax, column='case_weighted_mean', cmap='Blues', legend=True, markersize=50, alpha=0.5)
ax.set_title(f'{date}_台南市預測病例分布', fontsize=20)
# 設定x軸和y軸標籤
ax.set_xlabel('經度', fontsize=14)
ax.set_ylabel('緯度', fontsize=14)
# 顯示圖例
plt.legend(['最小統計區', '預測病例'], loc='upper right', fontsize=14)
plt.tight_layout()
plt.savefig(f'/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/xgboost/20250808xgboost_future14_case_results_{date}.jpg', dpi=600, bbox_inches='tight')

# 顯示圖表
plt.show()


