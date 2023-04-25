import os
import pandas as pd
import numpy as np
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
import matplotlib.pyplot as plt

from inspect import getsourcefile
from os.path import abspath

from transit_score import transit_score

#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

def analyze():
    #list of geodataframes - each one is a different amenity
    amenities = []
    
    #import ammenities: bus stops, grocery stores, hospitals, etc.  
    #list of files in 'amenity data'
    amenity_files = os.listdir('amenity data')
    for file in amenity_files:
        df = pd.read_csv('amenity data/'+file)
        #convert to gdf using Latitude	Longitude
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
        gdf['category'] = file[:-4]
        #wgs84 is the standard lat/long coordinate system
        gdf.crs = 'epsg:4326'
        #convert to NAD UTM 10N
        gdf = gdf.to_crs('epsg:26910')
        amenities.append(gdf)

    properties = gpd.read_file("cov properties/core muni properties dissolved.geojson")
    #drop all columns except geometry and AddressCombined
    properties = properties[['geometry', 'AddressCombined']]

    properties = properties.to_crs('epsg:26910')

    #check for invalid geometries
    properties = properties[properties.is_valid]

    #calculate transit score
    print("Calculating transit score...")
    properties = transit_score(properties)

    #reset index
    properties = properties.reset_index()
      
    for amenity in amenities:
        category = amenity['category'][0]
        properties[category] = 0

        buffer = gpd.GeoDataFrame(geometry=amenity.buffer(800,resolution=1))

        # Perform a spatial join operation between the two datasets
        properties_within_buffer = gpd.sjoin(properties, buffer, predicate='intersects')

        # Create a new column called category and assign a value of 1 to all rows
        properties_within_buffer[category] = 1

        # Update the 'amenity' column in the original properties dataset for the properties within the buffer
        properties.loc[properties_within_buffer.index, category] = 1

        print("Analyzed {}. {} amenities in dataset, {} properties within 800m buffer.".format(category, len(amenity), len(properties_within_buffer)))  

    properties.to_crs('epsg:4326')       
    properties.to_file("maps/analysis.geojson", driver='GeoJSON')

    return
    
def map():
    properties = gpd.read_file("maps/analysis.geojson")
    
    #import weights
    weights = pd.read_csv('amenity weights.csv')

    properties['amenity_score'] = 0

    #for coloumns that aren't index, AddressCombined, transit_score, or geometry:
    #multiply by weight
    #add to amenity_score
    properties = properties.to_crs('epsg:4326')
    for col in properties.columns:
        if(col not in ['index', 'AddressCombined', 'transit_score', 'geometry','amenity_score']):
            print(col)
            w = weights[weights['amenity'] == col]['weight'].values[0]
            properties[col] = properties[col].astype(int)
            properties['amenity_score'] = properties['amenity_score'] + w*properties[col]
    
    #normalize amenity score from 0 to 1
    properties['amenity_score'] = properties['amenity_score']/properties['amenity_score'].max()
    
    #transit_score is from 0 to 1. arbitrary weights
    properties['OCP Score'] = 0.5*properties['transit_score'] + 0.5*properties['amenity_score']  

    properties = properties[['geometry', 'AddressCombined', 'amenity_score', 'transit_score', 'OCP Score']]

    fig = px.choropleth_mapbox(properties, geojson=properties.geometry, locations=properties.index, color='OCP Score',
                                color_continuous_scale="cividis",
                                mapbox_style="carto-darkmatter",
                                zoom=12, center = {"lat":  48.431699, "lon": -123.319873},
                                opacity=.5,
                                hover_data = ['AddressCombined', 'amenity_score', 'transit_score', 'OCP Score']
                                )

    fig.update_traces(marker_line_width=.01,
                            hovertemplate = """
                            <b>%{customdata[0]}.</b><br> 
                            <b>Amenity Score:</b> %{customdata[1]}<br>
                            <b>Transit Score:</b> %{customdata[2]}<br>
                            <b>OCP Score:</b> %{customdata[3]}<br>
                            """
                    )
    #zero margin
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    #to html
    fig.write_html("maps/analysis.html")
    
    
    return

analyze()
map()

