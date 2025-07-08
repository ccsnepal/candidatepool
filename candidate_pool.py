from random import randint
import nepali_datetime
from datetime import datetime
import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from candidate_designation import candidate_designation 
from cv_checker import cv_checker

st.set_page_config(page_title="Nokari Nepal", page_icon="nokarinepal_logo.png")

visit_office_options = ['Yes', 'No']
interview_status_options = ["Not Attended", "Interview Scheduled", "Interview Rejected", "Interview Selected", "Attended"]

# Function to check if the current Nepali month has ended based on the English date
def get_nepali_month_end_check():
    today_nepali = nepali_datetime.date.today()
    current_month = today_nepali.month
    
    if current_month == 12:
        next_month = 1
        next_year = today_nepali.year + 1
    else:
        next_month = current_month + 1
        next_year = today_nepali.year
    
    next_month_first_day = nepali_datetime.date(year=next_year, month=next_month, day=1)
    nepali_month_end = next_month_first_day - pd.Timedelta(days=1)
    
    return today_nepali == nepali_month_end

# Function to load data from Google Sheet and check for new month
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('candidate-pool.json', scope)
    client = gspread.authorize(creds)

    if get_nepali_month_end_check():
        today_nepali = nepali_datetime.date.today()
        current_month = today_nepali.month
        
        if current_month == 12:
            next_month = 1
            next_year = today_nepali.year + 1
        else:
            next_month = current_month + 1
            next_year = today_nepali.year
        
        next_month_nepali = nepali_datetime.date(year=next_year, month=next_month, day=1)
        nepali_month_name = next_month_nepali.nepali_month_name
        sheet_name = f"{nepali_month_name}"

        try:
            existing_sheets = client.open_by_url("https://docs.google.com/spreadsheets/d/1AbcuzPvbUOLn_3IBTuh1Ts-Y2tBOCBlMOhy4qNKEX8c/edit?usp=sharing").worksheets()
            sheet_names = [sheet.title for sheet in existing_sheets]
            if sheet_name not in sheet_names:
                client.open_by_url("https://docs.google.com/spreadsheets/d/1AbcuzPvbUOLn_3IBTuh1Ts-Y2tBOCBlMOhy4qNKEX8c/edit?usp=sharing").add_worksheet(title=sheet_name, rows="100", cols="20")
        except Exception as e:
            st.error(f"Error creating a new sheet: {e}")
        
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1AbcuzPvbUOLn_3IBTuh1Ts-Y2tBOCBlMOhy4qNKEX8c/edit?usp=sharing").sheet1
    data = pd.DataFrame(sheet.get_all_records())
    data.columns = data.columns.str.strip()

    if 'Visit Office Date' in data.columns:
        data['Visit Office Date'] = pd.to_datetime(data['Visit Office Date'], errors='coerce')

    if data['Visit Office Date'].isnull().any():
        print("Some 'Visit Office Date' entries could not be converted and are set as NaT.")

    data = data.loc[:, ~data.columns.duplicated()]

    if 'Blacklisted' not in data.columns:
        data['Blacklisted'] = False
    else:
        data['Blacklisted'] = data['Blacklisted'].astype(bool)

    return data

