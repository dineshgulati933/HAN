from flask import Flask, render_template
from config import EXTERNAL_APPS

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/cv")
def cv():
    return render_template("cv.html")

@app.route("/about")
def about():
    return render_template("about.html")

# GIS Projects
@app.route("/gis")
def gis_projects():
    return render_template("gis_projects.html")

@app.route("/gis/project1")
def gis_project1():
    return render_template("gis/project1.html")

@app.route("/gis/project2")
def gis_project2():
    return render_template("gis/project2.html")

# Python Projects
@app.route("/python")
def python_projects():
    return render_template("python_projects.html", apps=EXTERNAL_APPS)

# IoT Projects
@app.route("/iot")
def iot_projects():
    return render_template("iot_projects.html")

# Conferences
@app.route("/conf")
def conf():
    return render_template("conf.html")

@app.route("/conf/wqw")
def wqw():
    return render_template("conf/wqw.html")

@app.route("/conf/pnw_ws24")
def pnw_ws24():
    return render_template("conf/pnw_ws24.html")

if __name__ == "__main__":
    app.run(debug=True)
