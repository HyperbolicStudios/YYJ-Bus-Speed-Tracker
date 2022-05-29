import plotly.graph_objects as go
import plotly.express as px
import chart_studio
import chart_studio.plotly
username = 'markedwardson' # your plotly username
api_key = 'WmN6zyhKAWqMVSKhLyUQ' # your plotly api key - go to profile > settings > regenerate key
chart_studio.tools.set_credentials_file(username=username, api_key=api_key)
def graph_variables(x,y,chart_title="plotted data"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
            y=y,x=x))
    fig.update(layout_yaxis_range = [0,120])
    annotations = [(dict(xref='paper', yref='paper', x=0.5, y=1.05,
                              xanchor='center', yanchor='bottom',
                              text=chart_title,
                              font=dict(family='Arial',
                                        size=30,
                                        color='rgb(37,37,37)'),
                              showarrow=False))]
    fig.update_layout(bargap=0.2,annotations=annotations)
    #return(chart_studio.plotly.plot(fig, filename = "Bus speed",auto_open=False))
    fig.show()
    return

def map():
    import pandas as pd
    results = pd.read_csv("50 Langford.csv")

    import plotly.express as px

    fig = px.scatter_mapbox(results, lat="y", lon="x", hover_name="Time", hover_data=["Speed"],
                            color_discrete_sequence=["fuchsia"], zoom=3, height=300)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()
    return
map()
