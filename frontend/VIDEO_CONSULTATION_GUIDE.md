# Video Consultation Setup Guide

## ✅ What's Been Fixed

1. **Socket.IO Connection** - Fixed CORS issues, now accepts connections from all origins
2. **Server Configuration** - Added `async_mode='threading'` for proper WebSocket support
3. **Doctor Dashboard** - Added video consultation capabilities
4. **Connection Flow** - Both doctors and patients can now initiate calls

## 🎯 How to Use Video Consultation

### For Doctors:

**Option 1: Start a New Call**
1. Go to Doctor Dashboard
2. Click the "Video Consultation" card (red with camera icon)
3. A unique Room ID will be generated
4. Share the Room ID with your patient
5. Wait for patient to join

**Option 2: Call a Specific Patient**
1. Go to Doctor Dashboard
2. Find the patient in the Patient Registry table
3. Click the red video camera button next to their name
4. A dialog will show the Room ID and shareable link
5. Share with patient via SMS/phone/notification
6. Click OK to start the call

### For Patients:

**Option 1: Join Doctor's Room**
1. Go to Patient Dashboard
2. Click "Video Consult" icon
3. Enter the Room ID provided by your doctor
4. You'll connect to the waiting room

**Option 2: Create Your Own Room**
1. Go to Patient Dashboard
2. Click "Video Consult" icon
3. Type 'new' when prompted
4. Share the generated Room ID with your doctor
5. Wait for doctor to join

## 🔗 Direct Access URLs

You can also use these direct URLs for testing:

**Patient URL:**
```
http://127.0.0.1:5000/patient/video-call.html?room=test123&type=patient&name=Patient1
```

**Doctor URL:**
```
http://127.0.0.1:5000/patient/video-call.html?room=test123&type=doctor&name=Dr.Sharma
```

> **Note:** Both must use the **same room ID** (e.g., "test123") to connect

## 🧪 Testing the Connection

1. Open the patient URL in one browser/tab
2. Open the doctor URL in another browser/tab (or different browser)
3. Allow camera/microphone permissions on both
4. The waiting overlay should disappear when both connect
5. You should see each other's video streams

## 🔧 Troubleshooting

**If the connection doesn't establish:**

1. Check browser console for errors (F12)
2. Verify both are using the exact same Room ID
3. Make sure camera/microphone permissions are granted
4. Try refreshing both pages
5. Check the server terminal for Socket.IO logs

**Server Logs Should Show:**
```
Client connected: [ID]
Upgrade to websocket successful
User (doctor/patient) joined room [room_id]
```

## 📱 Current Features

- ✅ WebRTC peer-to-peer video
- ✅ Audio muting
- ✅ Video on/off
- ✅ End call button
- ✅ Connection status indicator
- ✅ Room-based matching
- ✅ Doctor and patient role identification

## 🚀 Server Status

The server is currently running at:
- **Local:** http://127.0.0.1:5000
- **Network:** http://192.168.154.99:5000

Socket.IO is properly configured and accepting connections.
