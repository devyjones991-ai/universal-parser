#!/usr/bin/env python3
"""
Initialize Alembic migrations for Universal Parser
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command: str, description: str):
    """Run command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Initialize Alembic migrations"""
    print("🚀 Initializing Alembic migrations for Universal Parser...")
    
    # Check if alembic directory exists
    if not os.path.exists("alembic"):
        print("❌ Alembic directory not found. Please run this from the project root.")
        sys.exit(1)
    
    # Initialize Alembic (if not already done)
    if not os.path.exists("alembic/versions"):
        if not run_command("alembic init alembic", "Initializing Alembic"):
            sys.exit(1)
    
    # Create initial migration
    if not run_command("alembic revision --autogenerate -m 'Initial migration'", "Creating initial migration"):
        print("⚠️  Migration creation failed, but continuing...")
    
    # Show current revision
    run_command("alembic current", "Checking current revision")
    
    print("\n🎉 Alembic initialization completed!")
    print("\nNext steps:")
    print("1. Review the generated migration in alembic/versions/")
    print("2. Run 'alembic upgrade head' to apply migrations")
    print("3. Use 'alembic revision --autogenerate -m \"Description\"' for new migrations")

if __name__ == "__main__":
    main()

