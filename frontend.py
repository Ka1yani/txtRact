import streamlit as st
import requests

# API Endpoints Configurations
API_BASE_URL = "http://127.0.0.1:8000"

# Set Streamlit Page Config
st.set_page_config(page_title="txtRact - RAG Interface", page_icon="📄", layout="wide")

# Custom UI Styling (CSS) for a beautiful interface
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    /* Headers */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #A0AAB2;
        margin-bottom: 30px;
    }
    /* Custom Result Cards */
    .result-card {
        background-color: #1E2530;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        border-left: 6px solid #4ECDC4;
        transition: transform 0.2s ease-in-out;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .result-card:hover {
        transform: translateY(-5px);
    }
    .result-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #E2E8F0;
        margin-bottom: 12px;
    }
    .result-text {
        color: #CBD5E1;
        font-size: 1rem;
        line-height: 1.6;
        white-space: pre-wrap; /* Maintains newline formatting from extraction */
        word-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown('<div class="main-title">txtRact 📄</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI-Powered Intent Document Extraction & Retrieval Engine</div>', unsafe_allow_html=True)
st.divider()

# Layout Configuration
col1, col2 = st.columns([1, 1.8], gap="large")

# Left Column - Upload Document
with col1:
    st.subheader("📤 Upload Document")
    st.write("Upload a PDF to extract and index its contents page-by-page into the PostgreSQL GIN database.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], label_visibility="collapsed")
    
    if st.button("Upload & Index", type="primary", use_container_width=True):
        if uploaded_file is not None:
            with st.spinner("Uploading and starting background extraction..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(f"{API_BASE_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        task_id = data.get("task_id")
                        st.success(f"File uploaded! Task ID: `{task_id}`")
                        
                        # Background Status Tracker
                        status_placeholder = st.empty()
                        progress_bar = st.progress(0)
                        
                        is_completed = False
                        retry_count = 0
                        while not is_completed and retry_count < 60:  # Timeout after 2 minutes
                            import time
                            time.sleep(2)
                            
                            status_resp = requests.get(f"{API_BASE_URL}/status/{task_id}")
                            if status_resp.status_code == 200:
                                status_data = status_resp.json()
                                current_status = status_data.get("status")
                                
                                status_placeholder.info(f"Current Status: **{current_status.upper()}**")
                                
                                if current_status == "completed":
                                    is_completed = True
                                    status_placeholder.success("✅ Extraction and indexing complete!")
                                    progress_bar.progress(100)
                                    st.balloons()
                                elif "failed" in current_status:
                                    is_completed = True
                                    status_placeholder.error(f"❌ Error during background processing: {current_status}")
                                else:
                                    progress_bar.progress(50)  # Simple indeterminate progress
                            
                            retry_count += 1
                        
                        if not is_completed:
                            st.warning("The document is still processing in the background. You can check back later.")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Failed to upload')}")
                except Exception as e:
                    st.error(f"Backend Connection Error: Could not reach the FastAPI server. ({e})")
        else:
            st.warning("Please attach a PDF file first.")

# Right Column - Intelligent Search
with col2:
    st.subheader("🔍 Intelligent Search")
    st.write("Try contextual keyword queries **OR** try regex-powered intent lookups like *'page 7 of document.pdf'*")
    
    search_query = st.text_input("Search query", placeholder="e.g. Analysis revenue Q3 or Page 5...", label_visibility="collapsed")
    
    if st.button("Execute Search", type="primary", use_container_width=True):
        if search_query:
            with st.spinner("Searching Inverted Indexes..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/search", params={"q": search_query})
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.write("### Retrieval Results")
                        
                        # Show Intent Parsing Feature if matched
                        if "interpreted_intent" in data:
                            st.info(f"🎯 **Intent Parsed Successfully:** {data['interpreted_intent']}")
                        
                        results = data.get("results", [])
                        if not results:
                            st.warning("No matches found in the database. Ensure the document has been uploaded.")
                        else:
                            # Render Cards
                            for res in results:
                                with st.container():
                                    st.markdown(f"""
                                    <div class="result-card">
                                        <div class="result-header">📑 {res['document_name']} — (Page {res['page_number']})</div>
                                        <div class="result-text">{res['page_text']}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    with st.expander("Show Document Metadata Object"):
                                        st.json(res['metadata'])
                    else:
                        st.error("Error retrieving search results from the database.")
                except Exception as e:
                    st.error(f"Backend Connection Error: Could not reach the FastAPI server. ({e})")
        else:
            st.warning("Please enter a query to search.")
