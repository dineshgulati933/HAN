import sys
import os
from app import app
import shutil

# Copy CNAME file to the build directory
shutil.copyfile("build/static/CNAME", "build/CNAME")
print("CNAME file added to build directory")


# Output directory for static files
output_dir = "build"

# Ensure the output directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Define the pages to render
pages = {
    "index.html": "/",
    "cv.html": "/cv",
    "apps.html": "/apps",
    "about.html": "/about",
    "gis_projects.html": "/gis",
    "gis/project1.html": "/gis/project1",
    "gis/project2.html": "/gis/project2",
    "conf.html": "/conf",
    "conf/wqw.html": "/conf/wqw",
}

# Render pages
with app.test_request_context():
    for filename, route in pages.items():
        response = app.test_client().get(route)
        output_path = os.path.join(output_dir, filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(response.data.decode("utf-8"))
        print(f"Rendered: {filename}")

print(f"Static site generated in {output_dir}/")
