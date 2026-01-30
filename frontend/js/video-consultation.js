/**
 * Video Consultation Manager
 * 
 * DOCTOR-CONTROLLED MEETING LIFECYCLE:
 * - Only doctors can start meetings (calls /video/start-meeting)
 * - Patients can only join when meeting_status == 'live'
 * - Uses appointment_id as WebRTC room identifier
 * - No manual meeting IDs or sharing required
 * 
 * SECURITY FEATURES:
 * - Role-based access control on backend
 * - Ownership verification (doctor/patient must own appointment)
 * - Status validation prevents unauthorized joins
 * 
 * USAGE:
 * Doctor Dashboard:
 *   <button onclick="startConsultation(appointmentId)">Start Consultation</button>
 * 
 * Patient Dashboard:
 *   <button id="join-btn-123" onclick="joinConsultation(appointmentId)" disabled>Join Consultation</button>
 *   <script>pollMeetingStatus(appointmentId, 'join-btn-123');</script>
 */

// API base URL (update for production)
const API_BASE = window.location.origin;

/**
 * Doctor starts a video consultation
 * 
 * WORKFLOW:
 * 1. Call POST /video/start-meeting/<appointment_id>
 * 2. Backend sets meeting_status = 'live'
 * 3. Redirect doctor to video-call.html with appointment_id as room
 * 4. Patient's Join button automatically enables (via polling)
 */
async function startConsultation(appointmentId) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        alert('Please login first');
        window.location.href = '/login.html';
        return;
    }
    
    try {
        // Show loading state
        const button = event.target.closest('button');
        const originalHTML = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Starting...';
        
        // Start the meeting on backend
        const response = await fetch(`${API_BASE}/video/start-meeting/${appointmentId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to start meeting');
        }
        
        // Get doctor name from localStorage or use default
        const userName = localStorage.getItem('userName') || 'Doctor';
        const userRole = 'doctor';
        
        // Redirect to video call page using appointment_id as room
        // WHY: appointment_id is the WebRTC room identifier (no manual IDs)
        const videoUrl = `/patient/video-call.html?appointment_id=${appointmentId}&type=${userRole}&name=${encodeURIComponent(userName)}`;
        
        window.location.href = videoUrl;
        
    } catch (error) {
        console.error('Error starting consultation:', error);
        alert(`Failed to start consultation: ${error.message}`);
        
        // Restore button
        if (button) {
            button.disabled = false;
            button.innerHTML = originalHTML;
        }
    }
}

/**
 * Patient joins a video consultation
 * 
 * WORKFLOW:
 * 1. Get meeting status (should already be 'live' if button is enabled)
 * 2. Redirect to video-call.html with appointment_id as room
 * 3. WebRTC signaling uses appointment_id to connect both users
 * 
 * SECURITY: Patient can only join if meeting_status == 'live'
 */
async function joinConsultation(appointmentId) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        alert('Please login first');
        window.location.href = '/login.html';
        return;
    }
    
    try {
        // Show loading state
        const button = event.target.closest('button');
        const originalHTML = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Joining...';
        
        // Verify meeting is live
        const response = await fetch(`${API_BASE}/video/meeting-status/${appointmentId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to check meeting status');
        }
        
        if (!data.can_join) {
            throw new Error(data.message || 'Meeting is not available to join');
        }
        
        // Get patient name from localStorage or use default
        const userName = localStorage.getItem('userName') || 'Patient';
        const userRole = 'patient';
        
        // Redirect to video call page using appointment_id as room
        const videoUrl = `/patient/video-call.html?appointment_id=${appointmentId}&type=${userRole}&name=${encodeURIComponent(userName)}`;
        
        window.location.href = videoUrl;
        
    } catch (error) {
        console.error('Error joining consultation:', error);
        alert(`Failed to join consultation: ${error.message}`);
        
        // Restore button
        if (button) {
            button.disabled = false;
            button.innerHTML = originalHTML;
        }
    }
}

/**
 * Poll meeting status for a patient (updates UI automatically)
 * 
 * USE CASE: Patient dashboard
 * - Polls every 3 seconds
 * - Enables Join button when status='live'
 * - Updates status message
 * - Stops polling when meeting ends
 * 
 * @param {number} appointmentId - The appointment ID
 * @param {string} buttonId - ID of the Join button element
 * @param {string} statusId - ID of the status message element (optional)
 */
let pollIntervals = {}; // Store interval IDs per appointment

function pollMeetingStatus(appointmentId, buttonId, statusId = null) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        console.warn('No token found, stopping poll');
        return;
    }
    
    // Clear existing interval if any
    if (pollIntervals[appointmentId]) {
        clearInterval(pollIntervals[appointmentId]);
    }
    
    // Poll immediately, then every 3 seconds
    checkMeetingStatus(appointmentId, buttonId, statusId);
    
    pollIntervals[appointmentId] = setInterval(() => {
        checkMeetingStatus(appointmentId, buttonId, statusId);
    }, 3000);
}

/**
 * Check meeting status once and update UI
 * (Called by pollMeetingStatus)
 */
