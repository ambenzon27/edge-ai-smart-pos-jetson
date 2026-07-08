#!/usr/bin/env python3
"""
AMB Store POS System Launcher
Automated startup script with checks and diagnostics
"""

import subprocess
import socket
import sys
import os
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================
PORT = 8000  # ← Change this to use a different port (8080, 5000, etc.)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_ip_address():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def check_directory():
    """Check if we're in the correct directory"""
    current_dir = Path.cwd()
    required_files = ['app', 'web', 'best.pt']

    missing = []
    for item in required_files:
        if not (current_dir / item).exists():
            missing.append(item)

    if missing:
        print("❌ ERROR: Not in the correct directory!")
        print(f"   Missing: {', '.join(missing)}")
        print()
        print("📁 Please run this from the me7 directory:")
        print("   cd ~/me7")
        print(f"   python3 {Path(__file__).name}")
        return False

    return True

def check_camera():
    """Check if camera is available"""
    camera_devices = list(Path('/dev').glob('video*'))
    if not camera_devices:
        print("⚠️  WARNING: No camera detected!")
        print("   Camera devices not found in /dev/video*")
        print("   The system will start but may not detect objects.")
        print()
        response = input("   Continue anyway? (y/n): ").lower()
        if response != 'y':
            return False
    else:
        print(f"✅ Camera detected: {camera_devices[0]}")

    return True

def check_model():
    """Check if model file exists"""
    model_path = Path('best.pt')
    if not model_path.exists():
        # Also check in model directory
        model_path = Path('model/best.pt')
        if not model_path.exists():
            print("⚠️  WARNING: Model file 'best.pt' not found!")
            print("   Detection may not work without the YOLO model.")
            print()
            response = input("   Continue anyway? (y/n): ").lower()
            if response != 'y':
                return False
    else:
        print("✅ Model file found")

    return True

def check_port_available(port):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()

    if result == 0:
        print(f"⚠️  WARNING: Port {port} is already in use!")
        print()
        new_port = input(f"   Enter a different port (or press Enter for {port}): ").strip()
        if new_port:
            try:
                return int(new_port)
            except ValueError:
                print("   Invalid port number. Using default.")
                return port

    return port

def print_banner():
    """Print startup banner"""
    print()
    print("=" * 70)
    print("🛍️  AMB STORE - SMART POS SYSTEM")
    print("=" * 70)
    print()

def print_access_info(ip, port):
    """Print access information"""
    print()
    print("🚀 SERVER STARTED SUCCESSFULLY!")
    print()
    print("📱 Access the AMB Store POS System at:")
    print(f"   • On this device:  http://localhost:{port}")
    print(f"   • From network:    http://{ip}:{port}")
    print()
    print("🎨 AMB Store Features:")
    print("   ✓ SM Store branding (Blue/Orange theme)")
    print("   ✓ Real-time object detection with YOLO")
    print("   ✓ Automatic shopping cart updates")
    print("   ✓ Beautiful animations & transitions")
    print("   ✓ Checkout modal with receipt")
    print()
    print("💡 Tips:")
    print("   • Make sure your USB camera is connected")
    print("   • Place items in front of camera to scan")
    print("   • Click items in cart to remove them")
    print()
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    print_banner()

    print("🔍 Running pre-flight checks...")
    print()

    # Check 1: Directory
    if not check_directory():
        sys.exit(1)

    print("✅ Directory check passed")

    # Check 2: Camera
    if not check_camera():
        print("\n❌ Startup cancelled.")
        sys.exit(1)

    # Check 3: Model
    if not check_model():
        print("\n❌ Startup cancelled.")
        sys.exit(1)

    # Check 4: Port availability
    port = check_port_available(PORT)

    print()
    print("✅ All checks passed!")

    # Get IP address
    ip = get_ip_address()

    # Print access information
    print_access_info(ip, port)

    try:
        # Start the server
        print("Starting uvicorn server...\n")

        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--log-level", "info"
        ], check=True)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("🛑 Server stopped by user")
        print("=" * 70)
        print("\n👋 Thank you for using AMB Store POS System!")
        print()

    except subprocess.CalledProcessError as e:
        print("\n\n" + "=" * 70)
        print("❌ SERVER ERROR")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if uvicorn is installed:")
        print("   pip3 install uvicorn")
        print()
        print("2. Check if all requirements are installed:")
        print("   pip3 install -r requirements.txt")
        print()
        print("3. Check Python version (needs 3.8+):")
        print("   python3 --version")
        print()
        sys.exit(1)

    except FileNotFoundError:
        print("\n\n" + "=" * 70)
        print("❌ PYTHON OR UVICORN NOT FOUND")
        print("=" * 70)
        print("\n🔧 Please install requirements:")
        print("   pip3 install -r requirements.txt")
        print()
        sys.exit(1)

    except Exception as e:
        print("\n\n" + "=" * 70)
        print("❌ UNEXPECTED ERROR")
        print("=" * 70)
        print(f"\nError: {e}")
        print()
        print("🔧 Please check:")
        print("1. You're in the correct directory (cd ~/me7)")
        print("2. All files are present (app/, web/, best.pt)")
        print("3. Requirements are installed (pip3 install -r requirements.txt)")
        print()
        sys.exit(1)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
