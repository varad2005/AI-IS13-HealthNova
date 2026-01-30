/**
 * Razorpay Payment Integration
 * =============================
 * 
 * REUSABLE payment checkout function for:
 * - Doctor appointments
 * - Lab tests
 * - Health packages
 * - Any future paid features
 * 
 * ARCHITECTURE BENEFITS:
 * ---------------------
 * 1. Single function for all payments (DRY principle)
 * 2. No Razorpay SDK calls in HTML templates
 * 3. Consistent error handling across all payment flows
 * 4. Easy to test and maintain
 * 5. Works with existing backend routes
 * 
 * USAGE EXAMPLE:
 * --------------
 * <button onclick="initiatePayment(500, 'appointment', {appointment_id: '123'})">
 *     Pay ₹500 for Appointment
 * </button>
 * 
 * @requires Razorpay Checkout Script: https://checkout.razorpay.com/v1/checkout.js
 */

// ============================================================
// Configuration
// ============================================================

const PAYMENT_API = 'http://127.0.0.1:5000/payments';

/**
 * Initialize Razorpay payment checkout.
 * 
 * This is the ONLY function you need to call for payments.
 * 
 * @param {number} amount - Amount in rupees (e.g., 500 for ₹500)
 * @param {string} type - Payment type ('appointment', 'lab_test', 'package')
 * @param {Object} metadata - Additional data (appointment_id, patient_name, etc.)
 * @param {Function} onSuccess - Callback on successful payment
 * @param {Function} onFailure - Callback on payment failure
 */
async function initiatePayment(
    amount,
    type = 'general',
    metadata = {},
    onSuccess = null,
    onFailure = null
) {
    try {
        // Validate amount
        if (!amount || amount <= 0) {
            showPaymentError('Invalid amount');
            return;
        }
        
        // Show loading state
        showPaymentLoading(true);
        
        // Step 1: Create Razorpay order on backend
        const orderData = await createPaymentOrder(amount, type, metadata);
        
        if (!orderData.success) {
            throw new Error(orderData.error || 'Failed to create payment order');
        }
        
        // Step 2: Initialize Razorpay checkout
        const options = {
            key: orderData.key_id, // Razorpay Key ID from backend
            amount: orderData.order.amount, // Amount in paise
            currency: orderData.order.currency,
            name: 'Health Nova',
            description: getPaymentDescription(type, metadata),
            image: '/assets/images/logo.png', // Your logo
            order_id: orderData.order.id, // Order ID from backend
            
            // Prefill user details (if available)
            prefill: getPrefillData(),
            
            // Theme customization
            theme: {
                color: '#0dcaf0' // Bootstrap info color
            },
            
            // Payment success handler
            handler: async function(response) {
                await handlePaymentSuccess(response, type, metadata, onSuccess);
            },
            
            // Payment modal closed handler
            modal: {
                ondismiss: function() {
                    showPaymentLoading(false);
                    if (onFailure) {
                        onFailure('Payment cancelled by user');
                    }
                }
            }
        };
        
        // Step 3: Open Razorpay checkout
        const razorpay = new Razorpay(options);
        
        razorpay.on('payment.failed', function(response) {
            handlePaymentFailure(response, onFailure);
        });
        
        razorpay.open();
        showPaymentLoading(false);
        
    } catch (error) {
        console.error('Payment initiation error:', error);
        showPaymentError(error.message);
        showPaymentLoading(false);
        
        if (onFailure) {
            onFailure(error.message);
        }
    }
}

/**
 * Create payment order on backend.
 * 
 * @param {number} amount - Amount in rupees
 * @param {string} type - Payment type
 * @param {Object} metadata - Additional metadata
 * @returns {Promise<Object>} - Order data with key_id
 */
