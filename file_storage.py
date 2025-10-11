"""
File storage utility for handling uploads to Cloudinary
Supports both images and PDFs with fallback to local storage
"""

import os
import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename

# Initialize Cloudinary (will be configured from environment variables)
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def is_cloudinary_configured():
    """Check if Cloudinary credentials are configured"""
    return all([
        os.getenv('CLOUDINARY_CLOUD_NAME'),
        os.getenv('CLOUDINARY_API_KEY'),
        os.getenv('CLOUDINARY_API_SECRET')
    ])

def upload_image(file, folder='question_images'):
    """
    Upload an image to Cloudinary
    Returns: (success: bool, url_or_error: str)
    """
    if not is_cloudinary_configured():
        return False, "Cloudinary not configured"
    
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type='image',
            allowed_formats=['png', 'jpg', 'jpeg', 'gif', 'webp']
        )
        
        # Return the secure URL
        return True, result['secure_url']
    except Exception as e:
        return False, str(e)

def upload_pdf(file, folder='documents'):
    """
    Upload a PDF to Cloudinary
    Returns: (success: bool, url_or_error: str)
    """
    if not is_cloudinary_configured():
        return False, "Cloudinary not configured"
    
    try:
        # Upload to Cloudinary as raw file
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type='raw',
            allowed_formats=['pdf']
        )
        
        # Return the secure URL
        return True, result['secure_url']
    except Exception as e:
        return False, str(e)

def delete_file(public_id, resource_type='image'):
    """
    Delete a file from Cloudinary
    Returns: (success: bool, message: str)
    """
    if not is_cloudinary_configured():
        return False, "Cloudinary not configured"
    
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result.get('result') == 'ok', result.get('result', 'Unknown error')
    except Exception as e:
        return False, str(e)

def get_public_id_from_url(url):
    """
    Extract public_id from Cloudinary URL
    Example: https://res.cloudinary.com/demo/image/upload/v1234/folder/file.jpg
    Returns: folder/file
    """
    try:
        # Split URL and get the part after 'upload/'
        parts = url.split('/upload/')
        if len(parts) < 2:
            return None
        
        # Get everything after version number
        path_parts = parts[1].split('/')
        # Remove version (v1234567890)
        if path_parts[0].startswith('v'):
            path_parts = path_parts[1:]
        
        # Join remaining parts and remove extension
        public_id = '/'.join(path_parts)
        public_id = public_id.rsplit('.', 1)[0]
        
        return public_id
    except:
        return None

# Fallback: Local storage functions (for development)
def save_local_file(file, upload_folder, subfolder):
    """
    Save file locally (fallback for development)
    Returns: (success: bool, path_or_error: str)
    """
    try:
        import uuid
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Create directory if it doesn't exist
        full_path = os.path.join(upload_folder, subfolder)
        os.makedirs(full_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(full_path, unique_filename)
        file.save(file_path)
        
        # Return relative path
        return True, os.path.join(subfolder, unique_filename)
    except Exception as e:
        return False, str(e)
