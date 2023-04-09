from flask import Flask, render_template
from flask_apscheduler import APScheduler

from tracking import snapshot
from mapping import map

data = snapshot()
if data.empty == False:
    map(data,title="YYJ Bus Speeds")

# create app
app = Flask(__name__)
print("FLASK APP STARTING UP. SNAPSHOT TAKEN.")
# initialize scheduler
scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()
app.config["TEMPLATES_AUTO_RELOAD"] = True

# interval example
@scheduler.task('interval', id='do_job_1', seconds=10, misfire_grace_time=900)
def job1():
    data = snapshot()
    if data.empty == False:
        map(data,title="YYJ Bus Speeds")
    print('Job 1 executed')
    

@app.route("/plotly")
def plotly():
    return render_template("map.html")

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == '__main__':
    app.run()
