# Flask Video Consultation Authentication Guide

## 🔐 Authentication Architecture

### System Overview
This healthcare platform uses **session-based authentication**, NOT tokens.

```
User Login → Flask Sets Session Cookie → Browser Stores Cookie → Browser Sends Cookie on Every Request
```

### Key Components

#### Backend (Flask)
- **Session cookies** stored server-side
- `session['user_id']` - User ID
- `session['role']` - User role (patient/doctor/lab)
- `session['full_name']` - Display name

#### Frontend
- **NO localStorage tokens**
- **NO Authorization headers**
- Session cookies automatically sent by browser

---

## ✅ Correct Authentication Patterns

### 1. API Route Authentication

#### ✅ DO THIS: Proper API endpoint
```python
@video_bp.route('/check-auth', methods=['GET'])
def check_video_auth():
    """Check authentication WITHOUT @login_required decorator
    so we can return JSON instead of HTML redirect"""
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'authenticated': False,
            'error': 'Not authenticated'
        }), 401
    
    return jsonify({
        'success': True,
        'authenticated': True,
        'user': {
            'id': session.get('user_id'),
            'role': session.get('role'),
            'name': session.get('full_name')
        }
    }), 200
```

#### ❌ DON'T DO THIS: Using @login_required on check endpoint
```python
@video_bp.route('/check-auth', methods=['GET'])
@login_required  # ❌ This will redirect to HTML login page
def check_video_auth():
    return jsonify({'authenticated': True}), 200
```

**Why?** The `@login_required` decorator redirects to login page when not authenticated, returning HTML instead of JSON. This causes "Unexpected token '<'" errors.

---

### 2. Frontend API Calls

#### ✅ DO THIS: Include credentials for session cookies
```javascript
async function checkAuth() {
    const response = await fetch('/video/check-auth', {
        method: 'GET',
        credentials: 'include'  // ✅ Send session cookies
    });
    
    if (!response.ok) {
        window.location.href = '/login.html';
        return false;
    }
    
    const data = await response.json();
    return data.authenticated;
}
```

#### ❌ DON'T DO THIS: Using tokens
```javascript
async function checkAuth() {
    const token = localStorage.getItem('token');  // ❌ No tokens in this system
    const response = await fetch('/video/check-auth', {
        headers: {
            'Authorization': `Bearer ${token}`  // ❌ Wrong auth method
        }
    });
}
```

**Why?** This system uses session cookies, not JWT tokens. The browser automatically sends cookies when `credentials: 'include'` is set.

---

### 3. Socket.IO Authentication

#### ✅ DO THIS: Verify session in connect handler
```python
@socketio.on('connect')
def handle_connect():
    # Session is automatically available from Flask
    if 'user_id' not in session:
        print('Unauthorized connection attempt')
        return False  # Disconnect client
    
    user_id = session.get('user_id')
    print(f'Authenticated user {user_id} connected')
    return True
```

#### ✅ DO THIS: Enable credentials in frontend
```javascript
socket = io('http://127.0.0.1:5000', {
    transports: ['websocket', 'polling'],
    withCredentials: true  // ✅ Send cookies with Socket.IO
});
```

#### ❌ DON'T DO THIS: No authentication
```python
@socketio.on('connect')
def handle_connect():
    print('Client connected')  # ❌ Anyone can connect
    emit('connected', {'message': 'Welcome'})
```

**Why?** Without authentication, anyone can connect to Socket.IO and join video rooms, access private notifications, etc.

---

### 4. Page Protection

#### ✅ DO THIS: Check auth before initialization
```javascript
async function init() {
    // STEP 1: Check authentication FIRST
    const isAuthenticated = await checkAuthentication();
    if (!isAuthenticated) {
        return; // Don't proceed
    }
    
    // STEP 2: Then access camera, Socket.IO, etc.
    await setupLocalMedia();
    setupSocketConnection();
}
```

#### ❌ DON'T DO THIS: Access resources before checking auth
```javascript
async function init() {
    // ❌ Accessing camera before checking auth
    await setupLocalMedia();
    
    // ❌ Connecting to Socket.IO before auth check
    setupSocketConnection();
    
    // Auth check should be FIRST, not last
    checkAuthentication();
}
```

**Why?** If user is not authenticated, they shouldn't access camera, connect to Socket.IO, or see any video UI.

---

## 🚨 Common Mistakes & Solutions

### Mistake 1: HTML Login Page Returned as JSON
**Symptom:** `Unexpected token '<', "<!doctype html>" is not valid JSON`

**Cause:** API endpoint with `@login_required` redirects to HTML login page

**Solution:** 
```python
# Option A: Don't use @login_required, check manually
@video_bp.route('/check-auth', methods=['GET'])
def check_video_auth():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({'authenticated': True}), 200

# Option B: Ensure decorator detects API request
# Already configured in auth/decorators.py:
is_api_request = (
    request.path.startswith('/api/') or 
    request.path.startswith('/video/') or  # ✅ Video routes return JSON
    request.is_json or 
    'application/json' in request.headers.get('Accept', '')
)
```

---

### Mistake 2: Socket.IO Connection Fails
**Symptom:** "Connection refused" or immediate disconnect

**Cause 1:** Missing `withCredentials: true` in frontend
```javascript
// ❌ Wrong
socket = io('http://127.0.0.1:5000');

// ✅ Correct
socket = io('http://127.0.0.1:5000', {
    withCredentials: true  // Send session cookies
});
```

