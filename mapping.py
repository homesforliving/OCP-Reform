import os
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px

#chart studio

import plotly.io as pio
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from inspect import getsourcefile
from os.path import abspath

from OCP_score_generation import aggregate_amenities

#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

#apply OCP score to properties
def apply_score_and_zoning():
    properties = gpd.read_file("CRD Properties/scored_properties.geojson")
    properties = aggregate_amenities(properties)
    properties = properties.to_crs("epsg:26910")

    major_roads = gpd.read_file('Roads/CRD Major Roads.geojson').to_crs('epsg:26910')
    highways = gpd.read_file('Roads/CRD Highways.geojson').to_crs('epsg:26910')

    #combine the two geometries into a blank geodataframe
    roads = gpd.GeoDataFrame(geometry = pd.concat([major_roads.geometry, highways.geometry], ignore_index=True))
    roads_buffer = gpd.GeoDataFrame(geometry=roads.buffer(25))

     #establishes a baseline zoning
    properties['Proposed Zoning'] = 'Missing Middle/Low Rise Apartments'
    properties.loc[properties['OCP Score'] >= 50, 'Proposed Zoning'] = 'Apartments'

    # Perform the spatial join
    intersecting_properties = gpd.sjoin(properties, roads_buffer, how='inner', predicate='intersects')

    #using AddressCombined, find which properties are in intersecting_properties
    #if they are then change zoning to 'Commercial'. Otherwise do nothing.
    for index, row in properties.iterrows():
        if row['AddressCombined'] in intersecting_properties['AddressCombined'].values:
            properties.loc[index, 'Proposed Zoning'] = 'Mixed Use/Commercial'

    properties = properties.to_crs("epsg:4326")

    return(properties)

scored_properties = apply_score_and_zoning()

