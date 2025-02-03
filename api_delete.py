import os
from google.cloud import storage
from typing import Tuple, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CloudStorageDelete')

class CloudStorageDelete:
    """Class to handle file deletions from Google Cloud Storage"""
    
    def __init__(self, bucket_name: str, base_path: str):
        """
        Initialize the deleter with bucket and path configuration
        
        Args:
            bucket_name (str): Name of the GCS bucket
            base_path (str): Base path in the bucket for file storage
        """
        self.storage_client = storage.Client()
        self.bucket_name = bucket_name
        self.base_path = base_path
        logger.info(f"Initialized CloudStorageDelete for bucket: {bucket_name}")
    
    def delete_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Delete a single file from Google Cloud Storage
        
        Args:
            file_path (str): Full path to the file in the bucket
            
        Returns:
            Tuple[bool, str]: (Success status, Message/Error description)
        """
        try:
            # Get bucket and blob
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(file_path)
            
            # Check if file exists
            if not blob.exists():
                msg = f"File {file_path} does not exist"
                logger.warning(msg)
                return False, msg
            
            # Delete the file
            blob.delete()
            
            logger.info(f"Successfully deleted file: {file_path}")
            return True, f"File {file_path} deleted successfully"
            
        except Exception as e:
            error_msg = f"Error deleting file {file_path}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def delete_multiple_files(self, file_paths: List[str]) -> List[Tuple[str, bool, str]]:
        """
        Delete multiple files from Google Cloud Storage
        
        Args:
            file_paths (List[str]): List of file paths to delete
            
        Returns:
            List[Tuple[str, bool, str]]: List of (file_path, success_status, message)
        """
        results = []
        for file_path in file_paths:
            success, message = self.delete_file(file_path)
            results.append((file_path, success, message))
        
        # Log summary
        successful = len([r for r in results if r[1]])
        logger.info(f"Deleted {successful} out of {len(file_paths)} files")
        
        return results
    
    def delete_by_prefix(self, prefix: str) -> Tuple[bool, str]:
        """
        Delete all files with a specific prefix
        
        Args:
            prefix (str): Prefix to match files against
            
        Returns:
            Tuple[bool, str]: (Success status, Message/Error description)
        """
        try:
            # Get bucket
            bucket = self.storage_client.bucket(self.bucket_name)
            
            # List all blobs with prefix
            blobs = bucket.list_blobs(prefix=os.path.join(self.base_path, prefix))
            
            # Delete all matching blobs
            count = 0
            for blob in blobs:
                blob.delete()
                count += 1
            
            msg = f"Successfully deleted {count} files with prefix {prefix}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            error_msg = f"Error deleting files with prefix {prefix}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
