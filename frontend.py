import streamlit as st
import requests
import html
import re

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
    .highlight {
        background-color: #FCD34D;
        color: #1E293B;
        font-weight: 700;
        padding: 0px 4px;
        border-radius: 4px;
    }
    .meta-badge {
        display: inline-block;
        background-color: #334155;
        color: #94A3B8;
        font-size: 0.85rem;
        padding: 4px 10px;
        border-radius: 20px;
        margin-right: 8px;
        margin-bottom: 12px;
        border: 1px solid #475569;
    }
    .box-rep {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

def render_search_interface():
    # Application Header
    st.markdown('<div class="main-title">txtRact 📄</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">AI-Powered Intent Document Extraction & Retrieval Engine</div>', unsafe_allow_html=True)
    st.divider()

    # Layout Configuration
    col1, col2 = st.columns([1, 1.8], gap="large")

    # Left Column - Upload Document
    with col1:
        st.subheader("📤 Upload Omni-Document")
        st.write("Upload omni-format files (`.pdf`, `.docx`, `.txt`, `.csv`, `.xlsx`, `.png`, `.jpeg`) to extract and index their contents seamlessly into the PostgreSQL GIN database via the Strategy Factory.")
        
        uploaded_file = st.file_uploader("Choose an Omni-Format file", type=["pdf", "docx", "txt", "csv", "xlsx", "png", "jpeg", "jpg"], label_visibility="collapsed")
        
        if st.button("Upload & Index", type="primary", use_container_width=True):
            if uploaded_file is not None:
                with st.spinner("Uploading and starting background omni-extraction..."):
                    try:
                        # Ensure a generic fallback octet-stream representation if needed
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
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
                                    # 1. Escape HTML so that < and > characters in the PDF don't break the Markdown div rendering
                                    safe_text = html.escape(res['page_text'])
                                    
                                    # 2. Highlight Keywords if it's a general search
                                    terms = search_query.split()
                                    for term in terms:
                                        if len(term) > 3 and term.lower() not in ['page', 'document', 'from', 'the', 'and', 'with']:
                                            pattern = re.compile(re.escape(term), re.IGNORECASE)
                                            safe_text = pattern.sub(lambda m: f'<span class="highlight">{m.group(0)}</span>', safe_text)
                                            
                                    # 3. Format badges
                                    author = html.escape(res.get("author") or "Unknown Author")
                                    c_date = html.escape(res.get("creation_date") or "Unknown Date")
                                    author_badge = f'<span class="meta-badge">👤 {author}</span>'
                                    date_badge = f'<span class="meta-badge">📅 {c_date}</span>'

                                    with st.container():
                                        st.markdown(f"""
                                        <div class="result-card">
                                            <div class="result-header">📑 {res['document_name']} — (Page {res['page_number']})</div>
                                            <div>{author_badge} {date_badge}</div>
                                            <div class="result-text">{safe_text}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        with st.expander("Show Raw DB Metadata Object"):
                                            st.json(res['metadata'])
                        else:
                            st.error("Error retrieving search results from the database.")
                    except Exception as e:
                        st.error(f"Backend Connection Error: Could not reach the FastAPI server. ({e})")
            else:
                st.warning("Please enter a query to search.")

def render_pipeline_visualizer():
    st.markdown('<div class="main-title">Pipeline Visualizer ⚙️</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Interactive Educational Breakdown of the Ingestion Architecture</div>', unsafe_allow_html=True)
    st.divider()
    
    st.header("Step 1: Asynchronous Dispatch")
    st.info("When a file is uploaded, the FastAPI backend immediately generates a `task_id` and hands off the heavy lifting to a background thread. This ensures the main server is never blocked.")
    st.code('background_tasks.add_task(process_document_bg, task_id, temp_file_path, file.filename)', language="python")
    
    st.divider()
    st.header("Step 2: Interactive PyMuPDF Block Sandbox")
    st.write("A PDF is not a text file; it is a visual canvas. Words are painted at specific `(x, y)` bounding box coordinates.")
    st.info("Upload a real PDF below. The Sandbox will pick a random page and visualize exactly how PyMuPDF rips its raw blocks vs our post-sorting algorithm.")
    
    sandbox_file = st.file_uploader("Test PyMuPDF Parsing", type=["pdf"])
    
    if st.button("Analyze Bounding Boxes", type="secondary"):
        if sandbox_file is not None:
            with st.spinner("Parsing PyMuPDF Arrays..."):
                try:
                    files = {"file": (sandbox_file.name, sandbox_file.getvalue(), "application/pdf")}
                    resp = requests.post(f"{API_BASE_URL}/analyze_blocks", files=files)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(f"Successfully analyzed **Page {data['page_number']}** of {data['total_pages']} pages.")
                        
                        col1, col2 = st.columns(2, gap="large")
                        with col1:
                            st.markdown('### 1. Raw Extraction')
                            st.write('PyMuPDF reads the raw byte-stream and returns unsorted visual blocks:')
                            for i, b in enumerate(data.get("raw_blocks", [])[:15]): # Cap at 15 for UI sanity
                                color = "#3f1a20" if i % 2 == 0 else "#3b2816"
                                border = "#ef4444" if i % 2 == 0 else "#f59e0b"
                                st.markdown(f'<div class="box-rep" style="background-color: {color}; border-left: 4px solid {border};">[x0: {b["x0"]:>5}, y0: {b["y0"]:>5}] {html.escape(b["text"])}</div>', unsafe_allow_html=True)
                            if len(data.get("raw_blocks", [])) > 15:
                                st.markdown(f"*(...and {len(data['raw_blocks']) - 15} more blocks)*")
                            
                        with col2:
                            st.markdown('### 2. Spatial Algorithm')
                            st.write("We sort the array vertically (y) then horizontally (x) to simulate human reading:")
                            st.code("blocks.sort(key=lambda b: (b[1], b[0]))", language="python")
                            for b in data.get("sorted_blocks", [])[:15]:
                                st.markdown(f'<div class="box-rep" style="background-color: #1a3f29; border-left: 4px solid #10b981;">[x0: {b["x0"]:>5}, y0: {b["y0"]:>5}] {html.escape(b["text"])}</div>', unsafe_allow_html=True)
                            if len(data.get("sorted_blocks", [])) > 15:
                                st.markdown(f"*(...and {len(data['sorted_blocks']) - 15} more blocks)*")
                                
                    else:
                        st.error(f"Sandbox Error: {resp.json().get('detail')}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")
        else:
            st.warning("Upload a PDF to sandbox test.")

    st.divider()
    st.header("Step 3: Database & Hardware-Level Indexing")
    st.write("The database splits the text into pages and saves the relational metadata. Once the string hits PostgreSQL, the C++ Engine instantly auto-strips formatting and calculates a `TSVECTOR` hash.")
    st.code("search_vector = Column(TSVECTOR, Computed(\"to_tsvector('english', page_content)\", persisted=True))", language="python")
    st.info("The document has now transitioned from an unstructured, visual PDF file into a deterministic, lightning-fast SQL object readable by the frontend.")

import pandas as pd

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def render_database_catalog():
    st.markdown('<div class="main-title">Database Catalog 🗄️</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">View all locally indexed documents inside the system</div>', unsafe_allow_html=True)
    st.divider()
    
    with st.spinner("Fetching document catalog from database..."):
        try:
            resp = requests.get(f"{API_BASE_URL}/documents/all")
            if resp.status_code == 200:
                docs = resp.json().get("documents", [])
                if not docs:
                    st.info("No documents have been uploaded or processed yet.")
                else:
                    df_data = []
                    for d in docs:
                        fname = d.get('filename', 'Unknown')
                        ext = fname.split('.')[-1].upper() if '.' in fname else 'Unknown'
                        df_data.append({
                            "File Name": fname,
                            "File Type": ext,
                            "Date Uploaded": d.get('creation_date', 'Unknown'),
                            "Size": format_size(d.get('file_size_bytes', 0)),
                            "Total Pages": d.get('total_pages', 0)
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.error("Failed to fetch documents from database.")
        except Exception as e:
            st.error(f"Connection Error: {e}")

# Sidebar Navigation Module
st.sidebar.title("txtRact Navigation")
page = st.sidebar.radio("Go to:", ["Search Application", "Database Catalog", "Pipeline Visualizer"])

st.sidebar.divider()
st.sidebar.markdown(
    """<div style="color: #64748B; font-size: 0.85rem;">
    <b>Tech Stack:</b><br/>
    - FastAPI (Async)<br/>
    - PostgreSQL + GIN<br/>
    - SQLAlchemy 2.0 ORM<br/>
    - PyMuPDF Extraction<br/>
    - Streamlit User Interface
    </div>""", unsafe_allow_html=True
)

if page == "Search Application":
    render_search_interface()
elif page == "Database Catalog":
    render_database_catalog()
else:
    render_pipeline_visualizer()