async function createPaymentOrder(amount, type, metadata) {
    const response = await fetch(`${PAYMENT_API}/create-order`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include', // Include session cookie
        body: JSON.stringify({
            amount: amount,
            currency: 'INR',
            receipt: `${type}_${Date.now()}`,
            notes: {
                type: type,
                ...metadata
            }
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create order');
    }
    
    return await response.json();
}

/**
 * Handle successful payment.
 * 
 * @param {Object} response - Razorpay payment response
 * @param {string} type - Payment type
 * @param {Object} metadata - Payment metadata
 * @param {Function} onSuccess - Success callback
 */
async function handlePaymentSuccess(response, type, metadata, onSuccess) {
    try {
        showPaymentLoading(true);
        
        // Verify payment signature on backend (SECURITY CRITICAL)
        const verificationResult = await fetch(`${PAYMENT_API}/verify-payment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
            })
        });
        
        const result = await verificationResult.json();
        
        if (result.success && result.verified) {
            // Payment verified successfully
            showPaymentSuccess(type, result.payment);
            
            // Call custom success handler
            if (onSuccess) {
                onSuccess(result.payment);
            }
            
            // Redirect or update UI based on payment type
            setTimeout(() => {
                redirectAfterPayment(type, metadata);
            }, 2000);
            
        } else {
            throw new Error('Payment verification failed');
        }
        
    } catch (error) {
        console.error('Payment verification error:', error);
        showPaymentError('Payment verification failed. Please contact support.');
    } finally {
        showPaymentLoading(false);
    }
}

/**
 * Handle payment failure.
 * 
 * @param {Object} response - Razorpay error response
 * @param {Function} onFailure - Failure callback
 */
function handlePaymentFailure(response, onFailure) {
    const errorMessage = response.error?.description || 'Payment failed';
    console.error('Payment failed:', response);
    
    showPaymentError(errorMessage);
    
    if (onFailure) {
        onFailure(errorMessage);
    }
}

// ============================================================
// Helper Functions
// ============================================================

/**
 * Get payment description based on type.
 */
function getPaymentDescription(type, metadata) {
    switch (type) {
        case 'appointment':
            return `Doctor Appointment - ${metadata.doctor_name || 'Health Nova'}`;
        case 'lab_test':
            return `Lab Test - ${metadata.test_name || 'Health Nova'}`;
        case 'package':
            return `Health Package - ${metadata.package_name || 'Health Nova'}`;
        default:
            return 'Health Nova - Payment';
    }
}

/**
 * Get prefilled user data for checkout.
 */
function getPrefillData() {
    // Try to get user info from session storage or local storage
    const userInfo = JSON.parse(sessionStorage.getItem('user_info') || '{}');
    
    return {
        name: userInfo.name || '',
        email: userInfo.email || '',
        contact: userInfo.phone || ''
    };
}

/**
 * Redirect after successful payment.
 */
function redirectAfterPayment(type, metadata) {
    switch (type) {
        case 'appointment':
            window.location.href = '/patient/dashboard.html';
            break;
        case 'lab_test':
            window.location.href = '/patient/profile.html';
            break;
        default:
            // Reload current page to show updated status
            window.location.reload();
    }
}

// ============================================================
// UI Feedback Functions
// ============================================================

/**
 * Show payment loading state.
 */
function showPaymentLoading(show) {
    // Remove existing loader if any
    const existingLoader = document.getElementById('paymentLoader');
    if (existingLoader) {
        existingLoader.remove();
    }
    
    if (show) {
        const loader = document.createElement('div');
        loader.id = 'paymentLoader';
        loader.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                        background: rgba(0,0,0,0.5); display: flex; align-items: center; 
                        justify-content: center; z-index: 9999;">
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">Processing payment...</span>
                </div>
            </div>
        `;
        document.body.appendChild(loader);
    }
}

/**
 * Show payment success message.
 */
function showPaymentSuccess(type, payment) {
    const message = `Payment successful! Transaction ID: ${payment.id}`;
    
    // Use Bootstrap alert if available
    if (typeof bootstrap !== 'undefined') {
        showBootstrapAlert(message, 'success');
    } else {
        alert(message);
    }
}

/**
 * Show payment error message.
 */
function showPaymentError(message) {
    // Use Bootstrap alert if available
    if (typeof bootstrap !== 'undefined') {
        showBootstrapAlert(message, 'danger');
    } else {
        alert(`Payment Error: ${message}`);
    }
}

/**
 * Show Bootstrap alert (if Bootstrap is loaded).
 */
function showBootstrapAlert(message, type) {
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show position-fixed 
                    top-0 start-50 translate-middle-x mt-3" 
             style="z-index: 10000; min-width: 300px;" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertDiv = document.createElement('div');
    alertDiv.innerHTML = alertHTML;
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// ============================================================
// Convenience Functions for Common Payment Types
// ============================================================

/**
 * Quick function for appointment payment.
 */
function payForAppointment(appointmentId, doctorName, amount, onSuccess) {
    return initiatePayment(
        amount,
        'appointment',
        {
            appointment_id: appointmentId,
            doctor_name: doctorName
        },
        onSuccess
    );
}

/**
 * Quick function for lab test payment.
 */
function payForLabTest(testId, testName, amount, onSuccess) {
    return initiatePayment(
        amount,
        'lab_test',
        {
            test_id: testId,
            test_name: testName
        },
        onSuccess
    );
}

/**
 * Quick function for health package payment.
 */
function payForPackage(packageId, packageName, amount, onSuccess) {
    return initiatePayment(
        amount,
        'package',
        {
            package_id: packageId,
            package_name: packageName
        },
        onSuccess
    );
}

// ============================================================
// Load Razorpay SDK
// ============================================================

/**
 * Dynamically load Razorpay checkout script.
 * Call this on page load if not already included in HTML.
 */
function loadRazorpayScript() {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (typeof Razorpay !== 'undefined') {
            resolve(true);
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.onload = () => resolve(true);
        script.onerror = () => reject(new Error('Failed to load Razorpay SDK'));
        document.head.appendChild(script);
    });
}

// ============================================================
// Example Usage in HTML
// ============================================================

/*

<!-- Include this file in your HTML -->
<script src="/js/razorpay-integration.js"></script>

<!-- Example 1: Simple payment button -->
<button class="btn btn-primary" 
        onclick="initiatePayment(500, 'appointment', {appointment_id: '123'})">
    Pay ₹500
</button>

<!-- Example 2: Appointment payment with callback -->
<button class="btn btn-success" 
        onclick="payForAppointment('APT-123', 'Dr. Sharma', 300, function(payment) {
            console.log('Payment successful:', payment);
            alert('Appointment confirmed!');
        })">
    Book Appointment - ₹300
</button>

<!-- Example 3: Lab test payment -->
<button class="btn btn-info" 
        onclick="payForLabTest('LT-456', 'Blood Test', 250, null)">
    Pay for Blood Test - ₹250
</button>

<!-- Example 4: Dynamic payment from form -->
<form onsubmit="event.preventDefault(); 
                initiatePayment(
                    document.getElementById('amount').value,
                    'appointment',
                    {doctor_id: document.getElementById('doctorId').value}
                );">
    <input type="number" id="amount" placeholder="Amount" required>
    <input type="hidden" id="doctorId" value="DOC-789">
    <button type="submit" class="btn btn-primary">Pay Now</button>
</form>

*/
