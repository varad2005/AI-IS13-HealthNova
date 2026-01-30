from flask import Blueprint, request, jsonify, session
from models import db, LabTest, TestReport, Visit
from auth.decorators import role_required
from datetime import datetime

lab_bp = Blueprint('lab', __name__)


@lab_bp.route('/dashboard', methods=['GET'])
@role_required('lab')
def dashboard():
    """Get lab dashboard overview"""
    lab_id = session.get('user_id')
    
    # Get requested tests (not yet assigned)
    requested_tests = LabTest.query.filter_by(status='requested').all()
    
    # Get tests assigned to this lab
    assigned_tests = LabTest.query.filter_by(lab_id=lab_id).all()
    
    # Get pending tests (approved/scheduled but not completed)
    pending_tests = LabTest.query.filter_by(
        lab_id=lab_id
    ).filter(
        LabTest.status.in_(['approved', 'scheduled'])
    ).order_by(LabTest.scheduled_time).all()
    
    return jsonify({
        'status': 'success',
        'data': {
            'requested_tests': [test.to_dict() for test in requested_tests],
            'pending_tests': [test.to_dict() for test in pending_tests],
            'total_assigned': len(assigned_tests)
        }
    }), 200


@lab_bp.route('/tests', methods=['GET'])
@role_required('lab')
def get_tests():
    """Get all lab tests (optionally filtered by status)"""
    lab_id = session.get('user_id')
    
    status = request.args.get('status')
    
    # Build query
    if status == 'requested':
        # Show all requested tests (not yet assigned)
        query = LabTest.query.filter_by(status='requested')
    else:
        # Show tests assigned to this lab
        query = LabTest.query.filter_by(lab_id=lab_id)
        
        if status:
            query = query.filter_by(status=status)
    
    tests = query.order_by(LabTest.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': {
            'tests': [test.to_dict(include_reports=True) for test in tests],
            'total': len(tests)
        }
    }), 200


@lab_bp.route('/tests/<int:test_id>', methods=['GET'])
@role_required('lab')
def get_test(test_id):
    """Get specific lab test details"""
    lab_id = session.get('user_id')
    
    # Get test
    test = LabTest.query.get(test_id)
    
    if not test:
        return jsonify({
            'status': 'error',
            'message': 'Lab test not found'
        }), 404
    
    # Check access: either unassigned (requested) or assigned to this lab
    if test.status != 'requested' and test.lab_id != lab_id:
        return jsonify({
            'status': 'error',
            'message': 'Access denied'
        }), 403
    
    # Get patient info through visit
    visit = Visit.query.get(test.visit_id)
    test_data = test.to_dict(include_reports=True)
    
    if visit:
        patient_profile = visit.patient_profile
        test_data['patient'] = {
            'name': patient_profile.user.full_name,
            'age': patient_profile.age,
            'gender': patient_profile.gender,
            'phone': patient_profile.user.phone_number
        }
        test_data['symptoms'] = visit.symptoms
    
    return jsonify({
        'status': 'success',
        'data': test_data
    }), 200


@lab_bp.route('/tests/<int:test_id>/approve', methods=['POST'])
@role_required('lab')
def approve_test(test_id):
    """Approve and assign test to this lab"""
    lab_id = session.get('user_id')
    
    # Get test
    test = LabTest.query.get(test_id)
    
    if not test:
        return jsonify({
            'status': 'error',
            'message': 'Lab test not found'
        }), 404
    
    # Only requested tests can be approved
    if test.status != 'requested':
        return jsonify({
            'status': 'error',
            'message': f'Cannot approve test with status: {test.status}'
        }), 400
    
    # Assign to this lab and approve
    test.lab_id = lab_id
    test.status = 'approved'
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Test approved and assigned',
            'data': test.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to approve test: {str(e)}'
        }), 500


