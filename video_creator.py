import time
import datetime
import pytz
from pytz import timezone

import os
from inspect import getsourcefile
from os.path import abspath
import re
import traceback

from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile
import shutil

import pandas as pd
import numpy as np

import pymongo
import dns.resolver

import plotly
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio


mapbox_access_token = os.environ['MAPBOX_KEY']

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

def download_from_mongo(month,day):

    e1 = int(time.mktime(datetime.datetime(2023, month, day, 0, 0, 0, 0, pytz.timezone('US/Pacific')).timetuple()))
    e2 = int(time.mktime(datetime.datetime(2023, month, day, 23, 59, 59, 0, pytz.timezone('US/Pacific')).timetuple()))+3*3600
        
    myquery = { "Time": { "$gt": e1, "$lt": e2 } }
    mydoc = mycol.find(myquery)
    df = pd.DataFrame(list(mydoc))
    df = df.drop(columns = ["_id"])
    return(df)

def create_frames(df):
    #eliminate duplicate entries
    df = df.drop_duplicates().reset_index(drop = True)

    #get list of times
    times = df["Time"].unique()
    l = len(times)

    #see what frames already exist in the folder - if they exist, don't overwrite them
    png_files = [f for f in os.listdir('output/frames') if f.endswith('.png')]
    if png_files != []:
        # Sort the file names in numerical order
        png_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))

        #get the number of the last file
        last_file = png_files[-1]
        last_file_number = int(re.findall(r'\d+', last_file)[0])
    else:
        last_file_number = -1
    
    for i in range(last_file_number+1, l):
        time = times[i]
        snapshot = df[df["Time"] == time]

        fig = go.Figure(go.Scattermapbox(
            lat=snapshot["y"],
            lon=snapshot["x"],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=8,
                color = snapshot["Speed"],
                colorscale =  [(0, "red"), (.25, "yellow"), (.5, "green"), (1, "darkgreen")],
                colorbar_title="Speed (Km/Hr)",
                #set range of scale
                cmin = 0,
                cmax = 80
            )))

        fig.update_layout(
            
            title_x = 0.5,
            hovermode='closest',
            width = 1600,
            height = 912,
            margin=dict(l=0, r=0, t=0, b=0),
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=go.layout.mapbox.Center(
                    lat= 48.449454,
                    lon= -123.425040
                ),
                pitch=0,
                zoom=11
            ))
        #export to jpg
        print("Generated fig {} of {}".format(i+1, l))
        #export to htlp
        #fig.write_html("output/frames/frame" + str(i) + ".html")
        file_name = "output/frames/frame" + str(i) + ".png"
        fig.write_image(file_name.format(i),engine='orca')

            # Open the PNG file
        image = Image.open(file_name)

        # Create a draw object and get the image dimensions
        draw = ImageDraw.Draw(image)
        width, height = image.size

        # Load the font and set the font size
        font = ImageFont.truetype('arial.ttf', 30)

        # Get the text size of the timestamp string
        timestamp = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
        text_bbox = draw.textbbox((0, 0), timestamp, font=font)

        # Calculate the position of the timestamp string
        x = width - text_bbox[2] - 300
        y = height - text_bbox[3] - 100
        draw.text((x, y), timestamp, fill='orange', font=font)

        # Return the modified image object
        image.save(file_name)
        
    return
#create_frames()
def create_video():
    # Set up the path to PNG files
    png_dir = 'output/frames'

    # Create a list of file names in the directory
    png_files = [f for f in os.listdir(png_dir) if f.endswith('.png')]

    # Sort the file names in numerical order
    
    png_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))

    # Create an output file name for the video
    output_file = 'output/output.mp4'

    # Create a writer object to write the video
    writer = imageio.get_writer(output_file, fps=30)

    # Loop through each PNG file and add it to the video
    for png_file in png_files:
        file_path = os.path.join(png_dir, png_file)
        image = imageio.imread(file_path)
        writer.append_data(image)

    # Close the writer object to save the video
    writer.close()
    return

df = download_from_mongo(month=4,day=13)
create_frames(df)
create_video()


