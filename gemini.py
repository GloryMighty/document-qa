import os
import google.generativeai as genai
from typing import Optional, List, Dict
from dotenv import load_dotenv
import tempfile
from google.cloud import storage
import base64
import logging
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GeminiAPI')

# Load environment variables (for local development)
load_dotenv()

# Configure the Gemini API using Streamlit secrets or environment variables
genai.configure(api_key=st.secrets.get("gemini_api_key", os.getenv('GEMINI_API_KEY')))

class GeminiAPI:
    """Utility class for interacting with Gemini API"""
    
    def __init__(self):
        """Initialize the Gemini model with flash configuration and GCS client"""
        try:
            # Configure Gemini API
            gemini_key = st.secrets.get("gemini_api_key") or os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                raise ValueError("Gemini API key not found")
            genai.configure(api_key=gemini_key)
            
            logger.info("Initializing GeminiAPI with model: gemini-2.0-flash-exp")
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Initialize Google Cloud Storage client
            # if 'gcp_service_account' in st.secrets:
            #     import json
            #     credentials_dict = st.secrets["gcp_service_account"]
            #     if isinstance(credentials_dict, str):
            #         credentials_dict = json.loads(credentials_dict)
            #     self.storage_client = storage.Client.from_service_account_info(credentials_dict)
            # else:
            # Use default credentials from credentials.json
            self.storage_client = storage.Client()
            
            self.bucket_name = os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET') or st.secrets.get("gcp_bucket")
            if not self.bucket_name:
                raise ValueError("GCP bucket name not found")
                
            self.base_path = 'Codes/Testing - Phase 1/MD Community Solar IX'
            logger.info(f"Connected to GCS bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Error initializing GeminiAPI: {str(e)}")
            raise
        
    def list_available_files(self) -> List[Dict[str, str]]:
        """
        List all available files in the specified GCS directory
        
        Returns:
            List[Dict[str, str]]: List of files with their names and full paths
        """
        logger.info(f"Listing files from path: {self.base_path}")
        bucket = self.storage_client.bucket(self.bucket_name)
        files = bucket.list_blobs(prefix=self.base_path)
        
        file_list = [
            {
                'name': blob.name.split('/')[-1],
                'full_path': blob.name,
                'size': f"{blob.size / 1024:.1f} KB"
            }
            for blob in files
            if not blob.name.endswith('/')  # Skip directories
        ]
        logger.info(f"Found {len(file_list)} files")
        return file_list
        
    def read_gcs_file(self, file_path: str) -> bytes:
        """
        Read a file from Google Cloud Storage
        
        Args:
            file_path (str): Full path to the file in GCS
            
        Returns:
            bytes: File content
        """
        logger.info(f"Reading file: {file_path}")
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(file_path)
            content = blob.download_as_bytes()
            logger.info(f"Successfully read {len(content)} bytes")
            return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise
    
    def process_files_query(self, query: str, selected_files: List[str]) -> str:
        """
        Process a query about selected files using Gemini's capabilities
        
        Args:
            query (str): The user's query
            selected_files (List[str]): List of selected file paths
            
        Returns:
            str: Generated response about the files' content
        """
        logger.info(f"Processing query for {len(selected_files)} files")
        try:
            contents = []
            
            # Add each file as content with user role
            for file_path in selected_files:
                logger.debug(f"Processing file: {file_path}")
                file_content = self.read_gcs_file(file_path)
                file_type = self._get_file_type(file_path)
                
                # Format according to Gemini API requirements
                file_part = {
                    'role': 'user',
                    'parts': [{
                        'inline_data': {
                            'mime_type': file_type,
                            'data': base64.b64encode(file_content).decode('utf-8')
                        }
                    }]
                }
                contents.append(file_part)
            
            # Add the query as a text part with user role
            contents.append({
                'role': 'user',
                'parts': [{
                    'text': query
                }]
            })
            
            logger.info("Generating response from Gemini API")
            # Generate content using the model
            response = self.model.generate_content(
                contents=contents,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 4000,
                }
            )
            
            logger.info("Successfully generated response")
            return response.text
                
        except Exception as e:
            logger.error(f"Error processing files: {str(e)}")
            return f"Error processing files: {str(e)}"
    
    def _get_file_type(self, file_path: str) -> str:
        """
        Get the MIME type for a file based on its extension
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: MIME type
        """
        extension = file_path.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        mime_type = mime_types.get(extension, 'application/octet-stream')
        logger.debug(f"File type for {file_path}: {mime_type}")
        return mime_type
    
    def generate_response(self, prompt: str, temperature: float = 0.1) -> str:
        """
        Generate a response using the Gemini model
        
        Args:
            prompt (str): The input prompt
            temperature (float): Controls randomness in the response (0.0 to 1.0)
            
        Returns:
            str: Generated response text
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': temperature,
                    'max_output_tokens': 4000,
                }
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def process_pdf(self, pdf_content: bytes, query: str) -> str:
        """
        Process a PDF file and generate a response to a query using Gemini's built-in PDF capabilities
        
        Args:
            pdf_content (bytes): The PDF file content
            query (str): The user's query about the PDF
            
        Returns:
            str: Generated response about the PDF content
        """
        try:
            # Create a temporary file to store the PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf.flush()
                
                # Create the file data part for the model
                file_data = {
                    'fileData': {
                        'mimeType': 'application/pdf',
                        'data': pdf_content,
                    }
                }
                
                # Generate content using the model
                response = self.model.generate_content(
                    contents=[file_data, query],
                    generation_config={
                        'temperature': 0.1,
                        'max_output_tokens': 4000,
                    }
                )
                
                return response.text
                
        except Exception as e:
            return f"Error processing PDF: {str(e)}"
        finally:
            # Clean up the temporary file
            if 'temp_pdf' in locals():
                os.unlink(temp_pdf.name)
    
    def start_chat(self, history: Optional[List[dict]] = None) -> genai.ChatSession:
        """
        Start a new chat session with optional history
        
        Args:
            history (List[dict], optional): Previous chat history
            
        Returns:
            ChatSession: A new chat session
        """
        history = history or []
        return self.model.start_chat(history=history)
    
    def process_file_query(self, file_content: str, query: str) -> str:
        """
        Process a query about a specific file content
        
        Args:
            file_content (str): The content of the file to analyze
            query (str): The user's query about the file
            
        Returns:
            str: Generated response about the file
        """
        prompt = f"""Content: {file_content}\n\nQuery: {query}"""
        return self.generate_response(prompt) 