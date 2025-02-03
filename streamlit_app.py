import streamlit as st
from google.cloud.storage import storage
from google.oauth2 import service_account
from api_delete import CloudStorageDelete
from api_upload import CloudStorageUpload   
from gemini import GeminiAPI
import os
import json

# Initialize page config and title
st.set_page_config(page_title="📄 Document QA", layout="wide")
st.title("📄 Document question answering")
st.write(
    "Upload documents and ask questions about them using Google's Gemini AI. "
    "You'll need to provide API credentials to use this app."
)

# Configure Google Cloud credentials
def init_google_cloud():
    try:
        if 'GOOGLE_APPLICATION_CREDENTIALS_JSON' in st.secrets:
            credentials_dict = json.loads(st.secrets['GOOGLE_APPLICATION_CREDENTIALS_JSON'])
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            return credentials
        else:
            st.error("Google Cloud credentials not found in secrets")
            return None
    except Exception as e:
        st.error(f"Error initializing Google Cloud credentials: {e}")
        return None

# Setup configuration
credentials = init_google_cloud()
if not credentials:
    st.warning("Please configure Google Cloud credentials in Streamlit secrets")
else:
    storage_client = storage.Client(credentials=credentials)

# Initialize session state
if 'gemini_api' not in st.session_state:
    st.session_state.gemini_api = None
if 'uploader' not in st.session_state:
    st.session_state.uploader = None
if 'deleter' not in st.session_state:
    st.session_state.deleter = None

# Setup sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    gemini_api_key = st.text_input("Gemini API Key", type="password")
    gcs_bucket = st.text_input("GCS Bucket Name")
    base_path = st.text_input("Base Storage Path", value="documents")

    if gemini_api_key and gcs_bucket:
        try:
            st.session_state.gemini_api = GeminiAPI()
            st.session_state.uploader = CloudStorageUpload(gcs_bucket, base_path)
            st.session_state.deleter = CloudStorageDelete(gcs_bucket, base_path)
            st.success("APIs configured successfully!")
        except Exception as e:
            st.error(f"Error configuring APIs: {str(e)}")

# Main content area
if not st.session_state.gemini_api:
    st.info("Please configure your API credentials in the sidebar to continue.", icon="🔑")
else:
    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["Ask Questions", "Upload Documents", "Manage Files"])

    # Tab 1: Ask Questions
    with tab1:
        st.header("Ask Questions About Documents")
        
        # Get available files
        available_files = st.session_state.gemini_api.list_available_files()
        selected_files = st.multiselect(
            "Select documents to query",
            options=[f["full_path"] for f in available_files],
            format_func=lambda x: x.split("/")[-1]
        )

        question = st.text_area(
            "Ask your question",
            placeholder="What are the key points in these documents?",
            disabled=not selected_files
        )

        if selected_files and question and st.button("Get Answer"):
            with st.spinner("Processing your question..."):
                response = st.session_state.gemini_api.process_files_query(
                    query=question,
                    selected_files=selected_files
                )
                st.write(response)

    # Tab 2: Upload Documents
    with tab2:
        st.header("Upload New Documents")
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            accept_multiple_files=True,
            type=["pdf", "txt", "csv", "xlsx", "doc", "docx"]
        )

        if uploaded_files and st.button("Upload Selected Files"):
            for file in uploaded_files:
                with st.spinner(f"Uploading {file.name}..."):
                    success, message = st.session_state.uploader.upload_file(file)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

    # Tab 3: Manage Files
    with tab3:
        st.header("Manage Existing Documents")
        
        if available_files:
            files_to_delete = st.multiselect(
                "Select files to delete",
                options=[f["full_path"] for f in available_files],
                format_func=lambda x: f"{x.split('/')[-1]} ({next(f['size'] for f in available_files if f['full_path'] == x)})"
            )

            if files_to_delete and st.button("Delete Selected Files"):
                with st.spinner("Deleting files..."):
                    results = st.session_state.deleter.delete_multiple_files(files_to_delete)
                    for file_path, success, message in results:
                        if success:
                            st.success(f"Deleted: {file_path.split('/')[-1]}")
                        else:
                            st.error(f"Error deleting {file_path.split('/')[-1]}: {message}")
        else:
            st.info("No files available to manage.")

# Footer
st.markdown("---")
st.caption("Powered by Google Gemini AI")
