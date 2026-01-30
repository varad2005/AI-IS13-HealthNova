"""
Payment Routes
==============

All payment-related API endpoints.

ARCHITECTURE BENEFITS:
---------------------
1. No Razorpay SDK calls in routes (all in service layer)
2. Reusable for any payment type (appointments, lab tests, packages)
3. Clean error handling with proper HTTP status codes
4. Easy to test with mocked service
5. Frontend gets consistent JSON responses

SECURITY:
---------
1. Signature verification happens server-side
2. Key secret never exposed to frontend
3. Amount validation prevents tampering
4. Payment status from Razorpay, not client
"""

from flask import request, jsonify, current_app
from . import payments_bp
from services.razorpay_service import get_razorpay_service
from auth.decorators import login_required
import traceback


@payments_bp.route('/create-order', methods=['POST'])
@login_required
def create_payment_order():
    """
    Create a Razorpay order for payment.
    
    This endpoint is REUSABLE for:
    - Doctor appointments
    - Lab tests
    - Health packages
    - Any future paid features
    
    Request Body:
    {
        "amount": 500,  // Amount in rupees (will be converted to paise)
        "currency": "INR",  // Optional, defaults to INR
        "receipt": "apt_123",  // Optional, your internal reference
        "notes": {  // Optional metadata
            "type": "appointment",
            "appointment_id": "123",
            "patient_name": "John Doe"
        }
    }
    
    Response:
    {
        "success": true,
        "order": {
            "id": "order_xxxxx",
            "amount": 50000,  // Amount in paise
            "currency": "INR",
            "receipt": "apt_123"
        },
        "key_id": "rzp_test_xxxxx"  // For frontend Razorpay checkout
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'amount' not in data:
            return jsonify({
                'success': False,
                'error': 'Amount is required'
            }), 400
        
        amount_inr = float(data['amount'])
        
        # Validate amount
        if amount_inr <= 0:
            return jsonify({
                'success': False,
                'error': 'Amount must be greater than 0'
            }), 400
        
        # Convert rupees to paise (Razorpay uses smallest currency unit)
        amount_paise = int(amount_inr * 100)
        
        # Get optional parameters
        currency = data.get('currency', 'INR')
        receipt = data.get('receipt')
        notes = data.get('notes', {})
        
        # Add user info to notes for tracking
        if 'user_id' in request.session:
            notes['user_id'] = request.session['user_id']
            notes['user_role'] = request.session.get('role', 'unknown')
        
        # Initialize Razorpay service
        service = get_razorpay_service(current_app.config)
        
        # Create order using service (NO direct SDK call in route)
        order = service.create_order(
            amount=amount_paise,
            currency=currency,
            receipt=receipt,
            notes=notes
        )
        
        return jsonify({
            'success': True,
            'order': order,
            'key_id': service.get_key_id()  # Frontend needs this for checkout
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        print(f"Payment order creation error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to create payment order. Please try again.'
        }), 500


@payments_bp.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    """
    Verify payment signature after successful payment.
    
    SECURITY CRITICAL: Always verify on server-side.
    Never trust payment status from frontend alone.
    
    Request Body:
    {
        "razorpay_order_id": "order_xxxxx",
        "razorpay_payment_id": "pay_xxxxx",
        "razorpay_signature": "signature_xxxxx"
    }
    
    Response:
    {
        "success": true,
        "verified": true,
        "payment": {
            "id": "pay_xxxxx",
            "status": "captured",
            "amount": 50000,
            "method": "upi"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required payment details'
            }), 400
        
        # Initialize Razorpay service
        service = get_razorpay_service(current_app.config)
        
        # Verify signature (NO direct SDK call in route)
        is_valid = service.verify_payment_signature(
            razorpay_order_id=data['razorpay_order_id'],
            razorpay_payment_id=data['razorpay_payment_id'],
            razorpay_signature=data['razorpay_signature']
        )
        
        if not is_valid:
            return jsonify({
                'success': False,
                'verified': False,
                'error': 'Invalid payment signature'
            }), 400
        
        # Fetch payment details from Razorpay
        payment_details = service.fetch_payment(data['razorpay_payment_id'])
        
        # TODO: Update your database here
        # Example:
        # - Mark appointment as paid
        # - Update lab test payment status
        # - Send confirmation email
        
        return jsonify({
            'success': True,
            'verified': True,
            'payment': {
                'id': payment_details['id'],
                'status': payment_details['status'],
                'amount': payment_details['amount'],
                'method': payment_details.get('method'),
                'email': payment_details.get('email'),
                'contact': payment_details.get('contact')
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'verified': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        print(f"Payment verification error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'verified': False,
            'error': 'Failed to verify payment. Please contact support.'
        }), 500


@payments_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """
    Razorpay webhook endpoint for payment notifications.
    
    IMPORTANT: Configure this URL in Razorpay Dashboard:
    Dashboard > Settings > Webhooks > Add Endpoint
    URL: https://yourdomain.com/payments/webhook
    
    Events to subscribe:
    - payment.captured
    - payment.failed
    - order.paid
    
    SECURITY:
    - Razorpay sends webhook secret in X-Razorpay-Signature header
    - Verify signature before processing
    - Configure webhook secret in .env
    """
    try:
        # Get webhook signature from header
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET')
        
        if not webhook_signature or not webhook_secret:
            return jsonify({'status': 'error', 'message': 'Missing signature'}), 400
        
        # Get webhook body
        webhook_body = request.get_data()
        
        # Verify webhook signature
        import hmac
        import hashlib
        expected_signature = hmac.new(
            webhook_secret.encode(),
            webhook_body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_signature, webhook_signature):
            return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400
        
        # Parse webhook data
        data = request.get_json()
        event = data.get('event')
        payload = data.get('payload', {})
        
        # Handle different events
        if event == 'payment.captured':
            payment_entity = payload.get('payment', {}).get('entity', {})
            print(f"Payment captured: {payment_entity.get('id')}")
            # TODO: Update database, send confirmation email
            
        elif event == 'payment.failed':
            payment_entity = payload.get('payment', {}).get('entity', {})
            print(f"Payment failed: {payment_entity.get('id')}")
            # TODO: Handle failed payment
            
        elif event == 'order.paid':
            order_entity = payload.get('order', {}).get('entity', {})
            print(f"Order paid: {order_entity.get('id')}")
            # TODO: Fulfill order
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"Webhook processing error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500


@payments_bp.route('/order/<order_id>', methods=['GET'])
@login_required
def get_order_status(order_id):
    """
    Get order details by ID.
    
    Useful for checking payment status.
    """
    try:
        service = get_razorpay_service(current_app.config)
        order = service.fetch_order(order_id)
        
        return jsonify({
            'success': True,
            'order': order
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
        
    except Exception as e:
        print(f"Order fetch error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch order details'
        }), 500


@payments_bp.route('/config', methods=['GET'])
def get_payment_config():
    """
    Get payment configuration for frontend.
    
    Returns public configuration only (safe to expose).
    NEVER return key_secret here.
    """
    try:
        service = get_razorpay_service(current_app.config)
        
        return jsonify({
            'success': True,
            'key_id': service.get_key_id(),
            'currency': 'INR'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to load payment configuration'
        }), 500


@payments_bp.route('/health', methods=['GET'])
def payment_health():
    """
    Health check for payment service.
    """
    try:
        # Try to initialize service (checks if credentials are configured)
        service = get_razorpay_service(current_app.config)
        
        return jsonify({
            'status': 'healthy',
            'service': 'payments',
            'razorpay_configured': bool(service.get_key_id())
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'payments',
            'razorpay_configured': False,
            'error': str(e)
        }), 500
