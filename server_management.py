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
import matplotlib.pyplot as plt
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

def download_from_mongo():

    #download all data from mongo
    myquery = {}
    mydoc = mycol.find(myquery)
    df = pd.DataFrame(list(mydoc))
    df = df.drop(columns = ["_id"])
          
    #merge with trip data using trip ID
    #convert Trip Id  and trip_id to int
    df["Trip ID"] = df["Trip ID"].apply(lambda x: int(x))
    trips["trip_id"] = trips["trip_id"].apply(lambda x: int(x))
    df = df.merge(trips, left_on = "Trip ID", right_on = "trip_id", how = "left")
    
    df = df.drop(columns = ["trip_id"])

    #Make df["Route"] the first two letters of df["trip_headsign"]
    df["Route"] = df["trip_headsign"].apply(lambda x: x[:x.find(" ")])
    
    #convert 'time' to a timestamp - ISO-8601 date
    df["Time"] = df["Time"].apply(lambda x: datetime.datetime.utcfromtimestamp(x).strftime('%Y-%m-%dT%H:%M:%SZ'))
    df["Speed"] = df["Speed"].apply(lambda x: round(int(x)*3.6,1)) #converts to km/hr
    
    df.to_csv("output/timeline.csv", index = False)
    return

def upload_to_bigQuery():
    key_path = "service_account.json"

    credentials = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
  
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    #upload to bigquery

    dataset = client.dataset('yyj')
    #create a table 'A'
    table = dataset.table('bus_speeds')

    job_config = bigquery.job.LoadJobConfig(
        schema = [
        bigquery.SchemaField('Time', 'TIMESTAMP'),
        bigquery.SchemaField('Speed', 'FLOAT'),
        bigquery.SchemaField('x', 'FLOAT'),
        bigquery.SchemaField('y', 'FLOAT'),

        bigquery.SchemaField('trip_headsign', 'STRING'),

        bigquery.SchemaField('Route', 'STRING')
        
    ],
    autodetect=False)


    
    
    file = pd.read_csv("output/timeline.csv").head(3)

    #drop all colomns except for ones in the schema
    file = file[["Time","Speed","x","y","trip_headsign","Route"]]

    #make sure data matches schema type
   
    file["Speed"] = file["Speed"].astype(float)
    file["x"] = file["x"].astype(float)
    file["y"] = file["y"].astype(float)
    file["trip_headsign"] = file["trip_headsign"].astype(str)
    file["Route"] = file["Route"].astype(str)


    file.columns = file.columns.str.replace(" ","_")
    file = file.fillna(0)

    print(file)

    job = client.load_table_from_dataframe(file, table, job_config=job_config)  
    print(job)
    print('JSON file loaded to BigQuery')
#upload_to_bigQuery()


def track_and_log_to_mongo():

    while(1):
        feed = get_feed()
        for entity in feed.entity:
            try:
                trip = get_trip_data(entity.vehicle.trip.trip_id)
                new_row = {
                        "Time": feed.header.timestamp,
                        "Trip ID": entity.vehicle.trip.trip_id,
                        "Speed": entity.vehicle.position.speed,
                        "x": entity.vehicle.position.longitude,
                        "y": entity.vehicle.position.latitude,
                        "Occupancy Status": entity.vehicle.occupancy_status
                        }

            except:
                continue
            
            mycol.insert_one(new_row)
        
        print("Logged feed.")
        time.sleep(30)
        return    
    
def fix_speed_unit():
    data = pd.read_csv("output/timeline march-april.csv")
    
    #get epoch of Feb 1, 2023 at 3am, Pacific Time
    epoch = datetime.datetime(2023, 2, 1, 3, 0, 0, 0, pytz.timezone('US/Pacific')).timestamp()

    #get all rows where time is before epoch
    data = data[data["Time"] > epoch]

    data['Speed'] = data['Speed']*3.6

    data.to_csv("output/febuary.csv", index = False)
fix_speed_unit()