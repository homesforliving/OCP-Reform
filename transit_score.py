import numpy as np
import pandas as pd
import geopandas as gpd
from geopandas.tools import sjoin

import os
from inspect import getsourcefile
from os.path import abspath
import matplotlib.pyplot as plt

#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

#scores transit access from 0 to 1 for each property in properties
#score is scaled logarithmically, I mapped it and it looked fine. definitely is something to improve on though
def transit_score(properties):
    stops = pd.read_csv("Transit data/google_transit/stops.csv")

    stop_times = pd.read_csv("Transit data/google_transit/stop_times.csv")

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