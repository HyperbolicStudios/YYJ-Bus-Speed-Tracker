import pandas as pd
import plotly
import plotly.graph_objects as go
import chart_studio
import chart_studio.plotly as py
import plotly.io as pio
import os
from inspect import getsourcefile
from os.path import abspath
import traceback

#username = 'markedwardson' # your plotly username
#api_key = os.environ["PLOTLY_API_KEY"] # your plotly api key - go to profile > settings > regenerate key
#chart_studio.tools.set_credentials_file(username=username, api_key=api_key)
mapbox_access_token = os.environ['MAPBOX_KEY']

#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

def map(data,title="YYJ Bus Speeds"):

    fig = go.Figure(go.Scattermapbox(
            lat=data["y"],
            lon=data["x"],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=8,
                color = data["Speed"],
                colorscale =  [(0, "red"), (.25, "yellow"), (.5, "green"), (1, "darkgreen")],
                colorbar_title="Speed (Km/Hr)",
                cmin=0,
                cmax = 80
            ),
            text = data["Notes"]
        ))

    fig.update_layout(
        title = title,
        title_x = 0.5,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style = "mapbox://styles/markedwardson/clgbco9rt001z01nw5kb5p0rr",
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=data["y"][1],
                lon=data["x"][1]
            ),
            pitch=0,
            zoom=12
       
    ))

    #x = py.plot(fig,auto_open=True)
    #pio.write_html(fig, file='templates/map.html', auto_open=False)
    return(fig)
