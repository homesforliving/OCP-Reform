#standard stuff
import requests
import warnings
import json
import os
from inspect import getsourcefile
from os.path import abspath

import traceback
import time

import pandas as pd
import numpy as np

#special packages
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile
import shutil

import geopandas #note: much easier to install with conda
import plotly
import plotly.express as px

warnings.filterwarnings("ignore", message="pandas.Float64Index")
warnings.filterwarnings("ignore", message="pandas.Int64Index")

#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

def map(map_type="default"): 
    
    #HfL zoning data. Make sure this data is up to date - check the zoning repo
    #'SIMPLIFIED' column has the zone category.
    zones = geopandas.read_file('zoning/Harmonized_Zones_Dissolved.shp')
    zones = zones.to_crs(epsg=4326)

    if map_type == "default":
        legend = {
            "Commercial":plotly.colors.sequential.Viridis[0],
            "Apartment":plotly.colors.sequential.Viridis[2],
            "Comprehensive Development": plotly.colors.sequential.Viridis[6],
            "Mixed Use":plotly.colors.sequential.Viridis[4],
            "Missing Middle":plotly.colors.sequential.Viridis[8],
            "Single/Duplex":plotly.colors.sequential.Viridis[9],
            "Rural Residential":"rgb(246, 139, 69)",
            "Agricultural":"rgb(246, 139, 69)",
            "Recreational": "green",
            "Industrial": "blue",
            "Institutional": "grey",
            "Unclassified":"white"
            }
        
    elif map_type == "legal_apartments":
        #merge "Apartment" "Mixed use" and "Comprehensive Development" into "Legal Apartments"
        #merge "Commercial" "Missing Middle" "Single/Duplex" and "Industrial" into "Illegal Apartments"
        #merge "Rural Residential" "Agricultural" "Recreational" "Institutional" and "Unclassified" into "Other/Unclassified"
        zones['SIMPLIFIED'] = lambda x: "Legal Apartments" if x in ["Apartment","Comprehensive Development", "Mixed Use"] else "Apartments Illegal" if x in ["Commercial","Missing Middle","Single/Duplex","Industrial"] else "Other/Unclassified" if x in ["Rural Residential","Agricultural","Recreational","Institutional","Unclassified"] else "Unclassified"

        legend = {
            "Legal Apartments":"red",
            "Apartments Illegal":"lightgrey",
            "Other/Unclassified":"white"
            }                     
    else:
        print("Invalid map type.")
        return   

    fig = px.choropleth_mapbox(zones, geojson=zones.geometry, locations=zones.index, color='SIMPLIFIED',
                               color_continuous_scale="Viridis",
                               range_color=(0, 12),
                               mapbox_style="carto-positron",
                               zoom=12, center = {"lat": 48.4284, "lon": -123.3656},
                               opacity=.5,
                               labels = {'SIMPLIFIED':"Simplified Zoning Categories"},
                               color_discrete_map=legend,
                               category_orders={"SIMPLIFIED":legend.keys()}
                               )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                    ))
    
    fig.write_html('maps/zoning.html')
    return

map()