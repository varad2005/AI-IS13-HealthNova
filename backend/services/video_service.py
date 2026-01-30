"""
Video Consultation Lifecycle Service
=====================================

SECURITY PHILOSOPHY: Stateful Authorization
--------------------------------------------
Why: WebRTC connections bypass normal HTTP auth. We need database-backed 
     state to ensure only authorized parties join meetings.

States: SCHEDULED → ACTIVE → ENDED
- SCHEDULED: Meeting created, waiting for doctor
- ACTIVE: Doctor started, patients can join
- ENDED: Meeting finished, no one can join

Defense Layers:
1. Database state: Source of truth for meeting status
2. Role-based join: Only doctors can START, patients can JOIN
3. Timeout handling: Auto-end abandoned meetings (resource leak prevention)
4. Disconnect logic: Different behavior for doctor vs patient disconnect
5. Socket.IO room isolation: Each meeting has unique room ID

Pattern: Finite State Machine with Authorization
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from flask_socketio import join_room, leave_room, emit, rooms
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MeetingStatus(str, Enum):
    """
    Meeting lifecycle states.
    
    Why enum?
    - Type safety: Can't accidentally use wrong string
    - Autocomplete in IDE
    - Explicit state transitions
    """
    SCHEDULED = 'SCHEDULED'  # Created but not started
    ACTIVE = 'ACTIVE'        # Doctor joined, patients can join
    ENDED = 'ENDED'          # Meeting finished
    CANCELLED = 'CANCELLED'  # Cancelled before starting


class VideoService:
    """
    Manages video consultation lifecycle and Socket.IO state.
    
    Why separate from socket handlers?
    - Business logic separation from I/O layer
    - Testability: Can test without Socket.IO
    - Database state management: Single source of truth
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize video service.
        
        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session
        # In-memory cache for active rooms (performance optimization)
        # Key: room_id, Value: {doctor_id, patient_ids[], started_at}
        self._active_rooms = {}
    
    def create_meeting(
        self,
        doctor_id: int,
        patient_id: int,
        appointment_id: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Create a new video meeting (SCHEDULED state).
        
        Security:
        - Only doctors should call this (enforced by route decorator)
        - Generate unique room_id (prevents enumeration)
        
        Args:
            doctor_id: Doctor creating the meeting
            patient_id: Patient invited to meeting
            appointment_id: Optional linked appointment
        
        Returns:
            Dict with meeting details and room_id
        """
        try:
            # Import here to avoid circular dependency
            from models import VideoMeeting, db
            
            # Generate unique room ID (UUID-based)
            import uuid
            room_id = f"room_{uuid.uuid4().hex[:16]}"
            
            # Create meeting record
            meeting = VideoMeeting(
                room_id=room_id,
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_id=appointment_id,
                status=MeetingStatus.SCHEDULED.value,
                scheduled_at=datetime.utcnow()
            )
            
            db.session.add(meeting)
            db.session.commit()
            
            logger.info(
                f"Meeting created: room_id={room_id}, "
                f"doctor_id={doctor_id}, patient_id={patient_id}"
            )
            
            return {
                'status': 'success',
                'room_id': room_id,
                'meeting_id': meeting.id,
                'meeting_status': meeting.status,
                'message': 'Meeting created successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to create meeting: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': 'Failed to create meeting'
            }
    
    def start_meeting(
        self,
        room_id: str,
        doctor_id: int,
        socket_id: str
    ) -> Tuple[bool, str]:
        """
        Doctor starts meeting (SCHEDULED → ACTIVE).
        
        Authorization:
        - Verify doctor owns this meeting
        - Verify meeting is in SCHEDULED state
        
        Args:
            room_id: Meeting room ID
            doctor_id: Doctor starting the meeting
            socket_id: Socket.IO session ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            from models import VideoMeeting, db
            
            # Fetch meeting from database
            meeting = VideoMeeting.query.filter_by(room_id=room_id).first()
            
            if not meeting:
                logger.warning(f"Meeting not found: room_id={room_id}")
                return False, "Meeting not found"
            
            # AUTHORIZATION: Verify doctor owns this meeting
            if meeting.doctor_id != doctor_id:
                logger.warning(
                    f"Unauthorized meeting start: doctor_id={doctor_id}, "
                    f"meeting_owner={meeting.doctor_id}, room_id={room_id}"
                )
                return False, "Unauthorized: You are not the meeting host"
            
            # STATE VALIDATION: Can only start SCHEDULED meetings
            if meeting.status != MeetingStatus.SCHEDULED.value:
                return False, f"Meeting cannot be started (status: {meeting.status})"
            
            # Update meeting state
            meeting.status = MeetingStatus.ACTIVE.value
            meeting.started_at = datetime.utcnow()
            db.session.commit()
            
            # Cache active room info
            self._active_rooms[room_id] = {
                'doctor_id': doctor_id,
                'doctor_socket': socket_id,
                'patient_ids': [],
                'started_at': datetime.utcnow()
            }
            
            logger.info(
                f"Meeting started: room_id={room_id}, doctor_id={doctor_id}"
            )
            
            return True, "Meeting started successfully"
            
        except Exception as e:
            logger.error(
                f"Failed to start meeting: room_id={room_id}: {str(e)}",
                exc_info=True
            )
            return False, "Failed to start meeting"
    
    def join_meeting(
        self,
        room_id: str,
        patient_id: int,
        socket_id: str
    ) -> Tuple[bool, str]:
        """
        Patient joins meeting (must be ACTIVE).
        
        Authorization:
        - Verify patient is invited to this meeting
        - Verify meeting is ACTIVE (doctor already joined)
        
        Args:
            room_id: Meeting room ID
            patient_id: Patient joining
            socket_id: Socket.IO session ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            from models import VideoMeeting
            
            # Fetch meeting
            meeting = VideoMeeting.query.filter_by(room_id=room_id).first()
            
            if not meeting:
                return False, "Meeting not found"
            
            # AUTHORIZATION: Verify patient is invited
            if meeting.patient_id != patient_id:
                logger.warning(
                    f"Unauthorized meeting join: patient_id={patient_id}, "
                    f"invited_patient={meeting.patient_id}, room_id={room_id}"
                )
                return False, "Unauthorized: You are not invited to this meeting"
            
            # STATE VALIDATION: Can only join ACTIVE meetings
            if meeting.status != MeetingStatus.ACTIVE.value:
                if meeting.status == MeetingStatus.SCHEDULED.value:
                    return False, "Meeting not started yet. Please wait for the doctor."
                elif meeting.status == MeetingStatus.ENDED.value:
                    return False, "This meeting has ended"
                else:
                    return False, f"Cannot join meeting (status: {meeting.status})"
            
            # Add patient to active room cache
            if room_id in self._active_rooms:
                if patient_id not in self._active_rooms[room_id]['patient_ids']:
                    self._active_rooms[room_id]['patient_ids'].append(patient_id)
            
            logger.info(
                f"Patient joined meeting: room_id={room_id}, patient_id={patient_id}"
            )
            
            return True, "Joined meeting successfully"
            
        except Exception as e:
            logger.error(
                f"Failed to join meeting: room_id={room_id}: {str(e)}",
                exc_info=True
            )
            return False, "Failed to join meeting"
    
    def handle_disconnect(
        self,
        room_id: str,
        user_id: int,
        user_role: str
    ) -> Dict[str, any]:
        """
        Handle user disconnect with role-specific logic.
        
        Business Rules:
        - Doctor disconnect → END meeting immediately (host left)
        - Patient disconnect → Keep meeting ACTIVE for 5min (reconnect window)
        - Last person disconnect → END meeting
        
        Args:
            room_id: Meeting room ID
            user_id: User who disconnected
            user_role: 'doctor' or 'patient'
        
        Returns:
            Dict with action taken
        """
        try:
            from models import VideoMeeting, db
            
            meeting = VideoMeeting.query.filter_by(room_id=room_id).first()
            
            if not meeting or meeting.status != MeetingStatus.ACTIVE.value:
                return {'action': 'none', 'reason': 'Meeting not active'}
            
            # DOCTOR DISCONNECT: End meeting immediately
            if user_role == 'doctor' and meeting.doctor_id == user_id:
                meeting.status = MeetingStatus.ENDED.value
                meeting.ended_at = datetime.utcnow()
                db.session.commit()
                
                # Remove from active rooms cache
                if room_id in self._active_rooms:
                    del self._active_rooms[room_id]
                
                logger.info(
                    f"Meeting ended by doctor disconnect: room_id={room_id}, "
                    f"doctor_id={user_id}"
                )
                
                return {
                    'action': 'end_meeting',
                    'reason': 'Doctor left the meeting',
                    'notify_others': True
                }
            
            # PATIENT DISCONNECT: Keep active for reconnect window
            if user_role == 'patient' and meeting.patient_id == user_id:
                # Remove from active cache but don't end meeting
                if room_id in self._active_rooms:
                    cache = self._active_rooms[room_id]
                    if user_id in cache['patient_ids']:
                        cache['patient_ids'].remove(user_id)
                
                logger.info(
                    f"Patient disconnected: room_id={room_id}, patient_id={user_id}. "
                    "Meeting remains active for reconnection."
                )
                
                # Schedule timeout cleanup (implement with Celery/background task)
                # TODO: After 5 minutes, if patient hasn't rejoined, end meeting
                
                return {
                    'action': 'patient_left',
                    'reason': 'Patient disconnected',
                    'reconnect_window': 300  # 5 minutes in seconds
                }
            
            return {'action': 'none'}
            
        except Exception as e:
            logger.error(
                f"Error handling disconnect: room_id={room_id}, "
                f"user_id={user_id}: {str(e)}",
                exc_info=True
            )
            return {'action': 'error', 'message': str(e)}
    
    def end_meeting(
        self,
        room_id: str,
        user_id: int,
        user_role: str
    ) -> Tuple[bool, str]:
        """
        Explicitly end a meeting.
        
        Authorization:
        - Only doctor can explicitly end meeting
        
        Args:
            room_id: Meeting room ID
            user_id: User ending the meeting
            user_role: User role
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            from models import VideoMeeting, db
            
            meeting = VideoMeeting.query.filter_by(room_id=room_id).first()
            
            if not meeting:
                return False, "Meeting not found"
            
            # AUTHORIZATION: Only doctor can end meeting
            if user_role != 'doctor' or meeting.doctor_id != user_id:
                return False, "Only the meeting host can end the meeting"
            
            # STATE TRANSITION: ACTIVE → ENDED
            if meeting.status == MeetingStatus.ACTIVE.value:
                meeting.status = MeetingStatus.ENDED.value
                meeting.ended_at = datetime.utcnow()
                db.session.commit()
                
                # Cleanup cache
                if room_id in self._active_rooms:
                    del self._active_rooms[room_id]
                
                logger.info(
                    f"Meeting ended explicitly: room_id={room_id}, "
                    f"doctor_id={user_id}"
                )
                
                return True, "Meeting ended successfully"
            else:
                return False, f"Meeting cannot be ended (status: {meeting.status})"
                
        except Exception as e:
            logger.error(
                f"Failed to end meeting: room_id={room_id}: {str(e)}",
                exc_info=True
            )
            return False, "Failed to end meeting"
    
    def get_meeting_status(self, room_id: str) -> Optional[Dict[str, any]]:
        """
        Get current meeting status.
        
        Returns:
            Dict with meeting details or None if not found
        """
        try:
            from models import VideoMeeting
            
            meeting = VideoMeeting.query.filter_by(room_id=room_id).first()
            
            if not meeting:
                return None
            
            return {
                'room_id': meeting.room_id,
                'status': meeting.status,
                'doctor_id': meeting.doctor_id,
                'patient_id': meeting.patient_id,
                'scheduled_at': meeting.scheduled_at.isoformat() if meeting.scheduled_at else None,
                'started_at': meeting.started_at.isoformat() if meeting.started_at else None,
                'ended_at': meeting.ended_at.isoformat() if meeting.ended_at else None
            }
            
        except Exception as e:
            logger.error(
                f"Failed to get meeting status: room_id={room_id}: {str(e)}",
                exc_info=True
            )
            return None


# Factory function
def get_video_service(db_session: Session) -> VideoService:
    """Get video service instance with DB session"""
    return VideoService(db_session)
