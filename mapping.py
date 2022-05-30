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
username = 'markedwardson' # your plotly username
api_key = 'WIAjN7QL8J93lT9a296Q' # your plotly api key - go to profile > settings > regenerate key
chart_studio.tools.set_credentials_file(username=username, api_key=api_key)

#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

mapbox_access_token = "pk.eyJ1IjoibWFya2Vkd2FyZHNvbiIsImEiOiJjbDNjanIwMTYwMWZ1M2JxdjlpM2FoZG45In0.yHtIIsPy7ch-Qv_q45jqNQ"

def map(filename,toHTML=False,title=None):
    if title is None:
        title=filename[filename.find("/")+1:filename.find(".csv")]
    data = pd.read_csv(filename)

    fig = go.Figure(go.Scattermapbox(
            lat=data["y"],
            lon=data["x"],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=8,
                color = data["Speed"],
                colorscale = plotly.colors.diverging.RdYlGn,
                colorbar_title="Speed (Km/Hr)"

            ),
            text = data["Notes"]
        ))

    fig.update_layout(
        title = title,
        title_x = 0.5,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=data["y"][1],
                lon=data["x"][1]
            ),
            pitch=0,
            zoom=12
        )
    )

    #x = py.plot(fig,auto_open=True)
    if toHTML:
        pio.write_html(fig, file='templates/map.html', auto_open=False)
    else:
        py.plot(fig,auto_open=True)
    return
#map("50 Downtown.csv")
#map("output/snapshot.csv")
