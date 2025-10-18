#!/usr/bin/env python3
"""
Launch script for Universal Parser Dashboard
"""
import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "streamlit",
        "plotly", 
        "pandas",
        "requests",
        "httpx"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    return True

def check_api_connection():
    """Check if API is running"""
    import requests
    
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API connection successful")
            return True
        else:
            print(f"⚠️  API returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API connection failed: {e}")
        print("Make sure the API is running on http://localhost:8000")
        return False

def launch_dashboard():
    """Launch the Streamlit dashboard"""
    dashboard_dir = Path(__file__).parent / "dashboard"
    main_file = dashboard_dir / "main.py"
    
    if not main_file.exists():
        print(f"❌ Dashboard file not found: {main_file}")
        return False
    
    # Set environment variables
    env = os.environ.copy()
    env["STREAMLIT_SERVER_PORT"] = "8501"
    env["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    
    # Launch Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(main_file),
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("🚀 Launching Universal Parser Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the dashboard")
    
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🚀 Universal Parser Dashboard Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check API connection (optional)
    api_available = check_api_connection()
    if not api_available:
        print("⚠️  API is not available. Dashboard will work in limited mode.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Launch dashboard
    if not launch_dashboard():
        sys.exit(1)

if __name__ == "__main__":
    main()
