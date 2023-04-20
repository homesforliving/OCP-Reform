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

username = 'markedwardson' # your plotly username
api_key = os.environ["PLOTLY_API_KEY"] # your plotly api key - go to profile > settings > regenerate key
chart_studio.tools.set_credentials_file(username=username, api_key=api_key)

def collect_data(criteria):
    gmaps = googlemaps.Client(os.environ["GOOGLE_MAPS_API"])

    #make a request for all grocery stores within the city of victoria
    location = (48.425798, -123.343924)
    stores = gmaps.places_nearby(location=location, radius=5000, keyword=criteria)

    #get next page of results
    next_page_token = stores["next_page_token"]
    time.sleep(5) #This is required to prevent the API from returning an error
    
    """
    sample response:
    {'html_attributions': [], 'results': [{'business_status': 'OPERATIONAL', 'geometry': {'location': {'lat': 48.4305797, 'lng': -123.3456422}, 'viewport': {'northeast': {'lat': 48.4319060802915, 'lng': -123.3444796697085}, 'southwest': {'lat': 48.4292081197085, 'lng': -123.3471776302915}}}, 'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/shopping-71.png', 'icon_background_color': '#4B96F3', 'icon_mask_base_uri': 'https://maps.gstatic.com/mapfiles/place_api/icons/v2/shoppingcart_pinlet', 'name': 'Vegas market', 'opening_hours': {'open_now': True}, 'photos': [{'height': 1920, 'html_attributions': ['<a href="https://maps.google.com/maps/contrib/110681961810926048360">Rachele Anderson</a>'], 'photo_reference': 'AUjq9jmQ8dPbhjT8vgeWlsLNJrMHvjYFrYlgff8FTxWJEbklW35xVbcqE_ZRh95ZFyrDNm1zBX-8JLPdFv2xZdLICl6ar90JRg_T5oIFA6lX0IGzXQ7ghBbAaMsi1o2tdb376PBzR_sBbRRLkkeuYJgi_mExUlLXAGH5DNwj-hapfj8xYim8', 'width': 1080}], 'place_id': 'ChIJ43qkNWN0j1QRufA3mo9wKqE', 'plus_code': {'compound_code': 'CMJ3+6P Victoria, BC, Canada', 'global_code': '84WRCMJ3+6P'}, 'rating': 4.5, 'reference': 'ChIJ43qkNWN0j1QRufA3mo9wKqE', 'scope': 'GOOGLE', 'types': ['grocery_or_supermarket', 'supermarket', 'point_of_interest', 'store', 'food', 'establishment'], 'user_ratings_total': 37, 'vicinity': 'F-1284 Gladstone Avenue, Victoria'}], 'status': 'OK'}

    """

    #turn stores and stores_next page into a dataframe with: name, lat, long, address
    df = pd.DataFrame(columns=["Name", "Latitude", "Longitude", "Address"])
    for store in stores["results"]:
        name = store["name"]
        lat = store["geometry"]["location"]["lat"]
        long = store["geometry"]["location"]["lng"]
        address = store["vicinity"]
        new_row = pd.DataFrame({"Name": name, "Latitude": lat, "Longitude": long, "Address": address}, index=[0])
        df = pd.concat([df, new_row], ignore_index=True)
    for i in range(0,2):
        try:
            time.sleep(5)
            stores_next_page = gmaps.places_nearby(location=location, radius= 5000, keyword=criteria, page_token=next_page_token)
            next_page_token = stores_next_page["next_page_token"]
        except:
            print("{} pages returned by API".format(i+1))
            break
        
        for store in stores_next_page["results"]:
            name = store["name"]
            lat = store["geometry"]["location"]["lat"]
            long = store["geometry"]["location"]["lng"]
            address = store["vicinity"]
            #add new row using df.concat
            new_row = pd.DataFrame({"Name": name, "Latitude": lat, "Longitude": long, "Address": address}, index=[0])
            df = pd.concat([df, new_row], ignore_index=True)
                

    #to csv
    df.to_csv("{}.csv".format(criteria), index=False)
    return

def map(criteria): #quickly map the data
    #turn into geopandas dataframe
    df = pd.read_csv("{}.csv".format(criteria))
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
    gdf.drop(columns=["Longitude", "Latitude"], inplace=True)
    gdf.crs = "WGS84"
    #convert to NAD 83 10N
    
    gdf = gdf.to_crs("EPSG:26910")
   
    #create new gdf of a diagonal buffer of 400m around each store
    #create empty gdf called buf
    buf = gpd.GeoDataFrame()
    buf.geometry = gdf.buffer(distance=400,resolution=1)
    
    buf = buf.to_crs("WGS84")
    gdf = gdf.to_crs("WGS84")
    buf["Category"] = "Grocery Store"
   
    fig = px.choropleth_mapbox(buf, geojson=buf, locations=buf.index, color="Category",
                              
                                    mapbox_style="carto-positron",
                                    zoom=12, center = {"lat": 48.4284, "lon": -123.3656},
                                    opacity=.5,
                                    #no hover
                                    hover_data=None
    )

    #add title
    fig.update_layout(title_text="{} in City of Victoria (400m Buffer)".format(criteria), title_x=0.5)

    fig1 = px.scatter_mapbox(gdf,
                            lat=gdf.geometry.y,
                            lon=gdf.geometry.x,
                            hover_name="Name",
                            mapbox_style="carto-positron",
                            #colour blue
                            color_discrete_sequence=["blue"],
                            zoom=12, center = {"lat": 48.4284, "lon": -123.3656}
                            )

    fig.add_trace(fig1.data[0])
                                       
    
    py.plot(fig, filename = criteria, auto_open=True)

keyword = "coffee shop"
collect_data(keyword)
map(keyword)