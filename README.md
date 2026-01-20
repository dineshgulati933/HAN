# HydroAgriNexus - Static Site Generator

A Flask-based static site generator for the HydroAgriNexus website, deployed on GitHub Pages.

## Project Structure

```
HAN/
├── app.py                 # Flask application with all routes
├── config.py              # Site configuration and page definitions
├── build.py               # Main build script (improved)
├── render_static.py       # Legacy build script (deprecated)
├── requirements.txt       # Python dependencies
├── CNAME                  # Custom domain configuration
├── templates/             # Jinja2 templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Homepage
│   ├── cv.html           # CV page
│   ├── about.html        # About page
│   ├── python_projects.html
│   ├── iot_projects.html
│   ├── gis_projects.html
│   ├── conf.html         # Conferences listing
│   ├── conf/             # Conference-specific pages
│   │   ├── pnw_ws24.html
│   │   └── wqw.html
│   └── gis/              # GIS project pages
│       ├── project1.html
│       └── project2.html
├── static/               # Static assets (CSS, JS, images)
│   ├── css/
│   ├── js/
│   ├── images/
│   └── assets/
└── build/                # Generated static site (deploy this)
    ├── index.html
    ├── *.html
    ├── conf/
    ├── gis/
    └── static/
```

## Workflow

### Development

1. **Edit templates** in the `templates/` directory
2. **Update configuration** in `config.py` to add new pages
3. **Add routes** in `app.py` for new pages
4. **Test locally** with Flask development server:
   ```bash
   python app.py
   ```
   Visit http://localhost:5000

### Building for Production

1. **Generate static files**:
   ```bash
   python build.py
   ```
   
2. **Review the build** in the `build/` directory

3. **Deploy to GitHub Pages**:
   ```bash
   git add build/
   git commit -m "Update site"
   git push
   ```

## Build Script Features

The new `build.py` script provides:
- ✅ Clean build process
- ✅ Error handling and reporting
- ✅ Progress tracking
- ✅ Automatic static file copying
- ✅ CNAME file handling
- ✅ Build summary with statistics

## Adding a New Page

1. **Create template** in `templates/`:
   ```html
   {% extends "base.html" %}
   {% block title %}My Page{% endblock %}
   {% block content %}
   <!-- Your content -->
   {% endblock %}
   ```

2. **Add route** in `app.py`:
   ```python
   @app.route("/my-page")
   def my_page():
       return render_template("my_page.html")
   ```

3. **Register page** in `config.py`:
   ```python
   PAGES = {
       # ... existing pages
       "my_page.html": {
           "route": "/my-page",
           "title": "My Page"
       }
   }
   ```

4. **Build and deploy**:
   ```bash
   python build.py
   ```

## External Applications

Python applications hosted on external platforms (PythonAnywhere, Heroku) are configured in `config.py` under `EXTERNAL_APPS`. These are:

- **SWB-SOC**: Soil Water Balance - Soil Organic Carbon model
- **SWB-SOC-CPS**: With Crop Production System
- **FieldSync**: Field data management tool
- **FAO56 SWB**: FAO-56 Soil Water Balance simulation

## Configuration

All site configuration is centralized in `config.py`:

- **PAGES**: All pages to be rendered
- **EXTERNAL_APPS**: Links to external applications
- **BUILD_DIR**: Output directory for static files
- Site metadata (name, tagline, year)

## Deployment

### GitHub Pages Setup

1. **Repository settings** → Pages
2. **Source**: Deploy from branch
3. **Branch**: `main` or `master`
4. **Folder**: `/build` or `/` (root)

### Custom Domain

The `CNAME` file contains your custom domain configuration and is automatically copied during build.

## Dependencies

```
Flask==3.0.3
```

Install with:
```bash
pip install -r requirements.txt
```

## Tips

- **Always test locally** before building for production
- **Keep templates DRY** using template inheritance
- **Use config.py** for all site-wide settings
- **Version control** the `templates/` and `static/` directories
- **Deploy the `build/` directory** to GitHub Pages

## Troubleshooting

**Build fails**: Check `app.py` routes match `config.py` PAGES

**Missing static files**: Ensure files are in `static/` directory before building

**404 on GitHub Pages**: Check that `build/` directory is committed and pushed

**Broken links**: Use root-relative paths starting with `/`

## Legacy Files

- `render_static.py` - Old build script (replaced by `build.py`)
- `about_basic.html` - Unused template (can be removed)

---

**Last Updated**: December 2025
