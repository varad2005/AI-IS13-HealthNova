# Health Nova

A comprehensive full-stack web platform connecting patients, doctors, and labs in rural areas with digital health records, visit management, lab tests, and prescriptions.

## 📁 Project Structure

```
rural-healthcare-platform/
│
├── frontend/                          # Frontend HTML/CSS/JS
│   ├── landing.html                  # Homepage with role selection
│   ├── login.html                    # Login page
│   ├── register.html                 # Registration page
│   │
│   ├── patient/                      # Patient pages
│   │   ├── dashboard.html           # Patient dashboard
│   │   └── profile.html             # Patient profile view
│   │
│   ├── doctor/                       # Doctor pages
│   │   ├── dashboard.html           # Doctor dashboard
│   │   └── patient_profile.html     # Patient profile (doctor view)
│   │
│   ├── lab/                          # Lab pages
│   │   └── dashboard.html           # Lab dashboard
│   │
│   ├── assets/                       # Static assets
│   │   ├── css/
│   │   │   └── style.css           # Main stylesheet
│   │   ├── images/                 # Images
│   │   └── icons/                  # Icons
│   │
│   └── js/
│       └── main.js                  # API calls and utilities
│
├── backend/                          # Flask Backend
│   ├── app.py                       # Main application
│   ├── config.py                    # Configuration
│   ├── models.py                    # Database models
│   ├── requirements.txt             # Python dependencies
│   │
│   ├── auth/                        # Authentication module
│   │   ├── __init__.py
│   │   ├── routes.py               # Login, register, logout
│   │   └── decorators.py           # Role-based decorators
│   │
│   ├── patient/                     # Patient module
│   │   ├── __init__.py
│   │   └── routes.py               # Patient endpoints
│   │
│   ├── doctor/                      # Doctor module
│   │   ├── __init__.py
│   │   └── routes.py               # Doctor endpoints
│   │
│   ├── lab/                         # Lab module
│   │   ├── __init__.py
│   │   └── routes.py               # Lab endpoints
│   │
│   ├── utils/                       # Utilities
│   │   ├── __init__.py
│   │   └── helpers.py              # Helper functions
│   │
│   └── uploads/                     # File uploads
│       └── reports/                # Lab reports
│
├── database/
│   └── schema.sql                   # Database schema (reference)
│
├── .env                             # Environment variables
└── README.md                        # This file
```

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create PostgreSQL database
createdb rural_health

# Setup environment variables
# Edit .env file in project root with your database credentials

# Initialize database
python setup_db.py

# Run backend server
python app.py
```

Backend runs at: `http://localhost:5000`

### 2. Frontend Setup

Open a new terminal:

```bash
# Serve frontend files
python -m http.server 8000
```

Access at: `http://localhost:8000/frontend/landing.html`

Or simply open `frontend/landing.html` in your browser.

## 🔐 User Roles

1. **Patient** - Creates visits, views history, tracks lab tests
2. **Doctor** - Diagnoses, prescribes medications, manages visits
3. **Lab** - Processes tests, uploads results, schedules appointments

## 📚 Documentation

- **[Backend Setup](backend/README.md)** - Detailed backend documentation
- **[API Testing](backend/API_TESTING.md)** - Complete API testing guide
- **[Database Schema](database/schema.sql)** - Database structure reference

## 🛠️ Technology Stack

### Backend
- **Flask 3.0.0** - Web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Werkzeug** - Password hashing
- **Flask-Migrate** - Database migrations

### Frontend
- **HTML5, CSS3, JavaScript**
- **Bootstrap Icons**
- **Fetch API** - Backend communication
- **Session-based authentication**

## 🎯 Features

### Authentication & Security
✅ Session-based authentication
✅ Password hashing
✅ Role-based access control
✅ Input validation

### Patient Features
✅ Digital health profile
✅ Create visits with symptoms
✅ View visit history (append-only)
✅ Track lab test status
✅ Access prescriptions

### Doctor Features
✅ View assigned patients
✅ Review patient history
✅ Add diagnosis and notes
✅ Prescribe medications
✅ Request lab tests
✅ Complete visits

### Lab Features
✅ View test requests
✅ Approve/reject tests
✅ Schedule appointments
✅ Update test results
✅ Upload report metadata

