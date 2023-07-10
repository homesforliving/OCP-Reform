import os
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px

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

def create_property_scores():
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

    properties = gpd.read_file("CRD Properties/core muni properties dissolved.geojson")
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

    properties = properties.to_crs('epsg:4326') 

    #MERGE WITH HFL ZONING DATA

    #import zoning data
    zoning = gpd.read_file('zoning/Harmonized_Zones.shp')
    zoning = zoning[['SIMPLIFIED', 'geometry']]
    zoning = zoning.to_crs('epsg:4326')
    zoning = zoning.rename(columns={'SIMPLIFIED': 'Current Zoning'})

    #perform spatial join. Find zoning for each property, create 'zone' column in properties with zoning.
    #zoning has a 'SIMPLIFIED' column. This is the zoning type.
    print(len(properties))

    original_geometry = properties.geometry
    
    #Zoning maps being aligned with the edge of properties is causing multiple zones to be assigned to each property.
    #Scaling properties down by 70% to fix most of this. Doesn't always work.

    properties.geometry = properties.geometry.scale(xfact=0.7, yfact=0.7, zfact=0.7, origin="centroid")
    properties = gpd.sjoin(properties, zoning, how='left', predicate='intersects')
    properties.geometry = original_geometry

    #if there's multiple rows with the same geometry/Address, go with the first one. There's a few edge cases where this happens and it's on my list of things to investigate.
    properties = properties.drop_duplicates(subset=['geometry'], keep='first')
    properties = properties.drop_duplicates(subset=['AddressCombined'], keep='first')

    print(len(properties))
    properties = properties.reset_index(drop=True)
    properties = properties.drop(columns=['index_right'])

    properties.to_file("CRD Properties/scored_properties.geojson", driver='GeoJSON')

    return

def aggregate_amenities(properties):
    
    #import weights
    weights = pd.read_csv('amenity weights.csv')

    properties['amenity_score'] = 0

    #for coloumns that aren't index, AddressCombined, transit_score, or geometry:
    #multiply by weight
    #add to amenity_score
    properties = properties.to_crs('epsg:4326')

    for col in properties.columns:
        if(col not in ['index', 'AddressCombined', 'transit_score', 'geometry','amenity_score', 'Current Zoning']):
            print(col)
            w = weights[weights['amenity'] == col]['weight'].values[0]
            properties[col] = properties[col].astype(int)
            properties['amenity_score'] = properties['amenity_score'] + w*properties[col]
    
    #normalize amenity score from 0 to 1
    properties['amenity_score'] = properties['amenity_score']/properties['amenity_score'].max()
    
    #transit_score is from 0 to 1. arbitrary weights
    properties['OCP Score'] = 0.5*properties['transit_score'] + 0.5*properties['amenity_score']

    properties = properties[['geometry', 'AddressCombined', 'amenity_score', 'transit_score', 'OCP Score', 'Current Zoning']]

    #multiply by 100 and then round to an integer using round()
    properties['amenity_score'] = round(100*properties['amenity_score'])
    properties['transit_score'] = round(100*properties['transit_score'])
    properties['OCP Score'] = round(100*properties['OCP Score'])

    return(properties)

#call this function before running mapping

#create_property_scores()