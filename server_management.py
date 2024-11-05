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
    
    timestamp = df["Time"].iloc[-1]
    timestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

    df.to_csv("historical speed data/{}-timeline.csv".format(timestamp), index = False)
    return

def clear_mongo():
    #clear all data from mongo
    myquery = {}
    mycol.delete_many(myquery)
    return

def download_and_clear():
    download_from_mongo()
    clear_mongo()
    return

clear_mongo()