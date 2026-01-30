# Rural Healthcare Platform - Backend Setup Guide

## Project Structure

```
backend/
├── app.py                  # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── auth/
│   ├── __init__.py
│   ├── routes.py         # Authentication endpoints
│   └── decorators.py     # Auth decorators (login_required, role_required)
├── patient/
│   ├── __init__.py
│   └── routes.py         # Patient endpoints
├── doctor/
│   ├── __init__.py
│   └── routes.py         # Doctor endpoints
├── lab/
│   ├── __init__.py
│   └── routes.py         # Lab endpoints
└── utils/
    ├── __init__.py
    └── helpers.py        # Helper functions
```

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## Installation Steps

### 1. Install PostgreSQL (if not installed)

Download and install PostgreSQL from: https://www.postgresql.org/download/windows/

### 2. Create Database

Open PostgreSQL command line (psql) or pgAdmin and run:

```sql
CREATE DATABASE rural_health;
```

### 3. Set Up Python Virtual Environment

```bash
cd backend
python -m venv venv
```

### 4. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Database Connection

Create a `.env` file in the `backend/` directory:

```env
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/rural_health
FLASK_ENV=development
```

**Note:** Replace `your_postgres_password` with your actual PostgreSQL password.

### 7. Initialize Database

```bash
# Initialize Flask-Migrate
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migration to database
flask db upgrade
```

**Alternative (if Flask-Migrate gives issues):**

Open Python shell in the backend directory:

```bash
python
```

Then run:

```python
from app import create_app
from models import db

app = create_app('development')
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
```

### 8. Run the Application

```bash
python app.py
```

The server will start at: `http://localhost:5000`

## API Endpoints Overview

### Authentication (`/auth`)

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user info
- `GET /auth/check-session` - Check session status

### Patient Routes (`/patient`)

- `GET /patient/dashboard` - Get patient dashboard
- `GET /patient/profile` - Get patient profile
- `PUT /patient/profile` - Update patient profile
- `GET /patient/visits` - Get all visits
- `POST /patient/visits` - Create new visit
- `GET /patient/visits/<id>` - Get specific visit
- `GET /patient/lab-tests` - Get all lab tests
- `GET /patient/prescriptions` - Get all prescriptions

### Doctor Routes (`/doctor`)

- `GET /doctor/dashboard` - Get doctor dashboard
- `GET /doctor/patients` - Get all assigned patients
- `GET /doctor/patients/<id>` - Get patient details
- `GET /doctor/visits` - Get all visits
- `GET /doctor/visits/<id>` - Get specific visit
- `PUT /doctor/visits/<id>/diagnose` - Add diagnosis
- `POST /doctor/visits/<id>/prescriptions` - Add prescription
- `POST /doctor/visits/<id>/lab-tests` - Request lab test
- `POST /doctor/visits/<id>/complete` - Complete visit

### Lab Routes (`/lab`)

- `GET /lab/dashboard` - Get lab dashboard
- `GET /lab/tests` - Get all lab tests
- `GET /lab/tests/<id>` - Get specific test
- `POST /lab/tests/<id>/approve` - Approve test
- `POST /lab/tests/<id>/reject` - Reject test
- `POST /lab/tests/<id>/schedule` - Schedule test
- `PUT /lab/tests/<id>/update` - Update test results
- `POST /lab/tests/<id>/reports` - Upload report metadata
- `POST /lab/tests/<id>/complete` - Complete test

## Testing the API

### Using cURL

**Register a Patient:**
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\":\"9876543210\",\"password\":\"patient123\",\"role\":\"patient\",\"full_name\":\"John Doe\"}"
```

**Register a Doctor:**
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\":\"9876543211\",\"password\":\"doctor123\",\"role\":\"doctor\",\"full_name\":\"Dr. Smith\"}"
```

**Login:**
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d "{\"phone_number\":\"9876543210\",\"password\":\"patient123\"}"
```

**Access Protected Route:**
```bash
curl -X GET http://localhost:5000/patient/dashboard \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

### Using Postman

1. Import the API endpoints
2. Set up session cookies for authentication
3. Test each endpoint with appropriate payloads

## Database Models

### User
- Stores authentication credentials
- Supports 3 roles: patient, doctor, lab
- Passwords are hashed using werkzeug.security

### PatientProfile
- One per patient user
- Contains demographic and medical history
- Linked to User via one-to-one relationship

### Visit
- Represents one health issue/consultation
- Append-only (never modified, only added to)
- Links patient to doctor

### LabTest
- Lab test requests and results
- Can be assigned to lab users

### TestReport
- Metadata for uploaded lab reports
- Multiple reports per test allowed

### Prescription
- Doctor's prescriptions
- Linked to specific visit

### Message
- Communication between patient and doctor
- Supports text and voice metadata

## Security Features

✅ Session-based authentication (no JWT)
✅ Password hashing with werkzeug
✅ Role-based access control
✅ Access verification on all protected routes
✅ No hardcoded users or fake data

## Development Tips

1. **Debug Mode:** Set `FLASK_ENV=development` for detailed error messages
2. **Database Reset:** Drop all tables and recreate using `db.drop_all()` and `db.create_all()`
3. **Session Issues:** Clear cookies if authentication seems broken
4. **CORS:** Add Flask-CORS if connecting from different origin

## Common Issues

**Issue:** Database connection error
**Solution:** Verify PostgreSQL is running and credentials in `.env` are correct

**Issue:** Import errors
**Solution:** Ensure virtual environment is activated

**Issue:** Session not persisting
**Solution:** Check `SECRET_KEY` is set and cookies are being sent

## Next Steps

1. Test all endpoints manually
2. Connect with frontend
3. Implement file upload for lab reports
4. Add external AI integration API
5. Deploy to production server

## Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to secure random value
- [ ] Set `FLASK_ENV=production`
- [ ] Use strong database password
- [ ] Enable HTTPS
- [ ] Set up proper CORS policies
- [ ] Add rate limiting
- [ ] Set up logging
- [ ] Configure backup strategy
- [ ] Add input validation/sanitization
- [ ] Set up monitoring

---

**Built with Flask, PostgreSQL, and SQLAlchemy**
