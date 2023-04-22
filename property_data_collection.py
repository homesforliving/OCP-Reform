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

#deletes invalid geometries
#also: properties data shows small boxes for apartments, condos, etc.
#this function simplifies the shapefile and combines them all to reduce processing needs
def simplify_properties():
    properties = gpd.read_file("cov properties/cov properties.geojson")

    #remove invalid geometries
    properties = properties[properties.is_valid]
    properties = properties[properties['StreetNumber'].notnull()]

    #utm zone 10n
    #properties = properties.to_crs(epsg=26910)
    #properties.geometry = properties.geometry.buffer(0)

    #make address all upercase
    properties['StreetName'] = properties['StreetName'].str.upper()
    #create pd column of Address Combined that combined StreetNumber and StreetName
    properties['AddressCombined'] = properties['StreetNumber'].astype(str) + ' ' + properties['StreetName']

    #print number of rows
    print('Number of rows: ' + str(len(properties.index)))
    #reduce df to just AddressCombined, City and geometry
    properties = properties[[ 'City', 'AddressCombined',  'geometry']]

    #dissolve shapes with the same AddressCombined
    properties = properties.dissolve(by='AddressCombined')

    #print number of rows
    print('Number of rows: ' + str(len(properties.index)))

    #to geojson
    properties.to_file("cov properties/cov properties dissolved.geojson", driver='GeoJSON')

    properties.plot()
    plt.show()
    return

simplify_properties()