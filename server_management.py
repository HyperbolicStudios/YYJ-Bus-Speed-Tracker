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
    print("Downloading data from MongoDB")
    #download all data from mongo
    myquery = {}
    mydoc = mycol.find(myquery)
    df = pd.DataFrame(list(mydoc))
    df = df.drop(columns=["_id"])

    earliest_timestamp = df["Time"].min()
    latest_timestamp = df["Time"].max()
    
    earliest_date = datetime.datetime.fromtimestamp(earliest_timestamp).strftime('%Y-%m-%d')
    latest_date = datetime.datetime.fromtimestamp(latest_timestamp).strftime('%Y-%m-%d')
    print("Downloaded. Saving...")

    df.to_csv(f"historical speed data/{earliest_date}_to_{latest_date}-timeline.csv", index=False)
    print("Saved.")
    return

def clear_mongo():
    print("Clearing MongoDB")
    # drop the entire collection
    mycol.drop()
    print("Collection dropped.")
    return

def download_and_clear():
    download_from_mongo()
    clear_mongo()
    return

clear_mongo()

#download_and_clear()