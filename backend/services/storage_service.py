"""
Hardened File Upload & Storage Service
=======================================

SECURITY PHILOSOPHY: "Never Trust User Files"
----------------------------------------------
Why: File uploads are a top attack vector (malware, path traversal, RCE)

Defense Layers:
1. MIME type validation (whitelist only)
2. Extension validation (double-check, users can rename)
3. Filename sanitization (prevent path traversal: ../../../etc/passwd)
4. Size limits (prevent DoS via disk exhaustion)
5. Content scanning (virus/malware detection)
6. Isolated storage (uploaded files never in web root)
7. Randomized filenames (prevent enumeration attacks)

Pattern: Defense in Depth
- Fail at the earliest possible layer
- Multiple independent checks (belt AND suspenders)
"""

import os
import uuid
import mimetypes
import logging
from typing import Optional, Tuple, Dict
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from datetime import datetime

logger = logging.getLogger(__name__)

# MIME type whitelist - ONLY these are allowed
# Why whitelist vs blacklist? Blacklists can be bypassed; whitelists cannot.
ALLOWED_MIMETYPES = {
    'application/pdf',      # Lab reports
    'image/jpeg',           # Medical photos
    'image/png',            # Screenshots, medical images
    'image/jpg'             # Alternative JPEG MIME
}

# Extension whitelist (double-check MIME validation)
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}

# File size limits (in bytes)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MIN_FILE_SIZE = 100  # 100 bytes (prevent empty file uploads)


