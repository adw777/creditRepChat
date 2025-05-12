import streamlit as st
import requests
import os
from typing import List

# FastAPI endpoint URLs
API_BASE_URL = "https://sweeping-moth-probably.ngrok-free.app"
PARSE_URL = f"{API_BASE_URL}/parse"
CHAT_URL = f"{API_BASE_URL}/chat"

# Page configuration
st.set_page_config(
    page_title="creditRepChat",
    page_icon="📄",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'processed_file_path' not in st.session_state:
        st.session_state.processed_file_path = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_document' not in st.session_state:
        st.session_state.current_document = None

def process_document(uploaded_file):
    """Send document to FastAPI endpoint for processing"""
    if uploaded_file is not None:
        files = {"file": uploaded_file}
        try:
            with st.spinner("Processing document..."):
                response = requests.post(PARSE_URL, files=files)
                response.raise_for_status()
                result = response.json()
                
                # Extract the file path from the result
                file_path = result["result"].split("Results saved to: ")[-1].split("\n")[0]
                return file_path
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")
            return None

def send_chat_message(query: str, document_path: str) -> str:
    """Send chat message to FastAPI endpoint"""
    try:
        response = requests.post(
            CHAT_URL,
            json={"query": query, "document_path": document_path}
        )
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return None

def reset_conversation():
    """Reset the conversation and clear the document"""
    st.session_state.processed_file_path = None
    st.session_state.messages = []
    st.session_state.current_document = None

def main():
    st.title("creditRepChat")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
        # Add reset button in sidebar
        if st.session_state.processed_file_path:
            if st.button("Upload New Document", use_container_width=True):
                reset_conversation()
                st.rerun()
    
    # Main content area
    if not st.session_state.processed_file_path:
        st.markdown("### Upload Your Document")
        uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
        
        if uploaded_file:
            file_path = process_document(uploaded_file)
            if file_path:
                st.session_state.processed_file_path = file_path
                st.session_state.current_document = uploaded_file.name
                st.success("Document processed successfully!")
                st.rerun()
    
    else:
        # Display current document information
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📄 Current Document: {st.session_state.current_document}")
        with col2:
            if st.button("New Document", key="new_doc"):
                reset_conversation()
                st.rerun()
        
        # Chat interface
        st.markdown("### Ask Questions About Your Document")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about your document..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = send_chat_message(prompt, st.session_state.processed_file_path)
                    if response:
                        st.markdown(response)
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Display initial message if no document is uploaded
    if not st.session_state.processed_file_path:
        st.info("👆 Please upload a PDF document to start the conversation.")

if __name__ == "__main__":
    main()