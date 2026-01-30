// Rural Healthcare Platform - Main JavaScript
// This file will contain fetch API calls to communicate with backend

// Base API URL
const API_BASE_URL = 'http://localhost:5000';

// Helper function to make API calls with session cookies
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include' // Important: Include cookies for session management
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        
        return {
            success: response.ok,
            status: response.status,
            data: result
        };
    } catch (error) {
        console.error('API call error:', error);
        return {
            success: false,
            status: 0,
            data: { message: 'Network error occurred' }
        };
    }
}

// Authentication functions
async function login(phoneNumber, password) {
    return await apiCall('/auth/login', 'POST', {
        phone_number: phoneNumber,
        password: password
    });
}

async function register(userData) {
    return await apiCall('/auth/register', 'POST', userData);
}

async function logout() {
    return await apiCall('/auth/logout', 'POST');
}

async function checkSession() {
    return await apiCall('/auth/check-session', 'GET');
}

// Patient functions
async function getPatientDashboard() {
    return await apiCall('/patient/dashboard', 'GET');
}

async function getPatientProfile() {
    return await apiCall('/patient/profile', 'GET');
}

async function updatePatientProfile(profileData) {
    return await apiCall('/patient/profile', 'PUT', profileData);
}

async function createVisit(symptoms) {
    return await apiCall('/patient/visits', 'POST', { symptoms });
}

async function getPatientVisits() {
    return await apiCall('/patient/visits', 'GET');
}

async function getPatientLabTests() {
    return await apiCall('/patient/lab-tests', 'GET');
}

async function getPatientPrescriptions() {
    return await apiCall('/patient/prescriptions', 'GET');
}

// Doctor functions
async function getDoctorDashboard() {
    return await apiCall('/doctor/dashboard', 'GET');
}

async function getDoctorPatients() {
    return await apiCall('/doctor/patients', 'GET');
}

async function getPatientDetails(patientId) {
    return await apiCall(`/doctor/patients/${patientId}`, 'GET');
}

async function addDiagnosis(visitId, diagnosisData) {
    return await apiCall(`/doctor/visits/${visitId}/diagnose`, 'PUT', diagnosisData);
}

async function addPrescription(visitId, prescriptionData) {
    return await apiCall(`/doctor/visits/${visitId}/prescriptions`, 'POST', prescriptionData);
}

async function requestLabTest(visitId, testData) {
    return await apiCall(`/doctor/visits/${visitId}/lab-tests`, 'POST', testData);
}

async function completeVisit(visitId) {
    return await apiCall(`/doctor/visits/${visitId}/complete`, 'POST');
}

// Lab functions
async function getLabDashboard() {
    return await apiCall('/lab/dashboard', 'GET');
}

async function getLabTests(status = null) {
    const endpoint = status ? `/lab/tests?status=${status}` : '/lab/tests';
    return await apiCall(endpoint, 'GET');
}

async function approveLabTest(testId) {
    return await apiCall(`/lab/tests/${testId}/approve`, 'POST');
}

async function rejectLabTest(testId, remarks) {
    return await apiCall(`/lab/tests/${testId}/reject`, 'POST', { remarks });
}

async function scheduleLabTest(testId, scheduledTime) {
    return await apiCall(`/lab/tests/${testId}/schedule`, 'POST', {
        scheduled_time: scheduledTime
    });
}

async function updateLabTestResult(testId, resultData) {
    return await apiCall(`/lab/tests/${testId}/update`, 'PUT', resultData);
}

async function uploadLabReport(testId, reportData) {
    return await apiCall(`/lab/tests/${testId}/reports`, 'POST', reportData);
}

async function completeLabTest(testId) {
    return await apiCall(`/lab/tests/${testId}/complete`, 'POST');
}

// Utility functions
function showMessage(message, type = 'info') {
    // Simple alert for now - can be enhanced with better UI
    alert(message);
}

function redirectBasedOnRole(role) {
    const redirectUrls = {
        'patient': '/frontend/patient/dashboard.html',
        'doctor': '/frontend/doctor/dashboard.html',
        'lab': '/frontend/lab/dashboard.html'
    };
    
    if (redirectUrls[role]) {
        window.location.href = redirectUrls[role];
    }
}

// Export functions for use in HTML pages
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        apiCall,
        login,
        register,
        logout,
        checkSession,
        getPatientDashboard,
        getDoctorDashboard,
        getLabDashboard
    };
}
