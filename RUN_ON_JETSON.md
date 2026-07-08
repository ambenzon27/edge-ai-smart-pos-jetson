# 🚀 How to Run AMB Store POS System on Jetson Orin

## Quick Start Guide

### Step 1: Transfer Files to Jetson Orin

```bash
# On your Mac, compress the me7 folder
cd "/Users/annamariebenzon/Documents/PhD in AI/SECOND YEAR/First Sem/AI231/MLOps Assignment/me7"
zip -r me7_amb_store.zip me7/

# Transfer to Jetson (replace with your Jetson's IP)
scp me7_amb_store.zip jetson@YOUR_JETSON_IP:~/

# Or use a USB drive to transfer the folder
```

---

### Step 2: Setup on Jetson Orin

SSH into your Jetson Orin:

```bash
ssh jetson@YOUR_JETSON_IP
```

Extract and navigate to the folder:

```bash
cd ~
unzip me7_amb_store.zip
cd me7
```

---

### Step 3: Install Dependencies

```bash
# Install required packages
pip3 install -r requirements.txt

# Or install individually:
pip3 install fastapi uvicorn opencv-python ultralytics mediapipe pyttsx3
```

---

### Step 4: Run the Server

**Option 1: Using the start script (Recommended)**

```bash
cd ~/me7
chmod +x scripts/start_server.sh
./scripts/start_server.sh
```

**Option 2: Direct command**

```bash
cd ~/me7
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

### Step 5: Access the AMB Store POS System

Open a web browser on any device on the same network:

```
http://YOUR_JETSON_IP:8000
```

Or on the Jetson itself:

```
http://localhost:8000
```

You should see the beautiful **AMB Store** interface with SM Store branding! 🎨

---

## 🎯 What You'll See

1. **Left Panel**: Order receipt with AMB Store header
2. **Right Panel**: Live camera feed with detection
3. **Blue/Orange Theme**: SM Store colors throughout
4. **Animations**: Scan line, floating logo, smooth effects
5. **Real-time Updates**: Items automatically added to cart

---

## 🔧 Troubleshooting

### Camera Not Working

```bash
# Check if camera is connected
ls /dev/video*

# You should see /dev/video0 or similar
# If not, reconnect your USB camera
```

### Port Already in Use

```bash
# Use a different port
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# Then access at: http://YOUR_JETSON_IP:8080
```

### Model Not Found

```bash
# Make sure best.pt exists
ls ~/me7/best.pt

# If missing, copy your trained model:
cp /path/to/your/best.pt ~/me7/
```

### Import Errors

```bash
# Reinstall dependencies
pip3 install --upgrade -r requirements.txt

# Or install system packages
sudo apt-get install python3-opencv
```

---

## ⚙️ Configuration

### Change Camera Device

Edit `app/config.py`:

```python
CAMERA_INDEX = 0  # Change to 1, 2, etc. if needed
```

### Adjust Detection Confidence

Edit `app/config.py`:

```python
PER_CLASS_CONFIDENCE_THRESHOLDS = {
    "Coke": 0.5,  # Adjust threshold (0.0 to 1.0)
    # Add more products...
}
```

### Change Server Port

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port YOUR_PORT
```

---

## 📱 Full Screen Kiosk Mode (Optional)

For a professional in-store setup:

```bash
# Run the kiosk script
chmod +x scripts/start_kiosk.sh
./scripts/start_kiosk.sh
```

This will:
- Start the server
- Open browser in fullscreen
- Hide cursor after inactivity
- Perfect for retail display!

---

## 🛑 Stopping the Server

Press `Ctrl + C` in the terminal where the server is running.

---

## 🔄 Auto-Start on Boot (Optional)

To make it start automatically when Jetson boots:

```bash
# Create systemd service
sudo nano /etc/systemd/system/amb-store.service
```

Add this content:

```ini
[Unit]
Description=AMB Store POS System
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/me7
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable amb-store.service
sudo systemctl start amb-store.service

# Check status
sudo systemctl status amb-store.service
```

---

## 📊 API Endpoints

The system provides these endpoints:

- `GET /` - Main web interface (AMB Store UI)
- `GET /video-stream` - Live camera feed
- `GET /detections` - Get detected items (JSON)
- `GET /recording-state` - Get recording status
- `GET /prices` - Get product prices
- `GET /health` - Server health check

---

## 🎨 Customization

### Change Store Name

Edit `web/index.html` (line 25):

```html
<h1 class="store-name">YOUR STORE NAME</h1>
```

### Change Colors

Edit `web/static/styles.css` (lines 7-13):

```css
:root {
  --sm-blue: #0066CC;      /* Change primary color */
  --sm-orange: #FFA500;    /* Change accent color */
  /* ... */
}
```

### Add Products

Edit `app/config.py`:

```python
ITEM_PRICES = {
    "Coke": 30.00,
    "Your Product": 99.99,
    # Add more...
}
```

---

## 📞 Common Commands Summary

```bash
# Start server
cd ~/me7 && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Stop server
Ctrl + C

# Check camera
ls /dev/video*

# View logs
tail -f logs/detections.log

# Restart Jetson
sudo reboot
```

---

## ✅ Checklist Before Running

- [ ] USB camera connected
- [ ] Files transferred to Jetson
- [ ] Dependencies installed (`pip3 install -r requirements.txt`)
- [ ] Model file exists (`best.pt`)
- [ ] Camera permissions OK
- [ ] Network connection active

---

## 🎉 You're Ready!

Your AMB Store POS system with beautiful SM Store branding is now running!

**Access it at:** `http://YOUR_JETSON_IP:8000`

Enjoy your smart retail system! 🛍️✨

---

## 💡 Tips

1. **For best performance**: Connect camera before starting
2. **Network access**: Make sure firewall allows port 8000
3. **Display**: Connect Jetson to a monitor for best experience
4. **Testing**: Test with a few products first before full deployment
5. **Backup**: Keep a copy of your `best.pt` model file

---

## Need Help?

Check these files in the `me7` folder:
- `JETSON_SETUP.md` - Detailed Jetson setup
- `AMB_STORE_DESIGN_README.md` - Design documentation
- `app/config.py` - Configuration options
