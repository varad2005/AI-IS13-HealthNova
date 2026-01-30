"""
Video Consultation Module

This module provides doctor-controlled video consultation management.

SECURITY ARCHITECTURE:
- Only doctors can start meetings (update meeting_status to 'live')
- Only patients can join when meeting_status == 'live'
- appointment_id is used as the WebRTC room identifier
- No manual meeting IDs or links are shared with patients
- All operations verify user role and appointment ownership

MEETING LIFECYCLE:
1. Doctor clicks "Start Consultation" → meeting_status becomes 'live'
2. Patient's "Join Consultation" button automatically enables
3. Both join the same WebRTC room using appointment_id
4. Doctor can end meeting → meeting_status becomes 'ended'
"""

from flask import Blueprint

video_bp = Blueprint('video', __name__, url_prefix='/video')

from . import routes
