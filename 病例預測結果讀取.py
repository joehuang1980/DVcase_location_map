#%%
import pandas as pd
df=pd.read_csv('/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/xgboost/20250804xgboost_future14_case_results.csv')
# %%
df.columns
# %%
# %%
import geopandas as gpd
file_path = '/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/台南最小統計區圖/G97_67000_U0200_2015.shp'
encoding = 'big5'
# Read the shapefile
data = gpd.read_file(file_path,  encoding=encoding)
#僅界定出台南市市中心九區的部份
townlist=['東區', '南區', '北區', '安平區', '安南區', '中西區', '永康區', '歸仁區', '仁德區']
#%%

data.head()
# %%
#merge the dataframes on 'CODEBASE'
merged = df.merge(data, left_on='townvill', right_on='CODEBASE')
merged
# %%
#轉換成geojson地理數據格式

merged = gpd.GeoDataFrame(merged, geometry='geometry')
merged.to_file('/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/病例結果呈現/20250804xgboost_future14_case_results.geojson', driver='GeoJSON')

# %%