# Function to update the Google Sheet with data
def update_google_sheet(data):
    data = data.replace([pd.NA, float('inf'), float('-inf')], None)

    for col in data.columns:
        if data[col].dtype == 'object':
            data[col] = data[col].astype(str)

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('candidate-pool.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1AbcuzPvbUOLn_3IBTuh1Ts-Y2tBOCBlMOhy4qNKEX8c/edit?usp=sharing").sheet1
    sheet.clear()
    sheet.update([data.columns.values.tolist()] + data.values.tolist())

def candidate_pool_management(data):
    st.title("Candidate Pool Management")

    # Initialize form fields in session state
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            "candidate_name": "",
            "job_category": data['Job Category'].unique()[0],
            "visit_sources": data['Visit From Where ?'].unique()[0],
            "email_id": "",
            "job_selection": data['Job Selection'].unique()[0],
            "address": "",
            "contact_number": "",
            "interview_status": interview_status_options[0],
            "visit_office": visit_office_options[0],
            "visit_office_date": datetime.today().date(),
            "remarks": ""
        }

    col1, col2, col3 = st.columns(3)

    with col1:
        job_categories = ['All'] + list(data['Job Category'].unique())
        selected_categories = st.multiselect("Select Job Categories", job_categories)

    with col2:
        job_selection = ['All'] + list(data['Job Selection'].unique())
        selected_jobs = st.multiselect("Select Job Selections", job_selection)

    with col3:
        visit_sources = ['All'] + list(data['Visit From Where ?'].unique())
        selected_sources = st.multiselect("Select Visit Sources", visit_sources)

    search_query = st.text_input("Search Keyword", "")
    
    filtered_data = data

    if 'All' not in selected_categories:
        filtered_data = filtered_data[filtered_data['Job Category'].isin(selected_categories)]

    if 'All' not in selected_jobs:
        filtered_data = filtered_data[filtered_data['Job Selection'].isin(selected_jobs)]

    if 'All' not in selected_sources:
        filtered_data = filtered_data[filtered_data['Visit From Where ?'].isin(selected_sources)]

    if search_query:
        filtered_data = filtered_data[filtered_data.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    total_candidates = len(filtered_data)
    col_total, col_add = st.columns([3, 1])
    with col_total:
        st.write(f"Total Candidates: {total_candidates}")

    with col_add:
        if st.button("➕"):
            st.session_state.show_form = True

    if 'show_form' not in st.session_state:
        st.session_state.show_form = False

    if st.session_state.show_form:
        with st.expander("Add New Candidate", expanded=True):
            with st.form(key='add_candidate_form'):
                candidate_name = st.text_input("Candidate Name", value=st.session_state.form_data["candidate_name"])
                job_category = st.selectbox("Job Category", data['Job Category'].unique(), index=list(data['Job Category'].unique()).index(st.session_state.form_data["job_category"]))
                visit_sources = st.selectbox("Visit From Where?", data['Visit From Where ?'].unique(), index=list(data['Visit From Where ?'].unique()).index(st.session_state.form_data["visit_sources"]))
                email_id = st.text_input("Email Id", value=st.session_state.form_data["email_id"])
                job_selection = st.selectbox("Job Selection", data['Job Selection'].unique(), index=list(data['Job Selection'].unique()).index(st.session_state.form_data["job_selection"]))
                address = st.text_input("Address", value=st.session_state.form_data["address"])
                contact_number = st.text_input("Contact Number", value=st.session_state.form_data["contact_number"])
                interview_status = st.selectbox("Interview Status", interview_status_options, index=interview_status_options.index(st.session_state.form_data["interview_status"]))
                visit_office = st.selectbox("Visit Office", visit_office_options, index=visit_office_options.index(st.session_state.form_data["visit_office"]))
                visit_office_date = st.date_input("Visit Office Date", value=st.session_state.form_data["visit_office_date"])
                remarks = st.text_input("Remarks", value=st.session_state.form_data["remarks"])
                
                submit_button = st.form_submit_button(label='Add New Candidate')

                if submit_button:
                    visit_office_date_str = visit_office_date.strftime('%Y-%m-%d')

                    new_candidate = pd.DataFrame({
                        'Candidate Name': [candidate_name],
                        'Job Category': [job_category],
                        'Job Selection': [job_selection],
                        'Email Id': [email_id],
                        'Address': [address],
                        'Contact Number': [contact_number],
                        'Visit From Where ?': [visit_sources],
                        'Interview Status': [interview_status],
                        'Visit Office': [visit_office],
                        'Visit Office Date': [visit_office_date_str],
                        'Blacklisted': [False],
                        'Remarks': [remarks]
                    })

                    data = data.loc[:, ~data.columns.duplicated()]
                    new_candidate = new_candidate.reindex(columns=data.columns)

                    try:
                        data = pd.concat([data, new_candidate], ignore_index=True)
                    except Exception as e:
                        st.error(f"Error while appending new candidate: {e}")
                        raise

                    update_google_sheet(data)

                    st.success("New candidate added successfully!")
                    st.write("Candidate Details:")
                    st.write(new_candidate)

                    # Clear form fields by resetting session state values
                    st.session_state.form_data = {
                        "candidate_name": "",
                        "job_category": data['Job Category'].unique()[0],
                        "visit_sources": data['Visit From Where ?'].unique()[0],
                        "email_id": "",
                        "job_selection": data['Job Selection'].unique()[0],
                        "address": "",
                        "contact_number": "",
                        "interview_status": interview_status_options[0],
                        "visit_office": visit_office_options[0],
                        "visit_office_date": datetime.today().date(),
                        "remarks": ""
                    }
                    st.session_state.show_form = False

    current_page_data = pd.DataFrame()  # Initialize with an empty DataFrame
    
    column_config = {
        "Interview Status": st.column_config.SelectboxColumn(
            "Interview Status", options=interview_status_options
        ),
        "Visit Office": st.column_config.SelectboxColumn(
            "Visit Office", options=visit_office_options
        ),
        "Blacklisted": st.column_config.CheckboxColumn(
            "Blacklisted", help="Check to blacklist this candidate"
        ),
        'Visit From Where ?': st.column_config.SelectboxColumn(
                'Visit From Where ?', options=data['Visit From Where ?'].unique()
        ),
        'Job Category': st.column_config.SelectboxColumn(
                'Job Category', options=data['Job Category'].unique()
        ),
        'Job Selection': st.column_config.SelectboxColumn(
            'Job Selection', options=data['Job Selection'].unique()
        )
    }

    if total_candidates > 0:
        page_size = 7
        total_pages = (total_candidates // page_size) + (1 if total_candidates % page_size > 0 else 0)

        if "page_number" not in st.session_state:
            st.session_state.page_number = 1

        col1, col2 = st.columns([7, 1])
        with col1:
            if st.button("⬅️") and st.session_state.page_number > 1:
                st.session_state.page_number -= 1
        with col2:
            if st.button("➡️") and st.session_state.page_number < total_pages:
                st.session_state.page_number += 1

        page_number = st.session_state.page_number

        start_index = (page_number - 1) * page_size
        end_index = start_index + page_size
        current_page_data = filtered_data.iloc[start_index:end_index]

        st.write(f"Showing candidates {start_index + 1} - {min(end_index, total_candidates)}")

    edited_data = st.data_editor(current_page_data, num_rows="dynamic", column_config=column_config)

    if st.button("Save Changes") and edited_data is not None:
        edited_data['Blacklisted'] = edited_data.get('Blacklisted', False).apply(lambda x: True if x else False)
        edited_data = edited_data.replace([pd.NA, float('inf'), float('-inf')], None)
        data.update(edited_data)
        update_google_sheet(data)
        st.success("Candidates updated successfully!")

    candidate_counts = filtered_data['Visit From Where ?'].value_counts().reset_index()
    candidate_counts.columns = ['Source', 'Count']

    options = {
        "title": {"text": "Candidate Pool Management", "subtext": "Pie-Chart ", "left": "center"},
        "tooltip": {"trigger": "item"},
        "legend": {"orient": "vertical", "left": "left"},
        "series": [
            {
                "name": "Candidate Pool",
                "type": "pie",
                "radius": "50%",
                "data": [{"value": row['Count'], "name": row['Source']} for index, row in candidate_counts.iterrows()],
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                    }
                },
            }
        ],
    }

    st_echarts(options=options, height="600px")

def contact_us():
    st.title("Contact Us")
    st.write("For inquiries, please contact us at: hr@nokarinepal.com")
    st.write("Join us at Nokari Nepal as we work together to create a thriving job market that benefits both job seekers and employers alike.")

def main():
    st.sidebar.title("Nokari Nepal")
    page = st.sidebar.selectbox("Select a page", ["Home", "Candidate Pool Management", "Cv Checker", "Candidate Designation"])

    if page == "Home":
        st.title("Welcome to Nokari Nepal")
        st.write("This is the home page of the Candidate Pool Management System.")
        st.write("Nokari Nepal is a dedicated online platform designed to bridge the gap between job seekers and employers in Nepal. Our primary goal is to streamline the recruitment process, making it easier for companies to find qualified candidates and for job seekers to discover suitable job opportunities.")
    elif page == "Candidate Pool Management":
        data = load_data()
        candidate_pool_management(data)
    elif page == "Cv Checker":
        cv_checker()
    elif page == "Candidate Designation":
        candidate_designation()

if __name__ == "__main__":
    main()
