"""
Payments Blueprint
==================

This blueprint handles all payment-related operations.
Routes here are simple - they delegate complex logic to RazorpayService.

WHY THIS PREVENTS BREAKING THE APP:
-----------------------------------
1. Blueprint isolation: Payment routes don't touch other modules
2. JSON-only responses: No template rendering = no HTML conflicts
3. Service abstraction: Routes call service, service calls Razorpay
4. Error boundaries: All exceptions caught and returned as JSON
"""

from flask import Blueprint

# Create payments blueprint
payments_bp = Blueprint('payments', __name__)

# Import routes after blueprint creation to avoid circular imports
from . import routes