@lab_bp.route('/tests/<int:test_id>/reject', methods=['POST'])
@role_required('lab')
def reject_test(test_id):
    """Reject a lab test request"""
    lab_id = session.get('user_id')
    
    # Get test
    test = LabTest.query.get(test_id)
    
    if not test:
        return jsonify({
            'status': 'error',
            'message': 'Lab test not found'
        }), 404
    
    # Only requested tests can be rejected
    if test.status != 'requested':
        return jsonify({
            'status': 'error',
            'message': f'Cannot reject test with status: {test.status}'
        }), 400
    
    data = request.get_json() or {}
    
    # Update status
    test.status = 'rejected'
    test.remarks = data.get('remarks', 'Rejected by lab')
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Test rejected',
            'data': test.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to reject test: {str(e)}'
        }), 500


@lab_bp.route('/tests/<int:test_id>/schedule', methods=['POST'])
@role_required('lab')
def schedule_test(test_id):
    """Schedule a time slot for the test"""
    lab_id = session.get('user_id')
    
    # Get test and verify access
    test = LabTest.query.filter_by(id=test_id, lab_id=lab_id).first()
    
    if not test:
        return jsonify({
            'status': 'error',
            'message': 'Lab test not found or access denied'
        }), 404
    
    # Only approved tests can be scheduled
    if test.status != 'approved':
        return jsonify({
            'status': 'error',
            'message': f'Cannot schedule test with status: {test.status}'
        }), 400
    
    data = request.get_json()
    
    # Validate scheduled time
    if not data.get('scheduled_time'):
        return jsonify({
            'status': 'error',
            'message': 'Scheduled time is required'
        }), 400
    
    try:
        # Parse scheduled time
        scheduled_time = datetime.fromisoformat(data['scheduled_time'].replace('Z', '+00:00'))
        
        # Update test
        test.scheduled_time = scheduled_time
        test.status = 'scheduled'
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Test scheduled successfully',
            'data': test.to_dict()
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'Invalid date format: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to schedule test: {str(e)}'
        }), 500


@lab_bp.route('/tests/<int:test_id>/update', methods=['PUT'])
@role_required('lab')
def update_test_result(test_id):
    """Update test results and status"""
    lab_id = session.get('user_id')
    
    # Get test and verify access
    test = LabTest.query.filter_by(id=test_id, lab_id=lab_id).first()
    
    if not test:
        return jsonify({
            'status': 'error',
            'message': 'Lab test not found or access denied'
        }), 404
    
    data = request.get_json()
    
    # Update result and remarks
    if 'result' in data:
        test.result = data['result']
    
    if 'remarks' in data:
        test.remarks = data['remarks']
    
    # Update status if provided
    if 'status' in data:
        allowed_statuses = ['scheduled', 'completed']
        if data['status'] in allowed_statuses:
            test.status = data['status']
        else:
            return jsonify({
                'status': 'error',
                'message': f'Invalid status. Allowed: {", ".join(allowed_statuses)}'
            }), 400
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Test updated successfully',
            'data': test.to_dict(include_reports=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to update test: {str(e)}'
        }), 500


@lab_bp.route('/tests/<int:test_id>/reports', methods=['POST'])
@role_required('lab')
def upload_report(test_id):
    """Upload report metadata (minimal file handling)"""
    lab_id = session.get('user_id')
    
    # Get test and verify access
    test = LabTest.query.filter_by(id=test_id, lab_id=lab_id).first()
    
    if not test:
        return jsonify({
            'status': 'error',
            'message': 'Lab test not found or access denied'
        }), 404
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['file_name', 'file_path']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400
    
    try:
        # Create report metadata
        report = TestReport(
            lab_test_id=test_id,
            file_name=data['file_name'],
            file_path=data['file_path'],
            file_type=data.get('file_type'),
            file_size=data.get('file_size')
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Report uploaded successfully',
            'data': report.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to upload report: {str(e)}'
        }), 500


@lab_bp.route('/tests/<int:test_id>/complete', methods=['POST'])
@role_required('lab')
def complete_test(test_id):
    """Mark test as completed"""
    lab_id = session.get('user_id')
    
    # Get test and verify access
    test = LabTest.query.filter_by(id=test_id, lab_id=lab_id).first()
    
    if not test:
        return jsonify({
            'status': 'error',
            'message': 'Lab test not found or access denied'
        }), 404
    
    # Mark as completed
    test.status = 'completed'
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Test marked as completed',
            'data': test.to_dict(include_reports=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to complete test: {str(e)}'
        }), 500
