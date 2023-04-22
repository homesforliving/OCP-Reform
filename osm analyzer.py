import os
import pandas as pd
import geopandas as gpd
import googlemaps
import matplotlib.pyplot as plt
import plotly
import plotly.express as px
import time

#chart studio
import chart_studio
import chart_studio.plotly as py
import plotly.io as pio

from inspect import getsourcefile
from os.path import abspath
#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

amenities = gpd.read_file("osm_data/OSM_export_victoria.geojson")

#convert to WGS 84
amenities = amenities.to_crs('epsg:4326')

#only need centroid, not polygon
amenities["geometry"] = amenities["geometry"].centroid

print("UNIQUE AMENITIES:")
print(amenities.amenity.unique())

for amenity in amenities.amenity.unique():
    #if not NaN:
    if(amenity == amenity):

        print("Collecting data for " + str(amenity))

        gdf = amenities[amenities["amenity"] == amenity]
        
        #create a new gdf with: name, geometry = geometry centroid
        gdf = gdf[["name", "geometry"]]

        #create pd df with columns: Name, Latitude, Longitude
        df = pd.DataFrame(columns=["Name", "Latitude", "Longitude"])

        df["Name"] = gdf["name"]
        df["Latitude"] = gdf["geometry"].y
        df["Longitude"] = gdf["geometry"].x

        #to csv
        df.to_csv("amenity data/" + amenity + ".csv", index=False)

    #create new df with two columns: list of unique amenities that aren't NaN, and the number 1
    weights = pd.DataFrame(columns=["amenity", "weight"])
    weights["amenity"] = amenities.amenity.unique()
    weights["weight"] = 1

    #to csv
    weights.to_csv("amenity weights.csv", index=False)
    
