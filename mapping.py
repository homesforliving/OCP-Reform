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
import matplotlib.pyplot as plt

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

transit_routes = ['10', '4', '11', '14','15', '95', '2', '5', '7','3','27']

def analyze():
    #list of geodataframes - each one is a different amenity
    ammenities = []
    
    #import ammenities: bus stops, grocery stores, hospitals, etc.  
    #list of files in 'amenity data'
    amenity_files = os.listdir('amenity data')
    for file in amenity_files:
        df = pd.read_csv('amenity data/'+file)
        #convert to gdf using Latitude	Longitude
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
        gdf['amenity'] = file[:-4]
        #wgs84 is the standard lat/long coordinate system
        gdf.crs = 'epsg:4326'
        #convert to NAD UTM 10N
        gdf = gdf.to_crs('epsg:26910')
        ammenities.append(gdf)

    #stops is a geodataframe of all bus stops
    stops = gpd.GeoDataFrame()

    for route in transit_routes:
        stops = gpd.GeoDataFrame(pd.concat([stops,gpd.read_file("transit data/filtered stops/route {} stops.shp".format(route))]))

    stops = stops.to_crs('epsg:26910')

    properties = gpd.read_file("cov properties/cov properties dissolved.geojson")
    #drop all columns except geometry and AddressCombined
    properties = properties[['geometry', 'AddressCombined']]

    properties = properties.to_crs('epsg:26910')

    #check for invalid geometries
    properties = properties[properties.is_valid]

    #buffer stops by 400m
    transit_buffer = stops.buffer(400, resolution = 1)
    amenity_buffers = []
    for amenity in ammenities:
        amenity_buffers.append({'type': amenity.loc[0,'amenity'], 'buffer': amenity.buffer(800, resolution=1)})
        print("Imported {} data".format(amenity.loc[0,'amenity']))

    print("Finished importing amenity data")
    #find properties within transit buffer
    properties = properties[properties.intersects(transit_buffer.unary_union)]

    print("Imported property data")
    properties['amenity_count'] = 0
    properties['label'] = ""

    #reset index
    properties = properties.reset_index()

    for property in properties.index:
        print("Calculating amenities for property {} of {}".format(property, len(properties.index)))
        amenities = []
        for amenity in amenity_buffers:
            if properties.loc[property,'geometry'].intersects(amenity['buffer'].unary_union):
                amenities.append(amenity['type'])
        
        label = ""
        for amenity in amenities:
            label += amenity + ", "
        properties.loc[property,'label'] = label[:-2]
        properties.loc[property,'amenity_count'] = len(amenities)

        
    print("Finished calculating amenities. Mapping...")

    properties = properties.to_crs('epsg:4326')
    properties.to_file("maps/analysis.geojson", driver='GeoJSON')
    
def map(properties):
    properties['amenity_count'] = properties['amenity_count'].astype('int')
    fig = px.choropleth_mapbox(properties, geojson=properties.geometry, locations=properties.index, color='amenity_count',
                                color_continuous_scale="Viridis_r",
                                mapbox_style="carto-positron",
                                
                                zoom=12, center = {"lat":  48.431699, "lon": -123.319873},
                                opacity=.5,
                                hover_data = ['AddressCombined', 'label']
                                )

    fig.update_traces(marker_line_width=.01,
                            hovertemplate = """
                            <b>%{customdata[0]}. Close to:</b><br> 
                            %{customdata[1]}
                            """
                    )
    #zero margin
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    #to html
    fig.write_html("maps/analysis.html")
    
    
    return

#analyze()
map(gpd.read_file("maps/analysis.geojson"))