import os
from google.cloud import storage
from typing import Optional, Tuple
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CloudStorageUpload')

class CloudStorageUpload:
    """Class to handle file uploads to Google Cloud Storage"""
    
    def __init__(self, bucket_name: str, base_path: str):
        """
        Initialize the uploader with bucket and path configuration
        
        Args:
            bucket_name (str): Name of the GCS bucket
            base_path (str): Base path in the bucket for file storage
        """
        self.storage_client = storage.Client()
        self.bucket_name = bucket_name
        self.base_path = base_path
        logger.info(f"Initialized CloudStorageUpload for bucket: {bucket_name}")
        
    def upload_file(self, file_obj, custom_filename: Optional[str] = None) -> Tuple[bool, str]:
        """
        Upload a file to Google Cloud Storage
        
        Args:
            file_obj: File object from Streamlit uploader
            custom_filename (Optional[str]): Custom filename to use instead of original
            
        Returns:
            Tuple[bool, str]: (Success status, Message/Error description)
        """
        try:
            # Get bucket
            bucket = self.storage_client.bucket(self.bucket_name)
            
            # Generate filename if not provided
            if not custom_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                custom_filename = f"{timestamp}_{file_obj.name}"
            
            # Create full path
            destination_blob_path = os.path.join(self.base_path, custom_filename)
            
            # Create blob and upload
            blob = bucket.blob(destination_blob_path)
            
            # Upload the file
            blob.upload_from_file(file_obj, content_type=self._get_content_type(file_obj.name))
            
            logger.info(f"Successfully uploaded file to {destination_blob_path}")
            return True, f"File uploaded successfully to {destination_blob_path}"
            
        except Exception as e:
            error_msg = f"Error uploading file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _get_content_type(self, filename: str) -> str:
        """
        Get the MIME type based on file extension
        
        Args:
            filename (str): Name of the file
            
        Returns:
            str: MIME type
        """
        extension = filename.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        return mime_types.get(extension, 'application/octet-stream')
