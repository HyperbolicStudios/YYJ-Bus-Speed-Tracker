import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import time
from inspect import getsourcefile
from os.path import abspath

from shapely.geometry import LineString, Point, MultiPoint

from shapely.ops import split

import plotly.graph_objs as go


#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

def retrieve_timeline():
    timeline = pd.read_csv("output/timeline.csv")

    #select Route = 50
    timeline = timeline[timeline["Route"] == '50']

    #turn into geopandas dataframe based on x and y
    timeline = gpd.GeoDataFrame(timeline, geometry=gpd.points_from_xy(timeline.x, timeline.y))
    timeline = timeline.set_crs("EPSG:4326").to_crs("EPSG:26910")

    return(timeline)

def generate_lines():
    print("Reading data...")
    
    trips_csv = pd.read_csv("google_transit/trips.csv")
    shapes_csv = pd.read_csv("google_transit/shapes.csv")
    #find first shape_id for routewith Headsign == "50 Downtown"
    #select Headsign == "50 Downtown"
    trips = trips_csv[trips_csv["trip_headsign"] == "50 Downtown"]
    #select first shape_id
    shape_id = trips.iloc[0]["shape_id"]
    #select shape_id == shape_id
    shapes = shapes_csv[shapes_csv["shape_id"] == shape_id]

    #turn into geopandas dataframe using shape_pt_lat and shape_pt_lon and set geographical CRS
    shapes = gpd.GeoDataFrame(shapes, geometry=gpd.points_from_xy(shapes.shape_pt_lon, shapes.shape_pt_lat))
    shapes = shapes.set_crs("EPSG:4326").to_crs("EPSG:26910")   

    #shapes is a series of points, ordered by shape_pt_sequence. turn it into a line
    shapes = shapes.sort_values(by="shape_pt_sequence")
    line = LineString(shapes["geometry"])
    
    n = 100
    
    points = ([line.interpolate((i/n), normalized=True) for i in range(1, n)])

    #create lines from points
    lines = []
    for i in range(0, len(points)-1):
        lines.append(LineString([points[i], points[i+1]]))
    
    #create geopandas dataframe from lines
    lines = gpd.GeoDataFrame(geometry=lines)

    """#give each line a different colour from a colourmap
    lines["colour"] = lines.index % 256
    lines.plot(column="colour", cmap="tab20", legend=True)"""
    return(lines)

route_segments = generate_lines()

#create a buffer around each line in lines, and create a new geodataframe with the buffers
buffers = gpd.GeoDataFrame(geometry=route_segments.buffer(100, cap_style=2))
buffers = buffers.set_crs("EPSG:26910")
#create 'datapoints' column in buffers dataframe
#buffers["datapoints"] should be an empty list

#array from 5 to 23 in steps of 1
for timeslot in np.arange(5, 24, 1):
    #create column for each timeslot
    route_segments["{}:00".format(timeslot)] = [[] for i in range(0, len(buffers))]


timeline = retrieve_timeline()

#convert Time to datetime
timeline["Time"] = pd.to_datetime(timeline["Time"])


#get first 1000 datapoints of timeline
timeline = timeline.head(1000)

#for each point in timeline, find which buffer it's in and add the buffer index number to the timeline dataframe
#should take 6 seconds for each 100 speed data points

#start timer
start = time.time()
for i in range(0, len(timeline)):
    for j in range(0, len(buffers)):
        
        if(timeline.iloc[i]["geometry"].within(buffers.iloc[j]["geometry"])):
            ##add datapoint to buffer datapoints
            route_segments.loc[j, "{}:00".format(timeline.iloc[i]["Time"].hour)].append(timeline.iloc[i]["Speed"])
     
            break

print("Took {} seconds to aggregate data.".format(round(time.time() - start)))

print(route_segments)

#for each buffer, calculate the average speed
def average(list):
    if len(list) == 0:
        return(100)
    else:
        return(sum(list)/len(list))
    
for timeslot in np.arange(5, 24, 1):
    #create column for each timeslot
    col = "{}:00".format(timeslot)
    route_segments[col] = route_segments[col].apply(average)



import geopandas as gpd
import plotly.express as px
from shapely.geometry import LineString

#convert df to wg84
df = route_segments.set_crs("EPSG:26910").to_crs("EPSG:4326")

#Create start_lat, start_lon, end_lat, end_lon columns
df["start_lat"] = df["geometry"].apply(lambda x: x.coords[0][1])
df["start_lon"] = df["geometry"].apply(lambda x: x.coords[0][0])
df["end_lat"] = df["geometry"].apply(lambda x: x.coords[1][1])
df["end_lon"] = df["geometry"].apply(lambda x: x.coords[1][0])

#delete geometry column
del df["geometry"]

print(df)

fig = px.line_mapbox(lat=df["start_lat"], lon=df["start_lon"], color=df["5:00"],
                     mapbox_style="stamen-terrain", zoom=1)
fig.update_layout(
                
                  mapbox_zoom=10,
                  mapbox_center_lon=df.loc[:,["start_lon","end_lon"]].mean().mean(),
                  mapbox_center_lat=df.loc[:,["start_lat","end_lat"]].mean().mean(),
                mapbox_style="carto-positron"
                         
                  
                 )
fig.show()