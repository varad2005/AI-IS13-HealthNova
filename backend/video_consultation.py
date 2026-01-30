"""
Video Consultation Module - WebRTC Signaling Server
====================================================

This module handles WebRTC signaling for video consultations between patients and doctors.

WebRTC Flow:
1. Both patient and doctor join the same room (using room_id)
2. Peer A sends an "offer" (SDP) → Server forwards to Peer B
3. Peer B sends an "answer" (SDP) → Server forwards to Peer A
4. Both peers exchange ICE candidates for connection establishment
5. Direct peer-to-peer video/audio stream begins

The server ONLY handles signaling (offer, answer, ICE).
Actual media streams go directly peer-to-peer (not through server).
"""

from flask_socketio import emit, join_room, leave_room
from flask import request

# Store active rooms and their participants
active_rooms = {}

def register_socketio_events(socketio):
    """
    Register all SocketIO event handlers for video consultation
    
    Events:
    - join_room: User joins a consultation room
    - offer: WebRTC offer (SDP)
    - answer: WebRTC answer (SDP)
    - ice_candidate: ICE candidate for peer connection
    - leave_room: User leaves the consultation
    """
    
    @socketio.on('connect')
    def handle_connect():
        """Called when a client connects to the WebSocket"""
        print(f'Client connected: {request.sid}')
        emit('connected', {'message': 'Connected to signaling server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Called when a client disconnects"""
        print(f'Client disconnected: {request.sid}')
        
        # Remove user from all rooms
        for room_id, participants in list(active_rooms.items()):
            if request.sid in participants:
                participants.remove(request.sid)
                # Notify other participants
                emit('user_left', {'user_id': request.sid}, room=room_id, skip_sid=request.sid)
                
                # Clean up empty rooms
                if len(participants) == 0:
                    del active_rooms[room_id]
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """
        User joins a consultation room
        
        Args:
            data: {
                'room_id': string - Unique room identifier,
                'user_type': string - 'patient' or 'doctor',
                'user_name': string - User's display name
            }
        """
        room_id = data.get('room_id')
        user_type = data.get('user_type', 'unknown')
        user_name = data.get('user_name', 'Anonymous')
        
        if not room_id:
            emit('error', {'message': 'Room ID is required'})
            return
        
        # Add room if it doesn't exist
        if room_id not in active_rooms:
            active_rooms[room_id] = []
        
        # Check if room is full (max 2 participants)
        if len(active_rooms[room_id]) >= 2:
            emit('error', {'message': 'Room is full'})
            return
        
        # Join the room
        join_room(room_id)
        active_rooms[room_id].append(request.sid)
        
        print(f'{user_name} ({user_type}) joined room {room_id}')
        
        # Notify the user they joined successfully
        emit('room_joined', {
            'room_id': room_id,
            'participants': len(active_rooms[room_id])
        })
        
        # Notify other participants in the room
        emit('user_joined', {
            'user_id': request.sid,
            'user_type': user_type,
            'user_name': user_name,
            'participants': len(active_rooms[room_id])
        }, room=room_id, skip_sid=request.sid)
    
    @socketio.on('offer')
    def handle_offer(data):
        """
        Forward WebRTC offer from one peer to another
        
        WebRTC Offer contains:
        - SDP (Session Description Protocol): describes media capabilities,
          codecs, network info
        
        Args:
            data: {
                'room_id': string,
                'offer': object - WebRTC SDP offer
            }
        """
        room_id = data.get('room_id')
        offer = data.get('offer')
        
        if not room_id or not offer:
            emit('error', {'message': 'Room ID and offer are required'})
            return
        
        print(f'Forwarding offer in room {room_id}')
        
        # Forward offer to all other participants in the room
        emit('offer', {
            'offer': offer,
            'sender_id': request.sid
        }, room=room_id, skip_sid=request.sid)
    
    @socketio.on('answer')
    def handle_answer(data):
        """
        Forward WebRTC answer from answering peer to offering peer
        
        WebRTC Answer:
        - Response to the offer
        - Contains answerer's SDP
        
        Args:
            data: {
                'room_id': string,
                'answer': object - WebRTC SDP answer
            }
        """
        room_id = data.get('room_id')
        answer = data.get('answer')
        
        if not room_id or not answer:
            emit('error', {'message': 'Room ID and answer are required'})
            return
        
        print(f'Forwarding answer in room {room_id}')
        
        # Forward answer to all other participants
        emit('answer', {
            'answer': answer,
            'sender_id': request.sid
        }, room=room_id, skip_sid=request.sid)
    
    @socketio.on('ice_candidate')
    def handle_ice_candidate(data):
        """
        Forward ICE candidate from one peer to another
        
        ICE (Interactive Connectivity Establishment):
        - Discovers best network path between peers
        - Handles NAT traversal
        - Each peer generates multiple ICE candidates
        
        Args:
            data: {
                'room_id': string,
                'candidate': object - ICE candidate info
            }
        """
        room_id = data.get('room_id')
        candidate = data.get('candidate')
        
        if not room_id or not candidate:
            return
        
        # Forward ICE candidate to all other participants
        emit('ice_candidate', {
            'candidate': candidate,
            'sender_id': request.sid
        }, room=room_id, skip_sid=request.sid)
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """
        User leaves a consultation room
        
        Args:
            data: {
                'room_id': string
            }
        """
        room_id = data.get('room_id')
        
        if not room_id:
            return
        
        # Remove user from room
        if room_id in active_rooms and request.sid in active_rooms[room_id]:
            active_rooms[room_id].remove(request.sid)
            leave_room(room_id)
            
            print(f'User left room {room_id}')
            
            # Notify other participants
            emit('user_left', {
                'user_id': request.sid
            }, room=room_id)
            
            # Clean up empty rooms
            if len(active_rooms[room_id]) == 0:
                del active_rooms[room_id]
                print(f'Room {room_id} deleted (empty)')
    
    @socketio.on('get_room_info')
    def handle_get_room_info(data):
        """
        Get information about a room
        
        Args:
            data: {
                'room_id': string
            }
        """
        room_id = data.get('room_id')
        
        if room_id in active_rooms:
            emit('room_info', {
                'room_id': room_id,
                'participants': len(active_rooms[room_id]),
                'is_full': len(active_rooms[room_id]) >= 2
            })
        else:
            emit('room_info', {
                'room_id': room_id,
                'participants': 0,
                'is_full': False
            })
