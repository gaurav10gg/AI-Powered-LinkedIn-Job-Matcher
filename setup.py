#!/usr/bin/env python3
"""
Setup script for LinkedIn Job Scraper
Run this to organize files and check dependencies
"""

import os
import sys
import shutil
import subprocess

def run_command(cmd, description):
    """Run a shell command and print status"""
    print(f"⏳ {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        print(f"✅ {description} - Done")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"   Error: {e.stderr.decode()}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 LinkedIn Job Scraper - Setup Script")
    print("="*60 + "\n")
    
    # Check if we're in the right directory
    required_files = ['linkedin_scraper.py', 'main.py', 'local_agent.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("❌ Error: Missing required files in current directory:")
        for f in missing_files:
            print(f"   - {f}")
        print("\nPlease run this script from the SCRAPING directory")
        sys.exit(1)
    
    print("✅ Found all required Python files\n")
    
    # Create directories
    print("📁 Creating directories...")
    os.makedirs('frontend', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    print("✅ Directories created\n")
    
    # Move frontend files
    print("📋 Organizing frontend files...")
    frontend_files = ['index.html', 'script.js', 'style.css']
    moved = 0
    
    for file in frontend_files:
        if os.path.exists(file) and not os.path.exists(f'frontend/{file}'):
            shutil.move(file, f'frontend/{file}')
            print(f"  ✅ Moved {file} to frontend/")
            moved += 1
        elif os.path.exists(f'frontend/{file}'):
            print(f"  ✓ {file} already in frontend/")
        else:
            print(f"  ⚠️  {file} not found")
    
    if moved > 0:
        print(f"✅ Moved {moved} files to frontend/\n")
    else:
        print("✅ Frontend files already organized\n")
    
    # Check if all frontend files exist
    missing_frontend = [f for f in frontend_files if not os.path.exists(f'frontend/{f}')]
    if missing_frontend:
        print("⚠️  Warning: Missing frontend files:")
        for f in missing_frontend:
            print(f"   - frontend/{f}")
        print("   The web interface may not work properly\n")
    
    # Check Python version
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]}\n")
    
    # Install dependencies
    print("📦 Installing Python dependencies...")
    packages = [
        'fastapi',
        'uvicorn[standard]',
        'python-multipart',
        'pdfplumber',
        'spacy',
        'scikit-learn',
        'playwright',
        'requests'
    ]
    
    for package in packages:
        run_command(f'pip install -q {package}', f'Installing {package}')
    
    print()
    
    # Download spaCy model
    print("🧠 Downloading spaCy language model...")
    run_command('python -m spacy download en_core_web_sm', 'Downloading spaCy model')
    print()
    
    # Install Playwright browsers
    print("🌐 Installing Playwright browsers...")
    run_command('playwright install chromium', 'Installing Chromium browser')
    print()
    
    # Summary
    print("="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\n📂 Project structure:")
    print("SCRAPING/")
    print("├── frontend/")
    for f in frontend_files:
        exists = "✓" if os.path.exists(f'frontend/{f}') else "✗"
        print(f"│   ├── {f} {exists}")
    print("├── uploads/")
    print("├── main.py ✓")
    print("├── linkedin_scraper.py ✓")
    print("├── local_agent.py ✓")
    print("└── ... (other files)")
    
    print("\n🚀 Next steps:")
    print("1. Start the server:")
    print("   uvicorn main:app --reload")
    print("\n2. Open your browser:")
    print("   http://127.0.0.1:8000")
    print("\n3. Upload your resume and get a Job ID")
    print("\n4. In a new terminal, run:")
    print("   python local_agent.py")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)