async function checkMeetingStatus(appointmentId, buttonId, statusId) {
    const token = localStorage.getItem('token');
    const button = document.getElementById(buttonId);
    const statusEl = statusId ? document.getElementById(statusId) : null;
    
    if (!button) {
        console.warn(`Button ${buttonId} not found, stopping poll`);
        if (pollIntervals[appointmentId]) {
            clearInterval(pollIntervals[appointmentId]);
        }
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/video/meeting-status/${appointmentId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            console.error('Failed to check meeting status:', data.error);
            return;
        }
        
        // Update button state
        button.disabled = !data.can_join;
        
        // Update button appearance based on status
        if (data.meeting_status === 'live') {
            button.classList.remove('btn-secondary');
            button.classList.add('btn-success');
            button.innerHTML = '<i class="bi bi-camera-video-fill me-2"></i>Join Consultation';
        } else if (data.meeting_status === 'ended') {
            button.classList.remove('btn-success');
            button.classList.add('btn-secondary');
            button.innerHTML = '<i class="bi bi-x-circle me-2"></i>Consultation Ended';
            
            // Stop polling if meeting ended
            if (pollIntervals[appointmentId]) {
                clearInterval(pollIntervals[appointmentId]);
                delete pollIntervals[appointmentId];
            }
        } else {
            // not_started
            button.classList.remove('btn-success');
            button.classList.add('btn-secondary');
            button.innerHTML = '<i class="bi bi-clock me-2"></i>Waiting for Doctor...';
        }
        
        // Update status message if element exists
        if (statusEl) {
            statusEl.textContent = data.message;
            
            // Add appropriate color classes
            statusEl.className = 'small fw-semibold';
            if (data.meeting_status === 'live') {
                statusEl.classList.add('text-success');
            } else if (data.meeting_status === 'ended') {
                statusEl.classList.add('text-muted');
            } else {
                statusEl.classList.add('text-warning');
            }
        }
        
    } catch (error) {
        console.error('Error checking meeting status:', error);
    }
}

/**
 * Stop polling for a specific appointment
 * (Call this when navigating away from appointments page)
 */
function stopPolling(appointmentId) {
    if (pollIntervals[appointmentId]) {
        clearInterval(pollIntervals[appointmentId]);
        delete pollIntervals[appointmentId];
    }
}

/**
 * Stop all polling intervals
 * (Call this on page unload)
 */
function stopAllPolling() {
    Object.keys(pollIntervals).forEach(appointmentId => {
        clearInterval(pollIntervals[appointmentId]);
    });
    pollIntervals = {};
}

// Cleanup on page unload
window.addEventListener('beforeunload', stopAllPolling);

/**
 * Doctor ends a consultation
 * 
 * WORKFLOW:
 * 1. Call POST /video/end-meeting/<appointment_id>
 * 2. Backend sets meeting_status = 'ended'
 * 3. Update UI to show ended state
 * 4. Optionally redirect to dashboard
 */
async function endConsultation(appointmentId, redirectToDashboard = false) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        alert('Please login first');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/video/end-meeting/${appointmentId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to end meeting');
        }
        
        if (redirectToDashboard) {
            window.location.href = '/doctor/dashboard.html';
        }
        
        return data;
        
    } catch (error) {
        console.error('Error ending consultation:', error);
        alert(`Failed to end consultation: ${error.message}`);
        throw error;
    }
}

/**
 * Fetch user's appointments
 * 
 * USE CASE: Populate appointments list on dashboards
 * 
 * @param {object} filters - Optional filters
 * @param {string} filters.status - 'scheduled', 'completed', 'cancelled'
 * @param {string} filters.meeting_status - 'not_started', 'live', 'ended'
 * @param {boolean} filters.upcoming - Only future appointments
 * @returns {Promise<Array>} Array of appointment objects
 */
async function fetchMyAppointments(filters = {}) {
    try {
        // Use session-based authentication
        const response = await fetch('/patient/appointments', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch appointments');
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            let appointments = data.data;
            
            // Apply filters
            if (filters.status) {
                appointments = appointments.filter(apt => apt.status === filters.status);
            }
            
            if (filters.meeting_status) {
                appointments = appointments.filter(apt => apt.meeting_status === filters.meeting_status);
            }
            
            if (filters.upcoming) {
                const now = new Date();
                appointments = appointments.filter(apt => new Date(apt.appointment_date) >= now);
            }
            
            return appointments;
        }
        
        return [];
        
    } catch (error) {
        console.error('Error fetching appointments:', error);
        return [];
    }
}

/**
 * Create a new appointment
 * 
 * USE CASE: Book appointment from patient/admin dashboard
 * 
 * @param {object} appointmentData - Appointment details
 * @param {number} appointmentData.doctor_id - Doctor ID
 * @param {string} appointmentData.appointment_date - ISO datetime string
 * @param {string} appointmentData.reason - Reason for consultation
 * @param {number} appointmentData.duration_minutes - Duration (default: 30)
 * @returns {Promise<object>} Created appointment object
 */
async function createAppointment(appointmentData) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        throw new Error('Please login first');
    }
    
    try {
        const response = await fetch(`${API_BASE}/video/create-appointment`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(appointmentData)
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to create appointment');
        }
        
        return data.appointment;
        
    } catch (error) {
        console.error('Error creating appointment:', error);
        throw error;
    }
}

// Export functions for use in other modules (if using module system)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        startConsultation,
        joinConsultation,
        pollMeetingStatus,
        stopPolling,
        stopAllPolling,
        endConsultation,
        fetchMyAppointments,
        createAppointment
    };
}
