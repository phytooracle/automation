# How to create a geojson file for a season

## 1. Locate the season's tif file
Locate the ne season's tif file on the lab server, and download it to your local machine. The path to the tif file looks somehting like this:
```bash
Z:\Processed Flights\<YEAR>\<CROP>\<DATE>\3_dsm_ortho\2_mosaic\<DATE>_transparent_mosaic_group1.tif
```

## 2. Download a previous season's geojson file
Download a previous season's geojson file from cyverse. The path to the geojson file looks something like this:
```bash
/iplant/home/shared/phytooracle/season_<X>_sorghum_yr_<YEAR>/level_0/season<X>_multi_latlon_geno_updated.geojson
```

## 3. Put both files on QGIS
Open both files on QGIS. The tif file should be on the bottom, and the geojson file should be on top. The geojson file should be transparent, so you can see the tif file underneath. 

If there are no issues, use the geojson file as a template to create a new geojson file for the new season. In the case that there are some misalignment in the geojson fix them using QGIS's tools and save the new geojson file.

## 4. Update plot information in the new geojson file
Find the excel sheet with the plot information for the new season. You may need to ask a lab member for this.

Using a python script you can update the information in the geojson. Feel free to use this script as a template:
```python
import pandas as pd
import geopandas as gpd
import numpy as np

# open geojson file
gdf = gpd.read_file('/Users/pauli-lab/Desktop/season_15/season15_multi_latlon_geno.geojson')

# open excel file specific sheet 
df = pd.read_excel('/Users/pauli-lab/Desktop/season_15/Maricopa_2022-2023_plots_by_variety.xlsx', sheet_name='SxS RIL')

# create a new column in the gdf for new genotype 
gdf['new_genotype'] = np.nan

for index, row in df.iterrows():
    # format plot number to match geojson file
    plot = str(row['plot'])
    if len(plot) == 3:
        plot = '0' + plot

    # print(row['plot'], row['genotype'])
    gdf.loc[gdf['ID'] == plot, 'new_genotype'] = row['family']

# open excel file specific sheet 
df2 = pd.read_excel('/Users/pauli-lab/Desktop/season_15/Maricopa_2022-2023_plots_by_variety.xlsx', sheet_name='collaborator')

for index, row in df2.iterrows():
    # format plot number to match geojson file
    plot = str(row['plot'])
    if len(plot) == 3:
        plot = '0' + plot

    # print(row['plot'], row['genotype'])
    gdf.loc[gdf['ID'] == plot, 'new_genotype'] = row['variety']

# open excel file specific sheet 
df3 = pd.read_excel('/Users/pauli-lab/Desktop/season_15/Maricopa_2022-2023_plots_by_variety.xlsx', sheet_name='GWAs')

for index, row in df3.iterrows():
    # format plot number to match geojson file
    plot = str(row['plot'])
    if len(plot) == 3:
        plot = '0' + plot

    # print(row['plot'], row['genotype'])
    gdf.loc[gdf['ID'] == plot, 'new_genotype'] = row['variety']

# open excel file specific sheet 
df4 = pd.read_excel('/Users/pauli-lab/Desktop/season_15/Maricopa_2022-2023_plots_by_variety.xlsx', sheet_name='border')

for index, row in df4.iterrows():
    # format plot number to match geojson file
    plot = str(row['plot'])
    if len(plot) == 3:
        plot = '0' + plot

    # print(row['plot'], row['genotype'])
    gdf.loc[gdf['ID'] == plot, 'new_genotype'] = row['genotype']

# drop the old ID the genotype column
gdf = gdf.drop(columns=['genotype'])

# rename the new genotype column to genotype 
gdf = gdf.rename(columns={'new_genotype': 'genotype'})

# save the dataframe as a geojson file
gdf.to_file('/Users/pauli-lab/Desktop/season_15/season15_multi_latlon_geno_new.geojson', driver='GeoJSON')

```

## 5. Upload the new geojson file to cyverse
Upload the new geojson file to cyverse. The path to the geojson file looks something like this:
```bash
/iplant/home/shared/phytooracle/season_<X>_sorghum_yr_<YEAR>/level_0/season<X>_multi_latlon_geno_updated.geojson
```
