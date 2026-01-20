# Static Assets

This directory contains all static files (CSS, images, PDFs) for the HydroAgriNexus website.

## Directory Structure

```
static/
├── css/
│   └── styles.css          # Main stylesheet with enhanced styles
├── images/
│   ├── c_and_p.webp        # Conference & Presentations thumbnail
│   ├── gis_projects.webp   # GIS Projects thumbnail
│   ├── iot_projects.webp   # IoT Projects thumbnail
│   ├── python_projects.webp # Python Projects thumbnail
│   ├── Profile_pic.jpg     # Profile picture
│   ├── WQW_poster.png      # Idaho Water Quality Workshop poster
│   └── pnw_ws24.png        # Pacific Northwest Water Summit poster
├── assets/
│   └── cv_dinesh.pdf       # Downloadable CV PDF
└── CNAME                   # Custom domain configuration
```

## Build Process

During the build process (`python build.py`), this entire directory is copied to `build/static/` for deployment to GitHub Pages.

## CSS Enhancements

The `styles.css` file includes:
- Professional card hover effects
- Smooth transitions and animations
- Responsive design for mobile devices
- Enhanced typography
- Accessibility features (focus states)
- Print-friendly styles
- Support for dark mode (if implemented)

## Adding New Assets

To add new images or files:
1. Place them in the appropriate subdirectory (`images/`, `assets/`, etc.)
2. Run `python build.py` to copy them to the build directory
3. Reference them in templates using `/static/path/to/file`

## Notes

- Images use WebP format for optimal web performance
- Posters are in PNG format for quality
- CV is in PDF format for universal compatibility