def map_proposed_ocp(properties):

    legend = {'Missing Middle/Low Rise Apartments':'blue',
              'Apartments':'orange',
              'Mixed Use/Commercial':'green'}

    fig = px.choropleth_mapbox(properties, geojson=properties.geometry, locations=properties.index, color='Proposed Zoning',
                            mapbox_style="carto-positron",
                            zoom=12, center = {"lat": 48.4284, "lon": -123.3656},
                            opacity=.5,
                            color_discrete_map=legend, 
                            category_orders={"Current Zoning":legend.keys()},
                            hover_data = ['AddressCombined', 'amenity_score', 'transit_score', 'OCP Score', 'Current Zoning']
                                )    

    fig.update_traces(marker_line_width=0,
                            hovertemplate = """
                            <b>%{customdata[0]}.</b><br> 
                            <b>Amenity Score:</b> %{customdata[1]}<br>
                            <b>Transit Score:</b> %{customdata[2]}<br>
                            <b>OCP Score:</b> %{customdata[3]}<br>
                            <b>Current Zoning:</b> %{customdata[4]}<br>
                            """                 
                    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    fig.write_html("docs/Maps/A - Proposed Zoning.html")
    fig.write_image(file="docs/Maps/A - Proposed Zoning.png", format="png", width=1920, height=800)

def map_current_zoning(properties):

    properties['Current Zoning'] = properties['Current Zoning'].replace(['Single/Duplex'], 'SFH/Duplex Only')
    #replace everything else with "Other/Unclassified"
    properties['Current Zoning'] = properties['Current Zoning'].replace(['Commercial', 'Missing Middle', 'Comprehensive Development', 'Mixed Use', 'Apartment', 'Industrial', 'Rural Residential', 'Agricultural', 'Recreational', 'Institutional', 'Unclassified'], 'Other')

    legend = {
        "SFH/Duplex Only":"red",
        "Other":"lightgrey"
        }
    
    fig = px.choropleth_mapbox(properties, geojson=properties.geometry, locations=properties.index, color='Current Zoning',
                            mapbox_style="carto-positron",
                            zoom=12, center = {"lat": 48.4284, "lon": -123.3656},
                            opacity=.5,
                            labels = {'Current Zoning':"Simplified Zoning Categories"},
                            color_discrete_map=legend,
                            category_orders={"Current Zoning":legend.keys()},
                            hover_data = ['AddressCombined', 'amenity_score', 'transit_score', 'OCP Score'],
                            hover_name='AddressCombined'
                                )    

    fig.update_traces(marker_line_width=0,             
                            hovertemplate = """
                            <b>%{customdata[0]}.</b><br> 
                            <b>Amenity Score:</b> %{customdata[1]}<br>
                            <b>Transit Score:</b> %{customdata[2]}<br>
                            <b>OCP Score:</b> %{customdata[3]}<br>
                            """                 
                    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    fig.write_html("docs/Maps/B - Current Zoning.html")
    fig.write_image(file="docs/Maps/B - Current Zoning.png", format="png", width=1920, height=800)

    return

def map_amenity_score(properties):
    # Discrete color scales cause huge bloat in the plotly choropleths, so this is
    # a way to create discrete colors using a continuous color scale, for efficiency.
    value_clamps = {
        (0, 24): 0, (25, 49): 33, (50, 74): 67, (75, 100): 100
    }
    for (range, value) in value_clamps.items():
        properties.loc[(properties['amenity_score'] >= range[0]) & (properties['amenity_score'] <= range[1]), 'rating'] = value

    fig = px.choropleth_mapbox(properties, geojson=properties.geometry, locations=properties.index, color='rating',
        color_continuous_scale="cividis",
        mapbox_style="carto-darkmatter",
        zoom=12, center = {"lat":  48.431699, "lon": -123.319873},
        opacity=0.5,
        hover_data = ['AddressCombined', 'amenity_score', 'Current Zoning']
    )

    fig.update_traces(hovertemplate = """
    <b>%{customdata[0]}.</b><br> 
    <b>Amenity Score:</b> %{customdata[1]}<br>
    <b>Current Zoning:</b> %{customdata[2]}<br>""")
    
   # set color bar title and labels
    colorbar = dict(
    title = 'Amenity Score',
    tickmode='array',
    tickvals=[1,33,67,100],
    ticktext=['Poor','Fair', 'Good', 'Excellent'],
    tickfont={
        'size': 20
    }
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar=colorbar
    )

    #also plot amenities
    amenities = pd.DataFrame()
    amenity_files = os.listdir('amenity data')
    for file in amenity_files:
        df = pd.read_csv('amenity data/'+file)
        #convert to gdf using Latitude	Longitude
        amenities = pd.concat([amenities, df], ignore_index=True)

    #plot amenities
    amenities['color'] = 'red'
    fig2 = px.scatter_mapbox(amenities, lat="Latitude", lon="Longitude", hover_name="name", mapbox_style="carto-darkmatter", zoom=12, center = {"lat":  48.431699, "lon": -123.319873}, opacity=.7, hover_data=['name'])

    #create hover template
    fig2.update_traces(hovertemplate = "<b>%{customdata[0]}.</b><br>"
                    )

    #add fig2 to fig
    fig.add_trace(fig2.data[0])

    fig.write_html("docs/Maps/C - Amenity Score.html")
    fig.write_image(file="docs/Maps/C - Amenity Score.png", format="png", width=1920, height=800)
    
    return

def map_transit_score(properties):

    transit_route_shps = gpd.read_file("transit data/google_transit/shapes.csv")
    trips = gpd.read_file("transit data/google_transit/trips.csv")
    routes = gpd.read_file("transit data/google_transit/routes.csv")

    #correlate shape_id with route_id
    transit_route_shps = transit_route_shps.merge(trips[['route_id', 'shape_id']], on = 'shape_id')
    transit_route_shps = transit_route_shps.drop_duplicates()
    #do the same for route_id and route_short_name in trips.csv
    transit_route_shps = transit_route_shps.merge(routes[['route_id', 'route_short_name']], on = 'route_id')
    #delete duplicate rows
    transit_route_shps = transit_route_shps.drop_duplicates()
    transit_route_shps = transit_route_shps.rename(columns = {'route_short_name': 'Route'})
    transit_route_shps = transit_route_shps.drop(columns = ['geometry', 'route_id'])

    #convert Route column to int
    transit_route_shps['Route'] = transit_route_shps['Route'].astype(int)

    rtn_routes = [95, 15, 70]
    ftn_routes = [4,6,11,14,26,27,28]
    local_routes = [1,2,5,3,7,8,9,10,11,12,13,17,21,22,24,25,30,31,32,35,39,43,46,47,48,50,51,52,53,54,55,56,57,58,59,60,61,63,64,65,71,72,75,81,82,83,85,87,88]

    #add route type column to transit routes
    transit_route_shps['route_type'] = np.nan

    #set route type
    transit_route_shps.loc[transit_route_shps['Route'].isin(rtn_routes), 'route_type'] = 'RTN'
    transit_route_shps.loc[transit_route_shps['Route'].isin(ftn_routes), 'route_type'] = 'FTN'
    transit_route_shps.loc[transit_route_shps['Route'].isin(local_routes), 'route_type'] = 'LTN'

    route_color_legend = {'RTN': 'orange',
                    'FTN': 'blue',
                    'LTN': 'grey',
                    }

    fig_1 = px.line_mapbox(transit_route_shps, lat="shape_pt_lat", lon="shape_pt_lon", color="route_type", line_group="shape_id", mapbox_style="carto-darkmatter", zoom=12, center = {"lat":  48.431699, "lon": -123.319873}, color_discrete_map=route_color_legend)

    #add title to fig_1 legend
    fig_1.update_layout(legend_title_text='Route Type')

    fig = px.choropleth_mapbox(properties, geojson=properties.geometry, locations=properties.index, color='transit_score',
                                color_continuous_scale=[(0, "white"), (1, "green")],
                                mapbox_style="carto-darkmatter",
                                zoom=12, center = {"lat":  48.431699, "lon": -123.319873},
                                opacity=.5,
                                hover_data = ['AddressCombined', 'amenity_score', 'transit_score', 'OCP Score', 'Current Zoning', 'Proposed Zoning']
                                )

    fig.update_traces(hovertemplate = """
                            <b>%{customdata[0]}.</b><br> 
                            <b>Amenity Score:</b> %{customdata[1]}<br>
                            <b>Transit Score:</b> %{customdata[2]}<br>
                            <b>OCP Score:</b> %{customdata[3]}<br>
                            <b>Current Zoning:</b> %{customdata[4]}<br>
                            <b>Proposed Zoning:</b> %{customdata[5]}<br>
                            """
                    )
    
   # set color bar title and labels
    colorbar = dict(
    title = 'Transit Score',
    tickmode='array',
    tickvals=[properties['transit_score'].min(), 100],
    ticktext=['Poor transit','Great transit'],
    len=0.8,
    #position it at the bottom
    yanchor='bottom',
    y = 0
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  coloraxis_colorbar=colorbar
                  )
    
    #add all traces in fig_1 to fig
    for data in fig_1.data:
        fig.add_trace(data)
    
    fig.write_html("docs/Maps/D - Transit Score.html")
    fig.write_image(file="docs/Maps/D - Transit Score.png", format="png", width=1920, height=800)
    
    return

def map_top_50(properties):

    #select properties with OCP score >= .5
    properties = properties[properties['OCP Score'] >= 50]

    #Select only properties in single/duplex zones
    properties = properties[properties['Current Zoning'] == 'Single/Duplex']

    fig = px.choropleth_mapbox(properties, geojson=properties.geometry, locations=properties.index, color='OCP Score',
                                color_continuous_scale="cividis",
                                mapbox_style="carto-darkmatter",
                                zoom=12, center = {"lat":  48.431699, "lon": -123.319873},
                                opacity=.5,
                                #set min
                                range_color=[1, 100],
                                hover_data = ['AddressCombined', 'amenity_score', 'transit_score', 'OCP Score', 'Current Zoning', 'Proposed Zoning']
                                )

    fig.update_traces(marker_line_width=0,
                            hovertemplate = """
                            <b>%{customdata[0]}.</b><br> 
                            <b>Amenity Score:</b> %{customdata[1]}<br>
                            <b>Transit Score:</b> %{customdata[2]}<br>
                            <b>OCP Score:</b> %{customdata[3]}<br>
                            <b>Current Zoning:</b> %{customdata[4]}<br>
                            <b>Proposed Zoning:</b> %{customdata[5]}<br>
                            """
                    )
       # set color bar title and labels
    colorbar = dict(
    title = 'Amenity Score',
    tickmode='array',
    tickvals=[1, 100],
    ticktext=['0', '100']
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  coloraxis_colorbar=colorbar
                  )
    #zero margin
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    #to html
    fig.write_html("docs/Maps/E - Top 50.html")
    fig.write_image(file="docs/Maps/E - Top 50.png", format="png", width=1920, height=800)

    return

#Call each map function
map_proposed_ocp(scored_properties)
map_current_zoning(scored_properties)
map_amenity_score(scored_properties)
map_transit_score(scored_properties)
# map_top_50(scored_properties)