class StorageService:
    """
    Hardened file upload handler for medical documents.
    
    Why separate service?
    - Reusability: Lab reports, prescriptions, medical images
    - Testability: Can mock for unit tests
    - Security: Centralized validation = fewer mistakes
    """
    
    def __init__(self, upload_folder: str):
        """
        Initialize storage service.
        
        Args:
            upload_folder: Base directory for uploads (must exist and be writable)
        """
        self.upload_folder = Path(upload_folder)
        
        # Ensure upload directory exists and is writable
        if not self.upload_folder.exists():
            logger.info(f"Creating upload directory: {self.upload_folder}")
            self.upload_folder.mkdir(parents=True, exist_ok=True)
        
        # Security check: Ensure upload folder is NOT in web root
        # TODO: Add explicit check that upload_folder is not under static/
    
    def save_file(
        self,
        file: FileStorage,
        user_id: int,
        file_category: str = 'general'
    ) -> Dict[str, any]:
        """
        Securely save uploaded file with validation.
        
        Args:
            file: Werkzeug FileStorage object from request.files
            user_id: User ID (for folder isolation and audit trail)
            file_category: Subdirectory (e.g., 'reports', 'prescriptions')
        
        Returns:
            Dict with keys: status, file_path, original_name, size, message
            
        Security Flow:
        1. Validate file is present
        2. Check file size (before reading into memory)
        3. Validate MIME type
        4. Sanitize filename
        5. Generate unique random filename
        6. Save to user-specific subdirectory
        7. (Future) Run virus scan
        8. Return secure file path
        """
        try:
            # VALIDATION 1: Check file is present
            if not file or file.filename == '':
                logger.warning(f"Empty file upload attempt by user_id={user_id}")
                return {
                    'status': 'error',
                    'message': 'No file provided'
                }
            
            original_filename = file.filename
            
            # VALIDATION 2: Check file size BEFORE reading
            # Why: Reading large files into memory = DoS attack vector
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()  # Get position (file size)
            file.seek(0)  # Reset to beginning
            
            if file_size > MAX_FILE_SIZE:
                logger.warning(
                    f"File too large: user_id={user_id}, "
                    f"size={file_size}, max={MAX_FILE_SIZE}"
                )
                return {
                    'status': 'error',
                    'message': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
                }
            
            if file_size < MIN_FILE_SIZE:
                logger.warning(
                    f"Suspicious empty file: user_id={user_id}, size={file_size}"
                )
                return {
                    'status': 'error',
                    'message': 'File appears to be empty or corrupted'
                }
            
            # VALIDATION 3: MIME type validation (primary defense)
            # Why: Extensions can be faked, MIME is harder (but still fakeable)
            mime_type = file.content_type
            if mime_type not in ALLOWED_MIMETYPES:
                logger.warning(
                    f"Blocked file upload: user_id={user_id}, "
                    f"mime_type={mime_type}, filename={original_filename}"
                )
                return {
                    'status': 'error',
                    'message': f'File type not allowed. Allowed types: PDF, JPEG, PNG',
                    'rejected_type': mime_type
                }
            
            # VALIDATION 4: Extension validation (secondary defense)
            # Why: Defense in depth - validate by extension too
            file_ext = Path(original_filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                logger.warning(
                    f"Blocked file by extension: user_id={user_id}, "
                    f"ext={file_ext}, filename={original_filename}"
                )
                return {
                    'status': 'error',
                    'message': f'File extension not allowed: {file_ext}'
                }
            
            # SANITIZATION: Prevent path traversal attacks
            # secure_filename removes: ../, ../../, null bytes, special chars
            safe_original_name = secure_filename(original_filename)
            
            if not safe_original_name:
                # secure_filename can return empty string for malicious names
                logger.error(
                    f"Filename sanitization failed: user_id={user_id}, "
                    f"original={original_filename}"
                )
                return {
                    'status': 'error',
                    'message': 'Invalid filename'
                }
            
            # RANDOMIZATION: Generate unique filename to prevent enumeration
            # Pattern: {uuid}_{timestamp}{extension}
            # Why: Prevents attackers from guessing file paths
            unique_id = uuid.uuid4().hex[:16]  # 16-char random hex
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{unique_id}_{timestamp}{file_ext}"
            
            # ISOLATION: Create user-specific subdirectory
            # Why: Prevent user A from accessing user B's files
            user_folder = self.upload_folder / f"user_{user_id}" / file_category
            user_folder.mkdir(parents=True, exist_ok=True)
            
            # Full file path
            file_path = user_folder / new_filename
            
            # VIRUS SCAN: Check file safety
            # Why: Medical files could contain malware targeting staff systems
            if not self._virus_scan(file, user_id):
                return {
                    'status': 'error',
                    'message': 'File failed security scan. Please contact support.',
                    'code': 'SECURITY_SCAN_FAILED'
                }
            
            # SAVE FILE: Write to disk
            file.save(str(file_path))
            
            # Verify file was written successfully
            if not file_path.exists() or file_path.stat().st_size != file_size:
                logger.error(
                    f"File save verification failed: user_id={user_id}, "
                    f"path={file_path}"
                )
                return {
                    'status': 'error',
                    'message': 'File upload failed. Please try again.'
                }
            
            logger.info(
                f"File uploaded successfully: user_id={user_id}, "
                f"size={file_size}, path={file_path.relative_to(self.upload_folder)}"
            )
            
            return {
                'status': 'success',
                'file_path': str(file_path.relative_to(self.upload_folder)),
                'absolute_path': str(file_path),
                'original_name': original_filename,
                'size': file_size,
                'mime_type': mime_type,
                'uploaded_at': datetime.utcnow().isoformat(),
                'message': 'File uploaded successfully'
            }
            
        except Exception as e:
            logger.error(
                f"File upload exception: user_id={user_id}, "
                f"filename={file.filename if file else 'None'}: {str(e)}",
                exc_info=True
            )
            return {
                'status': 'error',
                'message': 'File upload failed due to server error'
            }
    
    def _virus_scan(self, file: FileStorage, user_id: int) -> bool:
        """
        Placeholder for virus/malware scanning.
        
        Production Implementation:
        - Option 1: ClamAV (open-source antivirus)
        - Option 2: Cloud API (VirusTotal, MetaDefender)
        - Option 3: AWS S3 with Macie for automated scanning
        
        Why placeholder?
        - Antivirus integration requires system dependencies
        - Different deployment environments have different solutions
        - This enforces the integration point
        
        Returns:
            bool: True if file is safe, False if suspicious
        """
        # TODO: Integrate actual virus scanning
        # Example with ClamAV:
        # import pyclamd
        # cd = pyclamd.ClamdUnixSocket()
        # scan_result = cd.scan_stream(file.read())
        # file.seek(0)  # Reset after reading
        # return scan_result is None  # None = clean
        
        logger.debug(
            f"Virus scan placeholder called for user_id={user_id}. "
            "TODO: Implement actual scanning."
        )
        return True  # TEMP: Allow all files (REPLACE IN PRODUCTION)
    
    def delete_file(self, file_path: str, user_id: int) -> Dict[str, any]:
        """
        Safely delete a file with authorization check.
        
        Args:
            file_path: Relative path to file (from upload_folder)
            user_id: User ID (must own the file)
        
        Security:
        - Verify file belongs to user (path contains user_id)
        - Prevent path traversal
        - Log deletion for audit
        """
        try:
            # Resolve full path
            full_path = self.upload_folder / file_path
            
            # AUTHORIZATION: Ensure file belongs to this user
            # Check if path contains user's folder
            if f"user_{user_id}" not in str(full_path):
                logger.warning(
                    f"Unauthorized delete attempt: user_id={user_id}, "
                    f"path={file_path}"
                )
                return {
                    'status': 'error',
                    'message': 'Unauthorized: You can only delete your own files'
                }
            
            # SAFETY: Prevent path traversal
            # Ensure resolved path is still within upload_folder
            if not str(full_path.resolve()).startswith(str(self.upload_folder.resolve())):
                logger.error(
                    f"Path traversal attempt detected: user_id={user_id}, "
                    f"path={file_path}"
                )
                return {
                    'status': 'error',
                    'message': 'Invalid file path'
                }
            
            # Delete file if it exists
            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted: user_id={user_id}, path={file_path}")
                return {
                    'status': 'success',
                    'message': 'File deleted successfully'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'File not found'
                }
                
        except Exception as e:
            logger.error(
                f"File deletion error: user_id={user_id}, path={file_path}: {str(e)}",
                exc_info=True
            )
            return {
                'status': 'error',
                'message': 'Failed to delete file'
            }


# Factory function for dependency injection
def get_storage_service(upload_folder: str) -> StorageService:
    """
    Get storage service instance.
    
    Why factory function?
    - Easier to mock in tests
    - Can add caching/pooling later
    - Explicit configuration injection
    """
    return StorageService(upload_folder)
