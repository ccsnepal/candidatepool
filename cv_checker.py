import streamlit as st
import requests
import pdfplumber
import re

# Replace with your actual Gemini API key
gemini_api_key = "AIzaSyA73jNiOkyjzm26-SzUNAXVFmADISV7_18"

def extract_text_from_pdf(uploaded_file):
    """Extract text from a PDF file."""
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:  # Check if text was extracted
                text += page_text + "\n"
    return text

def analyze_resume_with_gemini(resume_text):
    """Analyze the resume text using Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": f"Extract the candidate's name, phone number, current or temporary address, expected salary, education qualifications, key skills, suggest a job title based on the skills, and determine the job level (entry-level, mid-level, senior-level) based on the experience and training from the following resume: {resume_text}"
            }]
        }]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

def extract_contact_info(resume_text):
    """Extract phone number, education, and address from the resume text."""
    # Simple regex patterns for demonstration purposes
    phone_pattern = r"\+?\d[\d -]{8,12}\d"
    education_pattern = r"(Bachelor's|Master's|PhD|B\.?Sc|M\.?Sc|Diploma|Certificate|Degree)(.*?)(?=\n)"
    address_pattern = r"(\d{1,5}\s\w+(\s\w+)*,\s\w+,\s\w+,\s\w+|\w+(\s\w+)*,\s\w+,\s\w+,\s\w+)"  # Basic address pattern

    phone = re.search(phone_pattern, resume_text)
    education = re.findall(education_pattern, resume_text)
    address = re.findall(address_pattern, resume_text)

    return {
        "phone": phone.group(0).strip() if phone else "Not found",
        "education": [edu[0].strip() + " " + edu[1].strip() for edu in education] if education else ["Not found"],
        "address": address[0][0].strip() if address else "Not found"  # Get the first match for address
    }

def cv_checker():

    # Display the logo at the top of the app
    st.image("Cv_checker_logo.png", width=200)

    st.title("CV Checker")
    st.markdown("""
        Choose an option below to analyze a candidate's resume:
    """)

    # Select box for input method
    input_method = st.selectbox("Select Input Method", ["Upload PDF", "Paste Text"])

    # Initialize resume_text variable
    resume_text = ""

    if input_method == "Upload PDF":
        # File uploader
        uploaded_file = st.file_uploader("Upload candidate resume (PDF)", type=["pdf"])
        
        if uploaded_file is not None:
            # Extract text from the PDF
            resume_text = extract_text_from_pdf(uploaded_file)
            
            # Display the CV text
            st.subheader("Extracted CV Content from PDF")
            st.text_area("CV Text", value=resume_text, height=300)

    elif input_method == "Paste Text":
        # Text area for pasting resume text
        resume_text = st.text_area("Paste candidate resume text here:", height=300)

    # Check if the extracted text is empty
    if resume_text.strip():
        # Extract contact information
        contact_info = extract_contact_info(resume_text)

        # Analyze resume using Gemini AI
        if st.button("Analyze Resume"):
            with st.spinner("Analyzing..."):
                result = analyze_resume_with_gemini(resume_text)
                
                # Check for errors in the result
                if "error" in result:
                    st.error(result["error"])
                elif "candidates" in result and len(result["candidates"]) > 0:
                    candidate_info = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Extracting the name from the candidate_info
                    name_pattern = r"Candidate Name:\s*(.*?),"
                    name_match = re.search(name_pattern, candidate_info)
                    name = name_match.group(1).strip() if name_match else "Not found"

                    # Extracting skills from the candidate_info
                    skills_pattern = r"Skills:\s*(.*)"
                    skills_match = re.search(skills_pattern, candidate_info)
                    skills = skills_match.group(1).strip().split(", ") if skills_match else []

                    # Extracting job title suggestion from the candidate_info
                    job_title_pattern = r"Suggested Job Title:\s*(.*)"
                    job_title_match = re.search(job_title_pattern, candidate_info)
                    job_title = job_title_match.group(1).strip() if job_title_match else "Not found"

                    # Extracting job level from the candidate_info
                    job_level_pattern = r"Job Level:\s*(.*)"
                    job_level_match = re.search(job_level_pattern, candidate_info)
                    job_level = job_level_match.group(1).strip() if job_level_match else "Not found"

                    # Display extracted information in a structured format
                    st.subheader("Extracted Information")
                    st.write(f"**Name:** {name}")
                    st.write(f"**Phone:** {contact_info['phone']}")
                    st.write(f"**Education:** {', '.join(contact_info['education'])}")
                    st.write(f"**Address:** {contact_info['address']}")
                    st.write(f"**Skills:** {', '.join(skills)}")
                    st.write(f"**Suggested Job Title:** {job_title}")
                    st.write(f"**Job Level:** {job_level}")

                else:
                    st.error("No information could be extracted from the resume.")
    else:
        st.warning("Please upload a PDF or paste the resume text to analyze.")

    # Add a footer
    st.markdown("""
    This CV Checker is designed to help you identify the skills, name, phone number, and education qualifications mentioned in your CV using Nokari Nepal App.
    """)

if __name__ == "__main__":
    cv_checker()