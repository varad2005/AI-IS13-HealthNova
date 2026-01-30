"""
Razorpay Service Module
=======================

WHY THIS ARCHITECTURE:
----------------------
1. Single Responsibility: All Razorpay SDK calls are in ONE place
2. Prevents Breaking Changes: Routes stay clean, easy to test
3. Reusability: Same service for appointments, lab tests, packages
4. Environment Safety: Keys loaded once from config, never hardcoded
5. Demo-Safe: Easy to switch between test/live modes

USAGE:
------
from services.razorpay_service import RazorpayService

service = RazorpayService(razorpay_key_id, razorpay_key_secret)
order = service.create_order(amount=500, currency='INR', receipt='receipt#123')
"""

import razorpay
from typing import Dict, Optional
import hmac
import hashlib


class RazorpayService:
    """
    Centralized service for all Razorpay payment operations.
    
    This class encapsulates ALL Razorpay SDK interactions, ensuring:
    - No SDK calls leak into Flask routes
    - No SDK calls leak into HTML templates
    - Easy to mock for testing
    - Easy to switch payment providers if needed
    """
    
    def __init__(self, key_id: str, key_secret: str):
        """
        Initialize Razorpay client with credentials from environment.
        
        Args:
            key_id: Razorpay Key ID (from RAZORPAY_KEY_ID env variable)
            key_secret: Razorpay Key Secret (from RAZORPAY_KEY_SECRET env variable)
        """
        if not key_id or not key_secret:
            raise ValueError("Razorpay credentials are required. Check your .env file.")
        
        self.key_id = key_id
        self.key_secret = key_secret
        self.client = razorpay.Client(auth=(key_id, key_secret))
        
    def create_order(
        self, 
        amount: int, 
        currency: str = 'INR',
        receipt: Optional[str] = None,
        notes: Optional[Dict] = None
    ) -> Dict:
        """
        Create a Razorpay order for payment.
        
        This is the ONLY function that creates orders. All payment flows use this.
        
        Args:
            amount: Amount in smallest currency unit (paise for INR, cents for USD)
                    Example: For ₹500, pass 50000 (500 * 100)
            currency: Currency code (default: 'INR')
            receipt: Unique receipt ID for your records (optional)
            notes: Additional metadata (optional)
                   Example: {'appointment_id': '123', 'patient_name': 'John'}
        
        Returns:
            Dict with order details:
            {
                'id': 'order_xxxxx',
                'amount': 50000,
                'currency': 'INR',
                'receipt': 'receipt#123',
                'status': 'created',
                'notes': {...}
            }
        
        Raises:
            razorpay.errors.BadRequestError: Invalid parameters
            razorpay.errors.ServerError: Razorpay server error
        """
        order_data = {
            'amount': amount,
            'currency': currency,
            'payment_capture': 1  # Auto-capture payment (1 = auto, 0 = manual)
        }
        
        if receipt:
            order_data['receipt'] = receipt
            
        if notes:
            order_data['notes'] = notes
        
        try:
            order = self.client.order.create(data=order_data)
            return order
        except razorpay.errors.BadRequestError as e:
            raise ValueError(f"Invalid order parameters: {str(e)}")
        except razorpay.errors.ServerError as e:
            raise Exception(f"Razorpay server error: {str(e)}")
    
    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """
        Verify payment signature to ensure payment authenticity.
        
        SECURITY CRITICAL: Always verify signatures on server-side.
        Never trust payment status from client-side alone.
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay callback
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Generate expected signature
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            expected_signature = hmac.new(
                self.key_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant-time comparison)
            return hmac.compare_digest(expected_signature, razorpay_signature)
            
        except Exception as e:
            print(f"Signature verification error: {str(e)}")
            return False
    
    def fetch_payment(self, payment_id: str) -> Dict:
        """
        Fetch payment details from Razorpay.
        
        Useful for:
        - Checking payment status
        - Getting payment method used
        - Retrieving transaction details
        
        Args:
            payment_id: Razorpay payment ID
        
        Returns:
            Dict with payment details
        """
        try:
            return self.client.payment.fetch(payment_id)
        except razorpay.errors.BadRequestError:
            raise ValueError(f"Payment not found: {payment_id}")
    
    def fetch_order(self, order_id: str) -> Dict:
        """
        Fetch order details from Razorpay.
        
        Args:
            order_id: Razorpay order ID
        
        Returns:
            Dict with order details
        """
        try:
            return self.client.order.fetch(order_id)
        except razorpay.errors.BadRequestError:
            raise ValueError(f"Order not found: {order_id}")
    
    def capture_payment(self, payment_id: str, amount: int, currency: str = 'INR') -> Dict:
        """
        Manually capture a payment (if auto-capture is disabled).
        
        Note: By default, we use auto-capture (payment_capture=1 in create_order).
        This is only needed if you set payment_capture=0.
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to capture (in smallest currency unit)
            currency: Currency code
        
        Returns:
            Dict with captured payment details
        """
        try:
            return self.client.payment.capture(payment_id, amount, {'currency': currency})
        except razorpay.errors.BadRequestError as e:
            raise ValueError(f"Payment capture failed: {str(e)}")
    
    def create_refund(self, payment_id: str, amount: Optional[int] = None) -> Dict:
        """
        Create a refund for a payment.
        
        Args:
            payment_id: Razorpay payment ID to refund
            amount: Amount to refund (optional, defaults to full refund)
        
        Returns:
            Dict with refund details
        """
        try:
            refund_data = {}
            if amount:
                refund_data['amount'] = amount
            
            return self.client.payment.refund(payment_id, refund_data)
        except razorpay.errors.BadRequestError as e:
            raise ValueError(f"Refund failed: {str(e)}")
    
    def get_key_id(self) -> str:
        """
        Get Razorpay Key ID for frontend integration.
        
        This is safe to expose to frontend (it's public).
        NEVER expose key_secret to frontend.
        
        Returns:
            Razorpay Key ID
        """
        return self.key_id


# Convenience function to initialize service from Flask config
def get_razorpay_service(app_config) -> RazorpayService:
    """
    Create RazorpayService instance from Flask app config.
    
    Usage in routes:
        service = get_razorpay_service(current_app.config)
    
    Args:
        app_config: Flask app.config object
    
    Returns:
        Configured RazorpayService instance
    """
    return RazorpayService(
        key_id=app_config.get('RAZORPAY_KEY_ID'),
        key_secret=app_config.get('RAZORPAY_KEY_SECRET')
    )
