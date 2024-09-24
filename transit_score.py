import numpy as np
import pandas as pd
import geopandas as gpd
from geopandas.tools import sjoin

import os
from inspect import getsourcefile
from os.path import abspath
import matplotlib.pyplot as plt

import plotly.express as px
#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

def transit_score_v2():

    properties = gpd.read_file("CRD Properties/core muni properties dissolved.geojson")
    #drop all columns except geometry and AddressCombined
    properties = properties[['geometry', 'AddressCombined']]

    properties = properties.to_crs('epsg:26910')

    #check for invalid geometries
    properties = properties[properties.is_valid]

    properties['Trip Count'] = 0

    trips = pd.read_csv("transit data/google_transit/trips.csv")
    stop_times = pd.read_csv("transit data/google_transit/stop_times.csv")
    stops = pd.read_csv("transit data/google_transit/stops.csv")
    routes = pd.read_csv("transit data/google_transit/routes.csv")
    calendar = pd.read_csv("transit data/google_transit/calendar.csv")

    #find the service id that is active on monday
    service_id = calendar[calendar.monday == 1]['service_id'].iloc[0]

    trips = trips[trips.service_id == service_id]
    trips = trips[trips.direction_id == 0]

    for route in trips.route_id.unique():
        print(route)
        #count the number of trips that route has
        trip_count = len(trips[trips['route_id'] == route])
        #get the first trip_id for each route
        trip_id = trips[trips['route_id'] == route]['trip_id'].iloc[0]
        stops_ids = stop_times[stop_times['trip_id'] == trip_id]['stop_id']
        route_stops = stops[stops['stop_id'].isin(stops_ids)]

        #create a gdf from stops
        route_stops = gpd.GeoDataFrame(route_stops, geometry=gpd.points_from_xy(route_stops.stop_lon, route_stops.stop_lat))
        #set to wgs
        route_stops = route_stops.set_crs("epsg:4326").to_crs("epsg:26910")
        buffer = gpd.GeoDataFrame(geometry=route_stops.buffer(400,resolution=1))

        #figure out which properties are within the buffer. If there are any, add the trip count to the property Trip Count column
        
        properties['Trip Count'] += trip_count*properties['geometry'].apply(lambda x: any(x.intersects(geom) for geom in buffer['geometry']))


#export to geojson
    properties.to_file("transit_scores.geojson", driver='GeoJSON')

    #plot
    properties.plot(column='Trip Count', legend=True)
    plt.show()

    print("Finished transit score")
    return(properties)


def plot_transit_score_v2():
    properties = gpd.read_file("transit_scores.geojson")
    properties = properties.to_crs("epsg:4326")

    #map with plotly
    fig = px.choropleth_mapbox(properties, geojson=properties.geometry, locations=properties.index, color='Trip Count',
                            color_continuous_scale="Viridis",
                            range_color=(0, 200),
                            mapbox_style="carto-positron",
                            zoom=10, center = {"lat": 48.4284, "lon": -123.3656},
                            opacity=0.5,
                            
                            labels={'Trip Count':'Trip Count'}
                              )
    fig.update_traces(marker_line_width=0)

    fig.show()

transit_score_v2()
plot_transit_score_v2()
#scores transit access from 0 to 1 for each property in properties
#score is scaled logarithmically, I mapped it and it looked fine. definitely is something to improve on though
def transit_score(properties):

    stops = pd.read_csv("transit data/google_transit/stops.csv")

    stop_times = pd.read_csv("transit data/google_transit/stop_times.csv")

    def fix_hour(hour_str):
        x = hour_str.find(':')
        hour = int(hour_str[:x])
        if hour >= 24:
            hour -= 24
        return(f'{hour:02d}{hour_str[x:]}')

    # Apply the fix_hour function to arrival_time
    stop_times['arrival_time'] = stop_times['arrival_time'].apply(fix_hour)

    stop_times['arrival_time'] = pd.to_datetime(stop_times['arrival_time'])

    print("Fixed stop data")

    def lookup(stop_id):
        #count how many times stop_id appears in stop_times['stop_id'] and arrival time is after 22:00
        #departure_time column has data like 16:25:00
        
        count = len(stop_times[stop_times["stop_id"] == stop_id])
        return(count)

    #main map
    stops['weekly_buses'] = stops['stop_id'].apply(lookup)

    #generate gdf from stop_lat, stop_lon
    stops = gpd.GeoDataFrame(stops, geometry=gpd.points_from_xy(stops.stop_lon, stops.stop_lat))
    #set to wgs
    stops = stops.set_crs("epsg:4326")
    #drop everything except for stop_id, count, and geometry
    stops = stops[['stop_id','weekly_buses','geometry']]

    #spatial join between properties and gdf. Find out how many 'counts' are within a 400m buffer of each property

    #convert to nad83 utm zone 10n)
    properties = properties.to_crs("epsg:26910")
    stops = stops.to_crs("epsg:26910")

    # Create a buffer around each property
    buffered_properties = properties.copy()
    buffered_properties.geometry = properties.geometry.buffer(400)

    # Perform spatial join
    joined = sjoin(buffered_properties, stops, predicate='contains')

    # Group by property and sum the weekly bus count
    grouped = joined.groupby('AddressCombined')['weekly_buses'].sum()

    # Join the result back to the original properties GeoDataFrame
    result = properties.merge(grouped, left_on='AddressCombined', right_index=True)

    result['transit_score'] = np.log2(result['weekly_buses'])
    #scale results to 0-1
    result.transit_score = result.transit_score / result.transit_score.max()
    result.drop(columns=['weekly_buses'], inplace=True)
    #plot by weekly_buses
    #result.plot(column='weekly_buses', legend=True)
    #plt.show()

    print("Finished transit score")
    return(result)