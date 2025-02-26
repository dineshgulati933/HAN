from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/cv")
def cv():
    return render_template("cv.html")

# @app.route("/apps")
# def apps():
#     return render_template("apps.html")

@app.route("/gis")
def gis_projects():
    return render_template("gis_projects.html")

@app.route("/gis/project1")
def gis_project1():
    return render_template("gis/project1.html")

@app.route("/gis/project2")
def gis_project2():
    return render_template("gis/project2.html")

@app.route("/conf")
def conf():
    return render_template("conf.html")

@app.route("/conf/wqw")
def wqw():
    return render_template("conf/wqw.html")

if __name__ == "__main__":
    app.run(debug=True)
