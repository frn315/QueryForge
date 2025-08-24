#!/usr/bin/env python3
"""
QueryForge Application Launcher
Provides unified entry point for API and UI components.
"""

import sys
import asyncio
import subprocess
import multiprocessing as mp
from pathlib import Path

def run_api():
    """Start the FastAPI server."""
    try:
        print("🚀 Starting QueryForge API...")
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "5000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  API server stopped")
    except Exception as e:
        print(f"❌ API server error: {e}")

def run_ui():
    """Start the Streamlit UI."""
    try:
        print("🎨 Starting QueryForge UI...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "ui_streamlit.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  UI server stopped")
    except Exception as e:
        print(f"❌ UI server error: {e}")

def run_both():
    """Start both API and UI servers in parallel."""
    print("🚀 Starting QueryForge (API + UI)...")

    # Start API server
    api_process = mp.Process(target=run_api)
    api_process.start()

    # Start UI server
    ui_process = mp.Process(target=run_ui)
    ui_process.start()

    try:
        # Wait for both processes
        api_process.join()
        ui_process.join()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down servers...")
        api_process.terminate()
        ui_process.terminate()
        api_process.join()
        ui_process.join()

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run.py [api|ui|both]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "api":
        run_api()
    elif mode == "ui":
        run_ui()
    elif mode == "both":
        run_both()
    else:
        print("❌ Invalid mode. Use: api, ui, or both")
        sys.exit(1)

if __name__ == "__main__":
    main()