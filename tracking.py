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

#from graphing import graph_variables
#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)


trips = pd.read_csv("google_transit/trips.csv")

def update_static():
    url = "http://victoria.mapstrat.com/current/google_transit.zip"
    
    shutil.rmtree('google_transit')
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

def get_feed(url="http://victoria.mapstrat.com/current/gtfrealtime_VehiclePositions.bin"):

    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(url)
    feed.ParseFromString(response.content)
    return(feed)

def get_trip_data(id): #searches the csv file and returns trip data (route #, direction, etc.)
    return(trips.loc[trips['trip_id']==int(id)])

def snapshot():
    results = pd.DataFrame(columns = ["Route","Time","Speed","x","y","Notes"])
    feed = get_feed()
    
    if mycol.count_documents({"Time": feed.header.timestamp}) == 0:
        print("New feed, timestamp = {}. Logging to Mongo...".format(feed.header.timestamp))
        for entity in feed.entity:
            try:
                trip = get_trip_data(entity.vehicle.trip.trip_id)
                header = trip.trip_headsign.values[0]
            
            except:
                header = "Route data not provided"
        
            if header != "Route data not provided":
             
                new_mongo_row = {
                    "Time": feed.header.timestamp,
                    "Trip ID": entity.vehicle.trip.trip_id,
                    "Speed": entity.vehicle.position.speed,
                    "x": entity.vehicle.position.longitude,
                    "y": entity.vehicle.position.latitude,
                    "Occupancy Status": entity.vehicle.occupancy_status
                }

                mycol.insert_one(new_mongo_row)
                

            utc_date = datetime.datetime.utcfromtimestamp(feed.header.timestamp)
            local_time = pytz.utc.localize(utc_date).astimezone(pytz.timezone('US/Pacific')).strftime("%H:%M:%S")

            speed = round(int(entity.vehicle.position.speed)*3.6,1) #converts to km/hr
            x = entity.vehicle.position.longitude
            y = entity.vehicle.position.latitude
            note = "Route: {}   Time: {}   Speed: {} km/hr".format(header,local_time,speed)
            
            result = pd.DataFrame(data = {"Route":[header],"Time":[local_time],"Speed":[speed],"x":[x],"y":[y],"Notes":note},columns = ["Route","Time","Speed","x","y","Notes"])
            results = pd.concat([results, result], ignore_index = True, axis = 0)
        
    return(results) #if no new data, returns empty dataframe



def audit_live_data():
    feed = get_feed()
    for entity in feed.entity:
        try:
            trip = get_trip_data(entity.vehicle.trip.trip_id)
            header = trip.trip_headsign.values[0]
            return(1)
        except:
            header = "Route data not provided"
    return(0)

#audit_feed_update_time()

"""def audit_feed_update_time(delta,end_time):
    #poll gtfs feed every delta seconds, for end_time seconds
    
    start_time = datetime.datetime.now()
    old_timestamp = 0
    while((datetime.datetime.now()-start_time).total_seconds() < end_time):
        feed = get_feed()
        timestamp = feed.header.timestamp
        if timestamp != old_timestamp:
            print("Updated feed. Delta: {}".format(timestamp-old_timestamp))
            old_timestamp = feed.header.timestamp
        time.sleep(delta)

    return"""


update_static()