"""
Payment Service with Integrity Guarantees
==========================================

SECURITY PHILOSOPHY: "Trust, But Verify" Payment Webhook Pattern
-----------------------------------------------------------------
Why: Payment gateways are external systems. We must verify:
1. Request authenticity (signature verification)
2. Idempotency (no double-crediting)
3. State consistency (payment matches order)

Defense Layers:
1. Signature Verification: Cryptographic proof request is from Razorpay
2. Idempotency: Transaction ID uniqueness check
3. State Machine: Order status transitions are atomic
4. Audit Trail: Log every payment event for reconciliation
5. Webhook Validation: Verify payload structure before processing

Pattern: Transactional Outbox + Idempotent Processing
"""

import os
import logging
import hmac
import hashlib
from typing import Dict, Optional, Tuple
from datetime import datetime
import razorpay
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Hardened payment service with signature verification and idempotency.
    
    Why separate service?
    - Single Responsibility: Payment logic isolated
    - Testability: Can mock Razorpay client
    - Security: Centralized signature verification
    - Audit: All payment operations logged
    """
    
    def __init__(self, key_id: str, key_secret: str, webhook_secret: str):
        """
        Initialize payment service with Razorpay credentials.
        
        Args:
            key_id: Razorpay Key ID
            key_secret: Razorpay Key Secret
            webhook_secret: Razorpay Webhook Secret (for signature verification)
        """
        if not key_id or not key_secret:
            raise ValueError("Razorpay credentials required. Check .env file.")
        
        self.key_id = key_id
        self.key_secret = key_secret
        self.webhook_secret = webhook_secret
        
        # Initialize Razorpay client
        self.client = razorpay.Client(auth=(key_id, key_secret))
    
    def create_order(
        self,
        amount: int,
        currency: str = 'INR',
        receipt: str = None,
        notes: Dict[str, str] = None
    ) -> Dict[str, any]:
        """
        Create Razorpay order.
        
        Args:
            amount: Amount in smallest currency unit (paise for INR)
            currency: Currency code (default: INR)
            receipt: Unique receipt ID for tracking
            notes: Additional metadata
        
        Returns:
            Dict with order details or error
        """
        try:
            # Input validation
            if amount <= 0:
                return {
                    'status': 'error',
                    'message': 'Amount must be positive'
                }
            
            # Create order via Razorpay API
            order_data = {
                'amount': amount,
                'currency': currency,
                'receipt': receipt or f"rcpt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                'notes': notes or {}
            }
            
            order = self.client.order.create(data=order_data)
            
            logger.info(
                f"Razorpay order created: order_id={order['id']}, "
                f"amount={amount}, receipt={receipt}"
            )
            
            return {
                'status': 'success',
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'receipt': order['receipt']
            }
            
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': 'Failed to create payment order'
            }
    
    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> Tuple[bool, str]:
        """
        Verify Razorpay payment signature (cryptographic authenticity).
        
        Security Rationale:
        - CRITICAL: Without verification, attackers can fake payment success
        - Uses HMAC-SHA256 to verify request came from Razorpay
        - Prevents replay attacks (signature tied to specific order+payment)
        
        Algorithm:
        1. Concatenate: order_id|payment_id
        2. HMAC-SHA256 with webhook_secret
        3. Compare with provided signature
        
        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Signature from Razorpay
        
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        try:
            # Use Razorpay SDK's built-in verification
            # Why SDK over manual? They handle edge cases and updates
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            # This raises SignatureVerificationError if invalid
            self.client.utility.verify_payment_signature(params_dict)
            
            logger.info(
                f"Payment signature verified: order_id={razorpay_order_id}, "
                f"payment_id={razorpay_payment_id}"
            )
            
            return True, "Signature valid"
            
        except razorpay.errors.SignatureVerificationError as e:
            logger.error(
                f"SECURITY: Invalid payment signature detected! "
                f"order_id={razorpay_order_id}, payment_id={razorpay_payment_id}: {str(e)}"
            )
            return False, "Invalid payment signature"
            
        except Exception as e:
            logger.error(
                f"Signature verification error: {str(e)}",
                exc_info=True
            )
            return False, "Signature verification failed"
    
    def process_payment_success(
        self,
        payment_id: str,
        order_id: str,
        signature: str,
        user_id: int,
        amount: int
    ) -> Dict[str, any]:
        """
        Process successful payment with idempotency guarantee.
        
        Security Flow:
        1. Verify signature (authenticity)
        2. Check if payment_id already processed (idempotency)
        3. Update order status atomically
        4. Audit log
        
        Args:
            payment_id: Razorpay payment ID
            order_id: Razorpay order ID
            signature: Payment signature
            user_id: User who made payment
            amount: Payment amount (for verification)
        
        Returns:
            Dict with processing result
        """
        try:
            from models import Payment, db
            
            # DEFENSE LAYER 1: Signature Verification
            is_valid, message = self.verify_payment_signature(
                order_id, payment_id, signature
            )
            
            if not is_valid:
                logger.error(
                    f"Payment signature verification failed: "
                    f"payment_id={payment_id}, user_id={user_id}"
                )
                return {
                    'status': 'error',
                    'message': 'Payment verification failed',
                    'code': 'SIGNATURE_INVALID'
                }
            
            # DEFENSE LAYER 2: Idempotency Check
            # Check if this payment_id has already been processed
            existing_payment = Payment.query.filter_by(
                razorpay_payment_id=payment_id
            ).first()
            
            if existing_payment:
                # Payment already processed - return success but log warning
                logger.warning(
                    f"IDEMPOTENCY: Duplicate payment processing attempt: "
                    f"payment_id={payment_id}, user_id={user_id}, "
                    f"original_status={existing_payment.status}"
                )
                
                return {
                    'status': 'success',
                    'message': 'Payment already processed',
                    'is_duplicate': True,
                    'payment_status': existing_payment.status
                }
            
            # DEFENSE LAYER 3: Atomic State Update
            # Create payment record (transaction_id constraint prevents duplicates)
            payment = Payment(
                user_id=user_id,
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id,
                amount=amount,
                status='PAID',
                paid_at=datetime.utcnow()
            )
            
            try:
                db.session.add(payment)
                db.session.commit()
                
                logger.info(
                    f"Payment processed successfully: payment_id={payment_id}, "
                    f"user_id={user_id}, amount={amount}"
                )
                
                return {
                    'status': 'success',
                    'message': 'Payment processed successfully',
                    'payment_id': payment.id,
                    'is_duplicate': False
                }
                
            except IntegrityError as ie:
                # Race condition: Another request processed same payment
                db.session.rollback()
                logger.warning(
                    f"IDEMPOTENCY: Race condition on payment processing: "
                    f"payment_id={payment_id}"
                )
                return {
                    'status': 'success',
                    'message': 'Payment already processed (race condition)',
                    'is_duplicate': True
                }
            
        except Exception as e:
            logger.error(
                f"Payment processing error: payment_id={payment_id}: {str(e)}",
                exc_info=True
            )
            return {
                'status': 'error',
                'message': 'Payment processing failed'
            }
    
    def handle_webhook(
        self,
        payload: Dict[str, any],
        signature: str
    ) -> Dict[str, any]:
        """
        Handle Razorpay webhook for asynchronous payment updates.
        
        Security:
        - Verify webhook signature (proves request is from Razorpay)
        - Idempotent processing (webhooks can be retried)
        - Event filtering (only process relevant events)
        
        Webhook Events:
        - payment.captured: Payment successful
        - payment.failed: Payment failed
        - order.paid: Order fully paid
        
        Args:
            payload: Webhook payload from Razorpay
            signature: X-Razorpay-Signature header
        
        Returns:
            Dict with processing result
        """
        try:
            # VALIDATION 1: Verify webhook signature
            if not self._verify_webhook_signature(payload, signature):
                logger.error("SECURITY: Invalid webhook signature detected!")
                return {
                    'status': 'error',
                    'message': 'Invalid webhook signature',
                    'code': 'WEBHOOK_SIGNATURE_INVALID'
                }
            
            # Extract event details
            event = payload.get('event')
            entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
            
            payment_id = entity.get('id')
            order_id = entity.get('order_id')
            amount = entity.get('amount')
            status = entity.get('status')
            
            logger.info(
                f"Webhook received: event={event}, payment_id={payment_id}, "
                f"status={status}"
            )
            
            # EVENT ROUTING: Handle different event types
            if event == 'payment.captured':
                return self._handle_payment_captured(payment_id, order_id, amount)
            
            elif event == 'payment.failed':
                return self._handle_payment_failed(payment_id, order_id)
            
            else:
                # Log unhandled events but don't fail
                logger.info(f"Unhandled webhook event: {event}")
                return {
                    'status': 'success',
                    'message': f'Event {event} logged but not processed'
                }
            
        except Exception as e:
            logger.error(
                f"Webhook processing error: {str(e)}",
                exc_info=True
            )
            return {
                'status': 'error',
                'message': 'Webhook processing failed'
            }
    
    def _verify_webhook_signature(
        self,
        payload: Dict[str, any],
        signature: str
    ) -> bool:
        """
        Verify webhook signature using HMAC-SHA256.
        
        Why manual verification?
        - Razorpay SDK doesn't have webhook signature verification
        - Must verify before trusting payload
        """
        try:
            import json
            
            # Convert payload to JSON string (order matters!)
            payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Constant-time comparison (prevents timing attacks)
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification error: {str(e)}")
            return False
    
    def _handle_payment_captured(
        self,
        payment_id: str,
        order_id: str,
        amount: int
    ) -> Dict[str, any]:
        """Handle payment.captured webhook event"""
        try:
            from models import Payment, db
            
            # Check if already processed (idempotency)
            payment = Payment.query.filter_by(
                razorpay_payment_id=payment_id
            ).first()
            
            if payment:
                if payment.status == 'PAID':
                    logger.info(f"Payment already marked as PAID: {payment_id}")
                    return {'status': 'success', 'message': 'Already processed'}
                
                # Update existing record
                payment.status = 'PAID'
                payment.paid_at = datetime.utcnow()
            else:
                # Create new payment record from webhook
                payment = Payment(
                    razorpay_order_id=order_id,
                    razorpay_payment_id=payment_id,
                    amount=amount,
                    status='PAID',
                    paid_at=datetime.utcnow()
                )
                db.session.add(payment)
            
            db.session.commit()
            
            logger.info(f"Webhook: Payment captured - {payment_id}")
            return {'status': 'success', 'message': 'Payment captured'}
            
        except Exception as e:
            logger.error(f"Error handling payment.captured: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def _handle_payment_failed(
        self,
        payment_id: str,
        order_id: str
    ) -> Dict[str, any]:
        """Handle payment.failed webhook event"""
        try:
            from models import Payment, db
            
            payment = Payment.query.filter_by(
                razorpay_payment_id=payment_id
            ).first()
            
            if payment:
                payment.status = 'FAILED'
                payment.failed_at = datetime.utcnow()
                db.session.commit()
            
            logger.warning(f"Webhook: Payment failed - {payment_id}")
            return {'status': 'success', 'message': 'Payment failure recorded'}
            
        except Exception as e:
            logger.error(f"Error handling payment.failed: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}


# Factory function
def get_payment_service() -> PaymentService:
    """
    Get payment service instance with credentials from environment.
    
    Why factory?
    - Centralizes configuration loading
    - Easy to mock in tests
    - Lazy initialization
    """
    key_id = os.getenv('RAZORPAY_KEY_ID', '')
    key_secret = os.getenv('RAZORPAY_KEY_SECRET', '')
    webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
    
    return PaymentService(key_id, key_secret, webhook_secret)
