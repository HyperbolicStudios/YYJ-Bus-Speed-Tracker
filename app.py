from flask import Flask, render_template
from flask_apscheduler import APScheduler
import time
from tracking import snapshot
from mapping import map


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
    snapshot()
    map("output/snapshot.csv",toHTML="True")
    print('Job 1 executed')
    time.sleep(10)

@app.route("/plotly")
def plotly():
    return render_template("map.html")

@app.route("/")
def home():
    return render_template("index.html")



if __name__ == '__main__':
    app.run()
