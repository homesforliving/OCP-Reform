import os
import pandas as pd
import geopandas as gpd

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

# property_exclude_list is a list of properties that should not be included in
# in the output.
# Street names should be all uppercase.
property_exclude_list = [
    '100 Cook St', # Beacon Hill Park
    '1495 Fairfield Rd', # Ross Bay Cemetery
    '1401 Rockland Ave', # Government House
]

#deletes invalid geometries
#also: properties data shows small boxes for apartments, condos, etc.
#this function simplifies the shapefile and combines them all to reduce processing needs
def simplify_properties():

    #data from here: https://hub.arcgis.com/datasets/SIPP::crd-properties/explore?layer=3&location=48.440229%2C-123.278142%2C13.00
    properties = gpd.read_file("CRD Properties/CRD_Properties.geojson")
    properties = properties[properties['geometry'].is_valid]
    
    properties['City'] = None
    
    #Each city has a jurisdiction code. 317 is Oak Bay, Esquimalt is 307, City of Victoria is 234, and Saanich is 308, 309, or 389

    #the relevant column is '"BCAJurisdiction' and stores data as text
    #Create a column called City and fill it with the appropriate city name
    def code_to_city(code):
        if code == '317':
            return 'OB'
        elif code == '307':
            return 'ES'
        elif code == '234':
            return 'VC'
        elif code in ['308', '309', '389']:
            return 'SN'
        return(None)
    
    properties['City'] = properties['BCAJurisdiction'].apply(code_to_city)

    properties = properties[properties['City'].isin(['VC', 'OB', 'ES', 'SN'])]
    properties = properties[['Folio', 'City', 'StreetName', 'StreetNumber', 'geometry']]
    properties['AddressCombined'] = properties['StreetNumber'].astype(str) + ' ' + properties['StreetName']
    
    #remove properties that are in the exclude list
    properties = properties[~properties['AddressCombined'].isin(property_exclude_list)]
    
    #dissolve shapes with the same AddressCombined
    properties = properties.dissolve(by='AddressCombined')

    #print number of rows
    print('Number of rows: ' + str(len(properties.index)))

    #to geojson
    properties.to_file("CRD Properties/core muni properties dissolved.geojson", driver='GeoJSON')

    return

simplify_properties()