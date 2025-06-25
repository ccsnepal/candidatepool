import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pandas as pd

# Setup Google Sheets connection
def setup_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('candidate-designation.json', scope)
    client = gspread.authorize(creds)
    return client.open_by_key('1z4zWATknbM4aKs5g-nUaKutuK81KgSrJRwvQWK8n4zw')

# Read data from sheet into DataFrame
def get_dataframe(sheet):
    worksheet = sheet.sheet1
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def save_dataframe(sheet, df):
    worksheet = sheet.sheet1
    df = df.fillna("")  # Replace NaN with empty strings

    # Keep headers, only clear data rows
    worksheet.resize(rows=1)

    # Append new data
    worksheet.append_rows(df.values.tolist())


# Candidate entry form function
def candidate_designation():
    st.title("Candidate Entry Form")

    # Input fields
    applicant = st.text_input("Applicant Name")
    role = st.text_input("Role")
    contact = st.text_input("Contact Number")
    address = st.text_input("Address")
    education = st.text_input("Education Qualification")
    remarks = st.text_area("Remarks")
    call_status = st.text_area("Call Status")
    office_visit = st.text_area("Office Visit Remarks")
    date = st.date_input("Select Date")

    sheet = setup_google_sheets()

    if st.button("Submit"):
        if applicant and role and contact and address and education:
            try:
                worksheet = sheet.sheet1
                worksheet.append_row([
                    applicant,
                    role,
                    contact,
                    address,
                    education,
                    remarks,
                    date.strftime('%Y-%m-%d'),
                    call_status,
                    office_visit
                ])
                st.success("Data saved successfully!")
            except Exception as e:
                st.error(f"Error updating sheet: {e}")
        else:
            st.error("Please fill in all required fields.")

    # Show editable data table below
    st.subheader("Existing Candidate Data")
    df = get_dataframe(sheet)

    # Show editable table
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button("Save Changes"):
        try:
            save_dataframe(sheet, edited_df)
            st.success("Changes saved to Google Sheets!")
        except Exception as e:
            st.error(f"Failed to save changes: {e}")

# Run the app
if __name__ == "__main__":
    candidate_designation()