## 📋 API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` - Register user
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `GET /auth/me` - Get current user
- `GET /auth/check-session` - Check session

### Patient (`/patient`)
- `GET /patient/dashboard` - Dashboard data
- `GET /patient/profile` - Get profile
- `PUT /patient/profile` - Update profile
- `POST /patient/visits` - Create visit
- `GET /patient/visits` - Get all visits
- `GET /patient/lab-tests` - Get lab tests
- `GET /patient/prescriptions` - Get prescriptions

### Doctor (`/doctor`)
- `GET /doctor/dashboard` - Dashboard data
- `GET /doctor/patients` - Get assigned patients
- `GET /doctor/patients/<id>` - Get patient details
- `PUT /doctor/visits/<id>/diagnose` - Add diagnosis
- `POST /doctor/visits/<id>/prescriptions` - Add prescription
- `POST /doctor/visits/<id>/lab-tests` - Request lab test
- `POST /doctor/visits/<id>/complete` - Complete visit

### Lab (`/lab`)
- `GET /lab/dashboard` - Dashboard data
- `GET /lab/tests` - Get all tests
- `POST /lab/tests/<id>/approve` - Approve test
- `POST /lab/tests/<id>/reject` - Reject test
- `POST /lab/tests/<id>/schedule` - Schedule test
- `PUT /lab/tests/<id>/update` - Update results
- `POST /lab/tests/<id>/reports` - Upload report
- `POST /lab/tests/<id>/complete` - Complete test

Full API documentation: [backend/API_TESTING.md](backend/API_TESTING.md)

## 🧪 Testing

### Test the Backend API

```bash
# Health check
curl http://localhost:5000/health

# Register a patient
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"9876543210","password":"test123","role":"patient","full_name":"Test Patient"}'

# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"phone_number":"9876543210","password":"test123"}'
```

See [backend/API_TESTING.md](backend/API_TESTING.md) for complete test workflow.

## 🔒 Security Features

- ✅ Session-based authentication (no JWT)
- ✅ Password hashing with werkzeug
- ✅ Role-based access control
- ✅ Input validation
- ✅ CSRF protection ready
- ✅ No hardcoded credentials
- ✅ .env for sensitive data

## 🚧 Future Enhancements

- [ ] Real file upload for lab reports
- [ ] Email/SMS notifications
- [ ] Real-time messaging (WebSockets)
- [ ] Admin panel
- [ ] Analytics dashboard
- [ ] AI symptom analysis
- [ ] Mobile responsive improvements
- [ ] PWA support

## 📱 Frontend Integration

The frontend uses `fetch` API in `frontend/js/main.js` to communicate with the backend. All API calls include credentials for session management.

Example usage:
```javascript
// Login user
const result = await login('9876543210', 'test123');
if (result.success) {
    redirectBasedOnRole(result.data.data.user.role);
}
```

## 🎓 Use Cases

- ✅ College project
- ✅ Hackathon demo
- ✅ Portfolio project
- ✅ Learning full-stack development

## ⚠️ Important Notes

- **NOT for production hospital use** - This is a demonstration/learning project
- Requires PostgreSQL database
- Use HTTPS in production
- Add CORS configuration if frontend and backend on different domains

## 🤝 Contributing

Feel free to:
- Add features
- Improve UI/UX
- Enhance security
- Add tests
- Improve documentation

## 📄 License

Educational/Personal use

## 🆘 Troubleshooting

### Backend Issues
1. Check PostgreSQL is running
2. Verify database credentials in `.env`
3. Ensure virtual environment is activated
4. Run `python setup_db.py` to initialize database

### Frontend Issues
1. Check backend is running at `http://localhost:5000`
2. Enable CORS if needed (see backend config)
3. Check browser console for errors
4. Verify API endpoint URLs in `main.js`

### Database Issues
1. Ensure PostgreSQL service is running
2. Database `rural_health` must exist
3. Check connection string in `.env`
4. Run migrations: `flask db upgrade`

## 📞 Support

For issues or questions:
1. Check [Backend README](backend/README.md)
2. Review [API Testing Guide](backend/API_TESTING.md)
3. Use `backend/admin_utils.py` for database management

---

**Built with Flask, PostgreSQL, HTML/CSS/JavaScript**
**Version: 1.0.0**
**Date: January 2026**

🎉 **Project Status: Complete and Ready!**
