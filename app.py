from flask import Flask, render_template
from flask_apscheduler import APScheduler
import time
from tracking import snapshot
from mapping import map
import boto3
import os

#snapshot()

s3 = boto3.resource(
    service_name='s3',
    region_name='us-east-2',
    aws_access_key_id=os.environ['aws_access_key_id'],
    aws_secret_access_key=os.environ['aws_secret_access_key']
)

# create app
app = Flask(__name__)

# initialize scheduler
scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()
app.config["TEMPLATES_AUTO_RELOAD"] = True

# interval example
@scheduler.task('interval', id='do_job_1', seconds=20, misfire_grace_time=900)
def job1():
    print("Starting job1")
    snapshot()
    map("output/snapshot.csv",toHTML="True",title="YYJ Bus Speeds")



@app.route("/plotly")
def plotly():
    s3.Bucket('busspeedbucket').download_file(Key='map.html', Filename='templates/map.html')
    return render_template("map.html")

@app.route("/")
def home():
    return render_template("index.html")



if __name__ == '__main__':
    app.run()
