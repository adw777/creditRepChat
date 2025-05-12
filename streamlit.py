import streamlit as st
import requests
import os
from typing import List, Dict
# from openai import OpenAI

# FastAPI endpoint URLs
API_BASE_URL = "https://sweeping-moth-probably.ngrok-free.app"
PARSE_URL = f"{API_BASE_URL}/parse"
CHAT_URL = f"{API_BASE_URL}/chat"
EMAIL_URL = f"{API_BASE_URL}/sendEmail"

# Page configuration
st.set_page_config(
    page_title="creditRepChat",
    page_icon="📄",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'processed_file_path' not in st.session_state:
        st.session_state.processed_file_path = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_document' not in st.session_state:
        st.session_state.current_document = None
    if 'dispute_mode' not in st.session_state:
        st.session_state.dispute_mode = False
    if 'dispute_details' not in st.session_state:
        st.session_state.dispute_details = None

def detect_dispute_intent(message: str) -> bool:
    """Detect if the message indicates a dispute"""
    dispute_keywords = [
        "incorrect", "wrong", "error", "mistake", "not true",
        "dispute", "inaccurate", "false", "never", "not mine"
    ]
    return any(keyword in message.lower() for keyword in dispute_keywords)

def handle_dispute_process():
    """Handle the dispute process including email generation"""
    st.markdown("### 📝 Credit Report Dispute Form")
    
    # Collect dispute details
    dispute_details = st.text_area(
        "Please describe what specific information is incorrect and why:",
        help="Be specific about which information is wrong and provide any supporting details."
    )
    
    # Collect email addresses
    col1, col2 = st.columns(2)
    with col1:
        user_email = st.text_input("Your email address:")
    with col2:
        bank_email = st.text_input("Bank's email address:")
    
    if dispute_details and user_email and bank_email:
        # Generate email content using the chat endpoint
        email_prompt = f"""
        Generate a formal credit report dispute email with the following information:
        Dispute Details: {dispute_details}
        
        The email should include:
        1. A clear subject line for credit report dispute
        2. Professional greeting
        3. Clear statement of the dispute
        4. Reference to Fair Credit Reporting Act (FCRA)
        5. Request for investigation and correction
        6. Professional closing
        
        Format the response as:
        SUBJECT: [subject line]
        [rest of the email body]
        """
        
        try:
            # Get email content from chat endpoint
            response = requests.post(
                CHAT_URL,
                json={"query": email_prompt, "document_path": st.session_state.processed_file_path}
            )
            response.raise_for_status()
            email_content = response.json()["response"]
            
            # Split into subject and body
            email_lines = email_content.split("\n")
            subject = email_lines[0].replace("SUBJECT:", "").strip()
            body = "\n".join(email_lines[1:]).strip()
            
            # Show email preview
            st.markdown("### 📧 Preview Generated Email")
            st.info(f"**Subject:** {subject}")
            st.text_area("Email Body", body, height=300, disabled=True)
            
            # Send email button
            if st.button("Send Email"):
                # Send email using email endpoint
                email_response = requests.post(
                    EMAIL_URL,
                    json={
                        "sender_email": user_email,
                        "receiver_email": bank_email,
                        "subject": subject,
                        "body": body,
                        "attachment_path": None
                    }
                )
                
                if email_response.status_code == 200:
                    st.success("✅ Your dispute email has been sent successfully!")
                    # Add dispute confirmation to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "I've sent the email. You should receive a confirmation from the bank. Keep your details for your records."
                    })
                    st.session_state.dispute_mode = False
                    st.rerun()
                else:
                    st.error("❌ Failed to send email. Please try again.")
        
        except Exception as e:
            st.error(f"Error generating email: {str(e)}")

def process_document(uploaded_file):
    """Send document to FastAPI endpoint for processing"""
    if uploaded_file is not None:
        files = {"file": uploaded_file}
        try:
            with st.spinner("Processing document..."):
                response = requests.post(PARSE_URL, files=files)
                response.raise_for_status()
                result = response.json()
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
    st.session_state.dispute_mode = False
    st.session_state.dispute_details = None

def main():
    st.title("creditRepChat")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
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
        
        # Handle dispute mode if active
        if st.session_state.dispute_mode:
            handle_dispute_process()
        
        # Display chat messages
        st.markdown("### 💬 Ask your queries")
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
            
            # Check for dispute intent
            if detect_dispute_intent(prompt):
                st.session_state.dispute_mode = True
                with st.chat_message("assistant"):
                    st.markdown("I notice you're reporting incorrect information. I'll help you file a dispute. Please fill out the dispute form above.")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "I notice you're reporting incorrect information. I'll help you file a dispute. Please fill out the dispute form above."
                })
                st.rerun()
            
            # Get and display assistant response
            else:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = send_chat_message(prompt, st.session_state.processed_file_path)
                        if response:
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Display initial message if no document is uploaded
    if not st.session_state.processed_file_path:
        st.info("👆 Please upload a PDF document to start the conversation.")

if __name__ == "__main__":
    main()