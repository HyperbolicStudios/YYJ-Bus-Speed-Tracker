import time
import datetime

import pytz
from pytz import timezone

import requests
import os
from inspect import getsourcefile
from os.path import abspath

from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile
import shutil

import traceback
import pandas as pd
import numpy as np

import pymongo
import dns.resolver
from google.transit import gtfs_realtime_pb2

from mapping import map

dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

client = pymongo.MongoClient(os.environ['MONGO_URL'])
mydb = client.Cluster0

mycol = mydb["transit_speed_data"]
header_col = mydb["headers"]
trip_id_col = mydb["trip_ids"]

#from graphing import graph_variables
#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

def update_static():
    url = "https://bct.tmix.se/Tmix.Cap.TdExport.WebApi/gtfs/?operatorIds=48"
    
    try:
        shutil.rmtree('google_transit')
    except:
        pass

    http_response = urlopen(url)
    zipfile = ZipFile(BytesIO(http_response.read()))
    zipfile.extractall(path='google_transit')

    for filename in os.listdir('google_transit'):
        print(filename)
        newname = filename[:-3]+'csv'
        os.rename('google_transit/'+filename,'google_transit/'+newname)
        time.sleep(.5)

    print("Updated static GTFS data from " + url)
    return

def get_headers_df():
    #get all headers from mongodb and create a pandas dataframe. Return the dataframe. Columns are HeaderID and Header
    myquery = {}
    mydoc = header_col.find(myquery)
    df = pd.DataFrame(list(mydoc))
    #df = df.drop(columns=["_id"])

    #if blank, return empty dataframe with columns HeaderID and Header
    if df.empty:
        df = pd.DataFrame(columns = ["Header_ID","Header"])
        df = pd.concat([df, pd.DataFrame([{"Header_ID": 0, "Header": "Placeholder"}])], ignore_index=True)
    return df

def get_trip_ids_df():
    myquery = {}
    mydoc = trip_id_col.find(myquery)
    df = pd.DataFrame(list(mydoc))
    
    if df.empty:
        df = pd.DataFrame(columns = ["Trip_ID_ref", "Trip_ID"])
        df = pd.concat([df, pd.DataFrame([{"Trip_ID_ref": 0, "Trip_ID": 0}])], ignore_index=True)
    return df

update_static()

trips = pd.read_csv("google_transit/trips.csv")
routes = pd.read_csv("google_transit/routes.csv")

def get_feed(url="https://bct.tmix.se/gtfs-realtime/vehicleupdates.pb?operatorIds=48"):
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(url)
    feed.ParseFromString(response.content)
    return feed

def snapshot():
    headers_df = get_headers_df()
    trip_ids_df = get_trip_ids_df()
    results = pd.DataFrame(columns = ["Route","Time","Speed","x","y","Notes"])
    feed = get_feed()
       
    if mycol.count_documents({"Time": feed.header.timestamp}) == 0:
        print("New feed, timestamp = {}. Logging to Mongo...".format(feed.header.timestamp))
        for entity in feed.entity:
            try:
                trip_data = trips.loc[trips['trip_id']==entity.vehicle.trip.trip_id]
                header = trip_data.trip_headsign.values[0]
            except:
                header = "Null"

            if header != "Null":
                
                route_id = entity.vehicle.trip.route_id
                route = routes.loc[routes['route_id'] == route_id]
                route_short_name = route['route_short_name'].values[0]

                speed = round(int(entity.vehicle.position.speed)*3.6,1) #converts to km/hr

                #check if header is already in the headers collection. If not, add it in and increment the headerID from the last headerID. If it is in, get the headerID and set header to the headerID
                #This scheme helps reduce storage space in the database
                if header in headers_df.values:
                    header_ID = int(headers_df.loc[headers_df['Header'] == header]['Header_ID'].values[0])
                else:
                    header_ID = int(headers_df['Header_ID'].max() + 1)
                    new_row = {
                        "Header_ID": header_ID,
                        "Header": header
                    }

                    header_col.insert_one(new_row)
                    headers_df = get_headers_df()
                #check if trip_id is already in the trip_ids collection. If not, add it in and increment the tripID from the last tripID. If it is in, get the tripID and set trip_id to the tripID
                #This scheme helps reduce storage space in the database
                trip_ID = entity.vehicle.trip.trip_id

                #trip_ID is in format XXXXXX:XXXXXX:block_id - everything after the first colon should yield a unique value
                trip_ID = trip_ID[trip_ID.find(":")+1:]
                trip_ID = trip_ID.replace(":","")
                trip_ID = int(trip_ID)

                if trip_ID in trip_ids_df.values:
                    trip_ID_ref = int(trip_ids_df.loc[trip_ids_df['Trip_ID'] == trip_ID]['Trip_ID_ref'].values[0])
                
                else:
                    trip_ID_ref = int(trip_ids_df["Trip_ID_ref"].max() + 1)
                    new_row = {
                        "Trip_ID_ref": trip_ID_ref,
                        "Trip_ID": trip_ID
                    }

                    trip_id_col.insert_one(new_row)
                    trip_ids_df = get_trip_ids_df()
                    
                new_mongo_row = {
                    "Time": feed.header.timestamp,
                    "Route": route_short_name,
                    "Header": header_ID, #'compressed' header
                    "Trip ID": trip_ID_ref, #'compressed' trip_id
                    "Speed": speed,
                    "x": entity.vehicle.position.longitude,
                    "y": entity.vehicle.position.latitude,
                }
                
                mycol.insert_one(new_mongo_row)
                

            utc_date = datetime.datetime.utcfromtimestamp(feed.header.timestamp)
            local_time = pytz.utc.localize(utc_date).astimezone(pytz.timezone('US/Pacific')).strftime("%H:%M:%S")

            speed = round(int(entity.vehicle.position.speed)*3.6,1) #converts to km/hr
            x = entity.vehicle.position.longitude
            y = entity.vehicle.position.latitude
            
            #route_num is the header if header is not available, otherwise it is the route number
            header = header if header == "Null" else route_short_name + ": " + header
            note = "Route: {}   Time: {}   Speed: {} km/hr".format(header,local_time,speed)
            
            result = pd.DataFrame(data = {"Route":[header],"Time":[local_time],"Speed":[speed],"x":[x],"y":[y],"Notes":note},columns = ["Route","Time","Speed","x","y","Notes"])
            results = pd.concat([results, result], ignore_index = True, axis = 0)
        
    return(results) #if no new data, returns empty dataframe

snapshot()