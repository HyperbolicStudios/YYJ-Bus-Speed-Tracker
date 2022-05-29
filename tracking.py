import time
from datetime import datetime
import pytz
from pytz import timezone

import pandas as pd
from google.transit import gtfs_realtime_pb2
import requests
import os
from inspect import getsourcefile
from os.path import abspath
import datetime
import traceback
import asyncio

from mapping import map
#from graphing import graph_variables
#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

url = "http://victoria.mapstrat.com/current/gtfrealtime_VehiclePositions.bin"
trips = pd.read_csv("google_transit/trips.csv")

def get_feed():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(url)
    feed.ParseFromString(response.content)
    return(feed)

def get_trip_data(id): #searches the csv file and returns trip data (route #, direction, etc.)
    return(trips.loc[trips['trip_id']==int(id)])

def snapshot():
    results = pd.DataFrame(columns = ["Route","Time","Speed","x","y","Notes"])
    feed = get_feed()
    for entity in feed.entity:
        try:
            trip = get_trip_data(entity.vehicle.trip.trip_id)
            header = trip.trip_headsign.values[0]
            utc_date = datetime.datetime.utcfromtimestamp(feed.header.timestamp)
            local_time = pytz.utc.localize(utc_date).astimezone(pytz.timezone('US/Pacific')).strftime("%H:%M:%S")
            speed = int(entity.vehicle.position.speed)*3.6 #converts to km/hr
            x = entity.vehicle.position.longitude
            y = entity.vehicle.position.latitude
            note = "Route: {}   Time: {}   Speed: {} km/hr".format(header,local_time,speed)
            #print(note)
            result = pd.DataFrame(data = {"Route":[header],"Time":[local_time],"Speed":[speed],"x":[x],"y":[y],"Notes":note},columns = ["Route","Time","Speed","x","y","Notes"])
            results = pd.concat([results, result], ignore_index = True, axis = 0)
        except:
            pass
    results.to_csv("output/snapshot.csv".format(local_time))
    return

async def track(bus_id):
    results = pd.DataFrame(columns = ["Route","Time","Speed","x","y","Notes"])
    start_time = datetime.datetime.now()
    old_feed = 0
    fail_counter = 0
    while(datetime.datetime.now()-start_time).total_seconds() < 60*60:
        try:
            feed = get_feed()

            print("Updated feed. Old feed == new feed: {}".format(old_feed == feed))
            print(feed.header.timestamp)
            for entity in feed.entity:
                id = entity.vehicle.vehicle.id
                if(id == bus_id):
                    trip = get_trip_data(entity.vehicle.trip.trip_id)
                    header = trip.trip_headsign.values[0]
                    utc_date = datetime.datetime.utcfromtimestamp(feed.header.timestamp)
                    local_time = pytz.utc.localize(utc_date).astimezone(pytz.timezone('US/Pacific')).strftime("%H:%M:%S")
                    speed = int(entity.vehicle.position.speed)*3.6 #converts to km/hr
                    x = entity.vehicle.position.longitude
                    y = entity.vehicle.position.latitude
                    note = "Route: {}   Time: {}   Speed: {} km/hr".format(header,local_time,speed)
                    print(note)
                    result = pd.DataFrame(data = {"Route":[header],"Time":[local_time],"Speed":[speed],"x":[x],"y":[y],"Notes":note},columns = ["Route","Time","Speed","x","y","Notes"])
                    results = pd.concat([results, result], ignore_index = True, axis = 0)
                    results.to_csv("output/"+(results["Route"][0]+".csv").replace("/",""))
            old_feed = feed
            fail_counter = 0
            await asyncio.sleep(10)
        except:
            traceback.print_exc()
            fail_counter = fail_counter+1
            if(fail_counter > 3):
                break
    return("Done")
snapshot()
