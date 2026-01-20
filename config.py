# Site Configuration
SITE_NAME = "HydroAgriNexus"
SITE_TAGLINE = "More Crops with Each Drop"
SITE_YEAR = "2025"

# Build Configuration
BUILD_DIR = "build"
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"

# Page Routes - Define all pages to be rendered
# Format: "output_filename": {"route": "/route", "title": "Page Title"}
PAGES = {
    "index.html": {
        "route": "/",
        "title": "Home"
    },
    "cv.html": {
        "route": "/cv",
        "title": "CV"
    },
    "about.html": {
        "route": "/about",
        "title": "About"
    },
    "gis_projects.html": {
        "route": "/gis",
        "title": "GIS Projects"
    },
    "gis/project1.html": {
        "route": "/gis/project1",
        "title": "GIS Project 1"
    },
    "gis/project2.html": {
        "route": "/gis/project2",
        "title": "GIS Project 2"
    },
    "python_projects.html": {
        "route": "/python",
        "title": "Python Projects"
    },
    "iot_projects.html": {
        "route": "/iot",
        "title": "IoT & Arduino Projects"
    },
    "conf.html": {
        "route": "/conf",
        "title": "Conferences & Presentations"
    },
    "conf/wqw.html": {
        "route": "/conf/wqw",
        "title": "Water Quality Workshop"
    },
    "conf/pnw_ws24.html": {
        "route": "/conf/pnw_ws24",
        "title": "Pacific Northwest Water Summit 2024"
    },
}

# External Apps (hosted on PythonAnywhere/Heroku)
EXTERNAL_APPS = [
    {
        "name": "SWB-SOC",
        "url": "https://dinesh933.pythonanywhere.com/approach1_params",
        "description": "Soil Water Balance - Soil Organic Carbon"
    },
    {
        "name": "SWB-SOC-CPS",
        "url": "https://dinesh933.pythonanywhere.com/approach2_params",
        "description": "Soil Water Balance - SOC - Crop Production System"
    },
    {
        "name": "FieldSync",
        "url": "https://fieldsync.pythonanywhere.com/",
        "description": "Field Data Synchronization Tool"
    },
    {
        "name": "FAO56 SWB",
        "url": "https://swb.hydroagrinexus.com/",
        "description": "FAO-56 Soil Water Balance Model"
    }
]
