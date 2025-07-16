#!/usr/bin/env python3
"""
Local setup script for MuseFit
This script helps set up the environment and dependencies for running MuseFit locally.
"""

import os
import sys
import subprocess
import secrets

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    dependencies = [
        'flask',
        'pillow',
        'google-genai',
        'werkzeug',
        'gunicorn',
        'pydantic'
    ]
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + dependencies)
        print("✅ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    print("\n🔑 Creating .env file...")
    
    # Check if .env.example exists
    if os.path.exists('.env.example'):
        print("Found .env.example file, using it as template...")
        with open('.env.example', 'r') as f:
            template = f.read()
    else:
        template = """# MuseFit Environment Variables
GEMINI_API_KEY=your_gemini_api_key_here
SESSION_SECRET=your_random_session_secret_here
"""
    
    api_key = input("Enter your Gemini API key (get it from https://aistudio.google.com/app/apikey): ").strip()
    
    if not api_key:
        print("❌ API key is required")
        return False
    
    session_secret = secrets.token_hex(32)
    
    # Replace placeholders in template
    env_content = template.replace('your_gemini_api_key_here', api_key)
    env_content = env_content.replace('your_random_session_secret_here', session_secret)
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        'static',
        'static/uploads',
        'static/results',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Directories created")

def create_test_images():
    """Generate test images"""
    print("\n🖼️ Creating test images...")
    try:
        exec(open('create_test_image.py').read())
        print("✅ Test images created")
        return True
    except Exception as e:
        print(f"⚠️ Could not create test images: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 MuseFit Local Setup")
    print("=" * 30)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Create directories
    create_directories()
    
    # Create .env file
    if not create_env_file():
        return
    
    # Create test images
    create_test_images()
    
    print("\n🎉 Setup complete!")
    print("\nTo start the application:")
    print("1. python main.py          (simple development server)")
    print("2. gunicorn --bind 0.0.0.0:5000 --reload main:app  (production server)")
    print("\nThen open http://localhost:5000 in your browser")

if __name__ == "__main__":
    main()