**Cause 2:** Backend not checking session
```python
# ✅ Add this to connect handler
@socketio.on('connect')
def handle_connect():
    if 'user_id' not in session:
        return False  # Disconnect
```

---

### Mistake 3: Session Not Persisting
**Symptom:** User keeps getting logged out

**Cause:** Session not marked as permanent
```python
# ✅ In login route
@auth_bp.route('/login', methods=['POST'])
def login():
    # ... validate credentials ...
    
    session.permanent = True  # ✅ Make session persistent
    session['user_id'] = user.id
    session['role'] = user.role
```

**Also check:** Flask session configuration
```python
# In app.py or config.py
app.config['SECRET_KEY'] = 'your-secret-key'  # Required for sessions
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
```

---

### Mistake 4: CORS Issues with Cookies
**Symptom:** Cookies not sent, auth fails on video page

**Cause:** Missing CORS configuration for credentials

**Solution:**
```python
from flask_cors import CORS

# ✅ If using CORS (only needed if frontend on different domain)
CORS(app, supports_credentials=True, origins=['http://localhost:5000'])
```

```javascript
// ✅ Frontend must include credentials
fetch('/video/check-auth', {
    credentials: 'include'  // Required for cross-origin cookie sharing
});
```

---

## 🔧 Debugging Authentication Issues

### Step 1: Check Session in Backend
```python
@video_bp.route('/debug-session', methods=['GET'])
def debug_session():
    return jsonify({
        'session_data': dict(session),
        'has_user_id': 'user_id' in session,
        'cookies': dict(request.cookies)
    })
```

### Step 2: Check Cookies in Browser
1. Open DevTools (F12)
2. Go to Application → Cookies
3. Look for session cookie (usually `session`)
4. Verify it's being sent with requests (Network tab)

### Step 3: Check Request Headers
In Network tab:
```
Request Headers:
  Cookie: session=eyJ1c2VyX2lkIjoxfQ...  ✅ Session cookie present
  
Response Headers:
  Set-Cookie: session=...; HttpOnly; Path=/  ✅ Server sets cookie
```

### Step 4: Test Auth Flow
```javascript
// Test in browser console
async function testAuth() {
    // 1. Check session
    const authResponse = await fetch('/video/check-auth', {
        credentials: 'include'
    });
    console.log('Auth status:', authResponse.status);
    console.log('Auth data:', await authResponse.json());
    
    // 2. Test Socket.IO
    const socket = io('http://127.0.0.1:5000', {
        withCredentials: true
    });
    socket.on('connect', () => console.log('✅ Socket connected'));
    socket.on('error', (err) => console.log('❌ Socket error:', err));
}

testAuth();
```

---

## 📋 Implementation Checklist

### Backend Setup
- [ ] Session configured in Flask app (`SECRET_KEY`, `PERMANENT_SESSION_LIFETIME`)
- [ ] Login route sets `session['user_id']`, `session['role']`
- [ ] Auth decorators distinguish API vs page requests
- [ ] Video routes detect API requests and return JSON
- [ ] Socket.IO connect handler checks session
- [ ] Socket.IO join_room handler verifies role matches session

### Frontend Setup
- [ ] All fetch calls include `credentials: 'include'`
- [ ] Socket.IO initialized with `withCredentials: true`
- [ ] Auth checked BEFORE accessing camera/Socket.IO
- [ ] No token-based auth (no localStorage tokens)
- [ ] Error handling redirects to login on 401

### Testing
- [ ] Login works and sets session cookie
- [ ] Session cookie visible in DevTools
- [ ] API calls send session cookie
- [ ] Unauthorized requests return 401 JSON (not HTML)
- [ ] Socket.IO connects with valid session
- [ ] Socket.IO disconnects without session
- [ ] Video page redirects to login when not authenticated

---

## 🎯 Quick Reference

### Session-Based Auth Flow
```
1. User submits login form
2. Backend validates credentials
3. Backend sets session cookie: session['user_id'] = user.id
4. Browser stores cookie automatically
5. All subsequent requests include cookie
6. Backend reads session from cookie
7. Decorators check session for authorization
```

### Critical Frontend Code
```javascript
// Check auth FIRST
const isAuth = await fetch('/video/check-auth', { 
    credentials: 'include' 
});

// Socket.IO with credentials
const socket = io(SERVER_URL, { 
    withCredentials: true 
});

// API calls with credentials
await fetch('/video/start-meeting/1', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' }
});
```

### Critical Backend Code
```python
# Check without redirect
if 'user_id' not in session:
    return jsonify({'error': 'Not authenticated'}), 401

# Socket.IO auth
@socketio.on('connect')
def handle_connect():
    if 'user_id' not in session:
        return False
```

---

## 🆘 Emergency Troubleshooting

### "Unexpected token '<'" Error
1. Check if endpoint has `@login_required` decorator
2. Verify `/video/` routes are detected as API requests in decorators.py
3. Ensure frontend sends `Accept: application/json` header

### Socket.IO Won't Connect
1. Add `withCredentials: true` to Socket.IO client
2. Add session check to `@socketio.on('connect')`
3. Check browser console for CORS errors

### Session Lost on Redirect
1. Verify `session.permanent = True` in login
2. Check `PERMANENT_SESSION_LIFETIME` configuration
3. Ensure cookies are HttpOnly and SameSite=Lax

---

**Last Updated:** January 31, 2026  
**System:** Flask 3.0.0 + Flask-SocketIO 4.6.0 + Session-based auth
