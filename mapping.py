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

    properties['amenity_score'] = 0
    properties['label'] = ""

    #reset index
    properties = properties.reset_index()

    #import weights
    weights = pd.read_csv('amenity weights.csv')
      
    for amenity in amenities:
        
        #amenity is a gdf of amenities of a certain type (e.g. restarants)
        #category of amenity.category (see line 42)
        category = amenity.category[0]
        print("Performing join with " + category + "...")
       
        buffered_properties = properties.copy()
        buffered_properties.geometry = properties.geometry.buffer(400)

        # Perform spatial join
        joined = gpd.sjoin(buffered_properties, amenity, predicate='contains')

        # Group by property (AddressCombined) and count the number of amenities and put this count for each property in a new column
        grouped = joined.groupby('AddressCombined').count()[['category']]

        # Merge with properties
        properties = properties.merge(grouped, how='left', on='AddressCombined')

        #rename category column name to category
        properties = properties.rename(columns={'category':category})

        #replace NaN with 0
        properties[category] = properties[category].fillna(0)

        #increment amenity score
        w = weights[weights['amenity'] == category]['weight'].values[0]
        properties.amenity_score =+ properties[category]*w
        break
    
    print(properties)
    return
    properties.ocp_score = properties.transit_score*.4 + properties.amenity_score*.6
            
    def create_label(row):
        label = ""
        for amenity in amenities:
            if(row[amenity.category[0]] > 0):
                label = label + amenity.category[0] + ", "
        if label != "":
            label = label[:-2]
        return label
    
    properties['label'] = properties.apply(create_label, axis=1)

    #calculate ocp score
    #these weights are arbitrary 
    
        
    print("Finished calculating amenities. Mapping...")

    properties = properties.to_crs('epsg:4326')
    properties.to_file("maps/analysis.geojson", driver='GeoJSON')

    return
    
def map(properties):
    properties['amenity_count'] = properties['amenity_count'].astype('int')
    properties.amenity_count = np.log(properties.amenity_count)/np.log(100)
    fig = px.choropleth_mapbox(properties, geojson=properties.geometry, locations=properties.index, color='ocp_score',
                                color_continuous_scale="cividis",
                                mapbox_style="carto-darkmatter",
                                
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

analyze()
#map(gpd.read_file("maps/analysis.geojson"))