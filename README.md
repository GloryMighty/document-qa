# 📄 Document Question Answering App

A Streamlit application that uses Google's Gemini AI to answer questions about documents.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://document-question-answering-template.streamlit.app/)

## Setup

### Local Development

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   Create `.streamlit/secrets.toml` with:
   ```toml
   GOOGLE_APPLICATION_CREDENTIALS_JSON = """YOUR_SERVICE_ACCOUNT_JSON"""
   gemini_api_key = "YOUR_GEMINI_API_KEY"
   gcp_bucket = "YOUR_GCS_BUCKET_NAME"
   ```

3. Run the app:
   ```bash
   streamlit run streamlit_app.py
   ```

### Streamlit Cloud Deployment

1. Add the following secrets in Streamlit Cloud dashboard:
   - `GOOGLE_APPLICATION_CREDENTIALS_JSON`: Your service account JSON
   - `gemini_api_key`: Your Gemini API key
   - `gcp_bucket`: Your GCS bucket name

2. Deploy directly from GitHub repository.
