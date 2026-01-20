"""
HydroAgriNexus Static Site Builder
Generates static HTML files from Flask templates for GitHub Pages deployment
"""
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from app import app
from config import PAGES, BUILD_DIR, STATIC_DIR

def ensure_directory(path):
    """Create directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)

def copy_static_files():
    """Copy static assets to build directory"""
    build_static = os.path.join(BUILD_DIR, STATIC_DIR)
    
    if os.path.exists(build_static):
        shutil.rmtree(build_static)
    
    shutil.copytree(STATIC_DIR, build_static)
    print(f"✓ Copied static files to {build_static}")

def copy_cname():
    """Copy CNAME file for custom domain"""
    cname_source = "CNAME"
    cname_dest = os.path.join(BUILD_DIR, "CNAME")
    
    if os.path.exists(cname_source):
        shutil.copy(cname_source, cname_dest)
        print(f"✓ Copied CNAME to {cname_dest}")
    else:
        print("⚠ Warning: CNAME file not found")

def render_pages():
    """Render all pages defined in config.PAGES"""
    ensure_directory(BUILD_DIR)
    
    rendered_count = 0
    failed_pages = []
    
    with app.test_request_context():
        for filename, page_info in PAGES.items():
            route = page_info["route"]
            
            try:
                # Get rendered HTML from Flask
                response = app.test_client().get(route)
                
                if response.status_code != 200:
                    failed_pages.append((filename, f"HTTP {response.status_code}"))
                    continue
                
                # Write to output file
                output_path = os.path.join(BUILD_DIR, filename)
                ensure_directory(os.path.dirname(output_path))
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(response.data.decode("utf-8"))
                
                print(f"✓ Rendered: {filename}")
                rendered_count += 1
                
            except Exception as e:
                failed_pages.append((filename, str(e)))
    
    return rendered_count, failed_pages

def clean_build_directory():
    """Remove old build directory"""
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
        print(f"✓ Cleaned build directory")

def main():
    """Main build process"""
    print("=" * 60)
    print("HydroAgriNexus - Static Site Builder")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Step 1: Clean old build
        clean_build_directory()
        
        # Step 2: Render pages
        print("\nRendering pages...")
        rendered_count, failed_pages = render_pages()
        
        # Step 3: Copy static files
        print("\nCopying static assets...")
        copy_static_files()
        
        # Step 4: Copy CNAME
        copy_cname()
        
        # Summary
        print("\n" + "=" * 60)
        print("Build Summary")
        print("=" * 60)
        print(f"✓ Successfully rendered: {rendered_count} pages")
        
        if failed_pages:
            print(f"✗ Failed: {len(failed_pages)} pages")
            for filename, error in failed_pages:
                print(f"  - {filename}: {error}")
            sys.exit(1)
        else:
            print(f"✓ All pages rendered successfully!")
        
        print(f"\n✓ Static site generated in '{BUILD_DIR}/' directory")
        print(f"✓ Ready for deployment to GitHub Pages")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Build failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
