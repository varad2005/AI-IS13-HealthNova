-- Rural Healthcare Platform Database Schema
-- PostgreSQL Schema for reference
-- Note: SQLAlchemy will create tables automatically, this is for reference only

-- Users table (authentication)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('patient', 'doctor', 'lab')),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Patient profiles
CREATE TABLE patient_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    gender VARCHAR(20),
    blood_group VARCHAR(5),
    address TEXT,
    emergency_contact VARCHAR(15),
    allergies TEXT,
    chronic_conditions TEXT,
    previous_surgeries TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Visits (append-only history)
CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    patient_profile_id INTEGER NOT NULL REFERENCES patient_profiles(id) ON DELETE CASCADE,
    doctor_id INTEGER REFERENCES users(id),
    symptoms TEXT NOT NULL,
    diagnosis TEXT,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Lab tests
CREATE TABLE lab_tests (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
    lab_id INTEGER REFERENCES users(id),
    test_name VARCHAR(200) NOT NULL,
    test_type VARCHAR(100),
    instructions TEXT,
    status VARCHAR(20) DEFAULT 'requested' CHECK (status IN ('requested', 'approved', 'rejected', 'scheduled', 'completed')),
    scheduled_time TIMESTAMP,
    result TEXT,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test reports (file metadata)
CREATE TABLE test_reports (
    id SERIAL PRIMARY KEY,
    lab_test_id INTEGER NOT NULL REFERENCES lab_tests(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prescriptions
CREATE TABLE prescriptions (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
    medication_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    duration VARCHAR(100) NOT NULL,
    instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages (patient-doctor communication)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id),
    message_type VARCHAR(20) DEFAULT 'text' CHECK (message_type IN ('text', 'voice')),
    content TEXT,
    voice_file_path VARCHAR(500),
    voice_duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);

-- Indexes for better query performance
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_visits_patient ON visits(patient_profile_id);
CREATE INDEX idx_visits_doctor ON visits(doctor_id);
CREATE INDEX idx_visits_status ON visits(status);
CREATE INDEX idx_lab_tests_visit ON lab_tests(visit_id);
CREATE INDEX idx_lab_tests_lab ON lab_tests(lab_id);
CREATE INDEX idx_lab_tests_status ON lab_tests(status);
CREATE INDEX idx_messages_visit ON messages(visit_id);

-- Sample queries for reference

-- Get patient's complete history
-- SELECT v.*, u.full_name as doctor_name 
-- FROM visits v 
-- LEFT JOIN users u ON v.doctor_id = u.id 
-- WHERE v.patient_profile_id = ?
-- ORDER BY v.created_at DESC;

-- Get doctor's assigned patients
-- SELECT DISTINCT pp.*, u.full_name, u.phone_number
-- FROM patient_profiles pp
-- JOIN users u ON pp.user_id = u.id
-- JOIN visits v ON v.patient_profile_id = pp.id
-- WHERE v.doctor_id = ?;

-- Get pending lab tests
-- SELECT lt.*, v.symptoms, pp.user_id
-- FROM lab_tests lt
-- JOIN visits v ON lt.visit_id = v.id
-- JOIN patient_profiles pp ON v.patient_profile_id = pp.id
-- WHERE lt.status IN ('requested', 'approved', 'scheduled');
