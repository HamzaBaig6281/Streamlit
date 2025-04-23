import os
import pandas as pd
import streamlit as st
from datetime import datetime
import numpy as np

# --- Configuration ---

# Simple dictionary for user credentials (username: password)
USERS = {
    "admin": "password123",
    "user1": "pass"
}

# This must be the first Streamlit command
st.set_page_config(page_title="Excel Data Manager", layout="wide")

# File mapping (table_name : filename) - Use lowercase table names consistently
EXCEL_FILES = {
    "students": "https://raw.githubusercontent.com/HamzaBaig6281/Streamlit/main/file3.xlsx",
    "college_admin_data": "https://raw.githubusercontent.com/HamzaBaig6281/Streamlit/main/college_admin_data.xlsx"
}


# Primary key mapping for each table (updated to match your actual column names)
PRIMARY_KEYS = {
    "students": "student_id",  # Changed from StudentId to student_id
    "college_admin_data": "admin_id"  # Changed from Admin_ID to admin_id
}


# --- Data Loading and Editing Functions ---

def get_table_data(table_name, file_path):
    """Get data from Excel file for a specific table"""
    try:
        if os.path.exists(file_path):
            df = pd.read_excel(file_path, engine='openpyxl')
            # Convert column names to lowercase for consistency
            df.columns = df.columns.str.strip().str.lower()
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].dtype == 'object': # Ensure it's actually text-like
                    df[col] = df[col].str.strip()
            return df
        else:
            st.warning(f"File not found: {file_path}. Returning empty DataFrame.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading {table_name} Excel data from {file_path}: {e}")
        return pd.DataFrame()

def display_data_editor(table_name, file_path):
    """Display an editable dataframe for the table (fixed rows)"""
    df = get_table_data(table_name, file_path)

    if df.empty and not os.path.exists(file_path):
        st.warning(f"Excel file for {table_name} does not exist at {file_path}. Cannot display data.")
        return
    elif df.empty and os.path.exists(file_path):
         st.info(f"The Excel file for {table_name} is empty or could not be read properly.")

    st.info("You can edit cell values here. Use 'Add New Record' tab to add rows, 'Delete Record' tab to remove rows.")
    try:
        edited_df = st.data_editor(
            df,
            key=f"editor_{table_name}",
            num_rows="fixed",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Error displaying data editor for {table_name}: {e}")
        st.info("This might happen if the Excel file structure is incompatible or corrupt.")
        return

    if st.button(f"Save Changes to {table_name}"):
        if edited_df.equals(df):
            st.info("No changes detected.")
        else:
            pk_col = PRIMARY_KEYS.get(table_name)
            if not pk_col:
                st.error(f"Primary key not defined for {table_name}. Cannot validate changes.")
                return
            
            # Convert edited_df columns to lowercase for comparison
            edited_df.columns = edited_df.columns.str.strip().str.lower()
            
            if pk_col not in edited_df.columns:
                 st.error(f"Critical error: Primary key column '{pk_col}' is missing in the edited data.")
                 return

            pk_series_str = edited_df[pk_col].astype(str)
            if edited_df[pk_col].isnull().any() or (pk_series_str == '').any() or (pk_series_str.str.lower() == 'nan').any() or (pk_series_str.str.lower() == 'nat').any():
                st.error(f"Error: Primary key column '{pk_col}' cannot contain empty values. Please correct the data.")
                invalid_rows = edited_df[edited_df[pk_col].isnull() | (pk_series_str == '') | (pk_series_str.str.lower() == 'nan') | (pk_series_str.str.lower() == 'nat')]
                if not invalid_rows.empty:
                    st.dataframe(invalid_rows)
                return

            if pk_series_str.duplicated().any():
                st.error(f"Error: Duplicate values found in the primary key column '{pk_col}' after editing. Each value must be unique.")
                st.dataframe(edited_df[pk_series_str.duplicated(keep=False)])
                return

            try:
                edited_df.to_excel(file_path, index=False, engine='openpyxl')
                st.success(f"Changes saved to Excel file: {os.path.basename(file_path)}")
            except Exception as e:
                st.error(f"Error saving changes: {e}")

def check_pk_exists(file_path, pk_column_name, pk_value):
    """Check if a Primary Key value already exists in the Excel file."""
    if not os.path.exists(file_path):
        return False
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        # Convert column names to lowercase for comparison
        df.columns = df.columns.str.strip().str.lower()
        pk_column_name = pk_column_name.lower()
        
        if pk_column_name not in df.columns:
             st.warning(f"PK Column '{pk_column_name}' not found in {os.path.basename(file_path)} for checking.")
             return False
        return str(pk_value).strip().lower() in df[pk_column_name].astype(str).str.strip().str.lower().values
    except Exception as e:
        st.error(f"Error checking PK in Excel: {e}")
        return False

def add_new_record_form(table_name, file_path):
    """Form to add new records to a table with duplicate PK check"""
    st.subheader(f"Add New Record to {table_name}")
    pk_column = PRIMARY_KEYS.get(table_name)
    if not pk_column:
        st.error(f"Primary key not defined for table '{table_name}'. Cannot add records.")
        return

    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if table_name == "students":
        with st.form(key=f"add_{table_name}_form", clear_on_submit=True):
            st.info(f"Enter details for a new student. {pk_column} must be unique.")
            student_id = st.text_input(f"{pk_column}*", key=f"add_sid_{table_name}")
            student_Name = st.text_input("StudentName*", key=f"add_sname_{table_name}")
            student_class = st.number_input("class*", min_value=1, step=1, key=f"add_class_{table_name}")
            gender = st.selectbox("gender*", ["Male", "Female", "Other", "Prefer not to say"], key=f"add_gen_{table_name}")
            dob = st.date_input("dob*", key=f"add_dob_{table_name}")
            email = st.text_input("email*", key=f"add_email_{table_name}")
            phone = st.text_input("phone", key=f"add_phone_{table_name}")
            address = st.text_area("address", key=f"add_addr_{table_name}")
            admission_date = st.date_input("admission_date*", value=datetime.now().date(), key=f"add_adm_{table_name}")
            fee_status = st.selectbox("fee_status*", ["Paid", "Unpaid", "Partial"], key=f"add_fee_{table_name}")

            submitted = st.form_submit_button("Add Student Record")
            if submitted:
                required_fields = [student_id, student_name, student_class, gender, dob, email, admission_date, fee_status]
                if not all(str(field).strip() for field in required_fields if not isinstance(field, (int, float, pd.Timestamp, datetime))):
                     if not all(required_fields):
                         st.error("Please fill all required fields (*)")
                         return

                if not str(student_id).strip():
                    st.error(f"{pk_column} cannot be empty.")
                    return

                if check_pk_exists(file_path, pk_column, student_id):
                     st.error(f"Error: {pk_column} '{student_id}' already exists. Please use a unique ID.")
                else:
                    new_record = {
                        "student_id": str(student_id).strip(),
                        "studentName": str(student_Name).strip(),
                        "class": student_class,
                        "gender": gender,
                        "dob": dob,
                        "email": str(email).strip(),
                        "phone": str(phone).strip() if phone else None,
                        "address": str(address).strip() if address else None,
                        "admission_date": admission_date,
                        "fee_status": fee_status,
                        "last_updated": last_updated
                    }
                    update_table(table_name, file_path, new_record)
                    st.rerun()

    elif table_name == "college_admin_data":
        with st.form(key=f"add_{table_name}_form", clear_on_submit=True):
            st.info(f"Enter details for new admin staff. {pk_column} must be unique.")
            admin_id = st.text_input(f"{pk_column}*", key=f"add_adminid_{table_name}")
            full_name = st.text_input("Full_Name*", key=f"add_admin_fname_{table_name}")
            email = st.text_input("Email*", key=f"add_admin_email_{table_name}")
            phone_number = st.text_input("Phone_Number", key=f"add_admin_phone_{table_name}")
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], key=f"add_admin_gen_{table_name}")
            dob = st.date_input("Date_of_Birth", key=f"add_admin_dob_{table_name}")
            address = st.text_area("Address", key=f"add_admin_addr_{table_name}")
            position = st.text_input("Position*", key=f"add_admin_pos_{table_name}")
            department = st.text_input("Department*", key=f"add_admin_dept_{table_name}")
            date_joined = st.date_input("Date_Joined*", value=datetime.now().date(), key=f"add_admin_join_{table_name}")
            employment_status = st.selectbox("Employment_Status", ["Active", "On Leave", "Resigned", "Terminated"], key=f"add_admin_stat_{table_name}")
            salary = st.number_input("Salary", min_value=0.0, step=100.0, format="%.2f", key=f"add_admin_sal_{table_name}")
            work_shift = st.selectbox("Work_Shift", ["Morning", "Evening", "Night", "Full-Time", "Part-Time"], key=f"add_admin_shift_{table_name}")

            submitted = st.form_submit_button("Add Admin Record")
            if submitted:
                required = [admin_id, full_name, email, position, department, date_joined]
                if not all(str(field).strip() for field in required if isinstance(field, str)):
                    if not all(required):
                        st.error("Please fill all required fields (*)")
                        return
                if not str(admin_id).strip():
                    st.error(f"{pk_column} cannot be empty.")
                    return

                if check_pk_exists(file_path, pk_column, admin_id):
                     st.error(f"Error: {pk_column} '{admin_id}' already exists. Please use a unique ID.")
                else:
                    new_record = {
                        "admin_id": str(admin_id).strip(),
                        "full_name": str(full_name).strip(),
                        "email": str(email).strip(),
                        "phone_number": str(phone_number).strip() if phone_number else None,
                        "gender": gender,
                        "date_of_birth": dob,
                        "address": str(address).strip() if address else None,
                        "position": str(position).strip(),
                        "department": str(department).strip(),
                        "date_joined": date_joined,
                        "employment_status": employment_status,
                        "salary": salary if salary is not None else None,
                        "work_shift": work_shift,
                        "last_updated": last_updated
                    }
                    update_table(table_name, file_path, new_record)
                    st.rerun()
    else:
        st.warning(f"No 'Add Record' form defined for table: {table_name}")

def update_table(table_name, file_path, new_record):
    """Append new record to Excel file."""
    try:
        new_df_row = pd.DataFrame([new_record])
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
                # Convert existing columns to lowercase
                df.columns = df.columns.str.strip().str.lower()
                
                # Ensure new record matches existing columns
                for col in df.columns:
                     if col not in new_df_row.columns:
                         new_df_row[col] = np.nan
                new_df_row = new_df_row[df.columns]
                df = pd.concat([df, new_df_row], ignore_index=True)
            except Exception as read_err:
                 st.error(f"Error reading existing Excel file {os.path.basename(file_path)} to append: {read_err}")
                 st.info("Attempting to overwrite the file with the new record only.")
                 df = new_df_row
        else:
            df = new_df_row
            st.info(f"Creating new Excel file: {os.path.basename(file_path)}")

        for col in df.columns:
            if 'date' in col.lower() or 'dob' in col.lower():
                 df[col] = pd.to_datetime(df[col], errors='coerce')

        df.to_excel(file_path, index=False, engine='openpyxl')
        st.success(f"Record added/updated in Excel: {os.path.basename(file_path)}")

    except Exception as e:
        st.error(f"Error adding/updating record: {e}")
        import traceback
        st.error(traceback.format_exc())

def delete_record(table_name, file_path, record_id_to_delete):
    """Delete a record from Excel file based on Primary Key"""
    if not os.path.exists(file_path):
        st.error(f"Excel file {os.path.basename(file_path)} not found. Cannot delete.")
        return False

    pk_column = PRIMARY_KEYS.get(table_name)
    if not pk_column:
        st.error(f"Primary key not defined for table '{table_name}'. Cannot delete.")
        return False

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        # Convert column names to lowercase for comparison
        df.columns = df.columns.str.strip().str.lower()
        pk_column = pk_column.lower()
        
        if pk_column not in df.columns:
            st.error(f"Primary Key column '{pk_column}' not found in Excel file. Cannot delete.")
            return False

        original_row_count = len(df)
        df_filtered = df[df[pk_column].astype(str) != str(record_id_to_delete)]

        if len(df_filtered) < original_row_count:
             df_filtered.to_excel(file_path, index=False, engine='openpyxl')
             st.success(f"Record '{record_id_to_delete}' removed from Excel file.")
             return True
        else:
             st.warning(f"Record with {pk_column} '{record_id_to_delete}' not found in the Excel file.")
             return False

    except Exception as e:
        st.error(f"Error deleting record: {e}")
        import traceback
        st.error(traceback.format_exc())
        return False

# --- Login/Logout Functions ---

def login_form():
    """Displays the login form and handles authentication."""
    st.title("Login - School Data Management System")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username in USERS and USERS[username] == password:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success("Logged In Successfully!")
                st.rerun()
            else:
                st.error("Incorrect Username or Password")

def logout():
    """Handles logout action."""
    if 'logged_in' in st.session_state:
        del st.session_state['logged_in']
    if 'username' in st.session_state:
        del st.session_state['username']
    st.success("Logged Out Successfully!")
    st.rerun()

# --- Main App Logic ---

def show_main_app():
    """Displays the main application content after successful login."""
    st.sidebar.header("Dataset Selection")
    st.sidebar.write(f"Welcome, {st.session_state.get('username', 'User')}!")
    if st.sidebar.button("Logout"):
        logout()

    table_display_names = list(EXCEL_FILES.keys())
    selected_table_display_name = st.sidebar.selectbox(
        "Select Dataset to Manage",
        table_display_names,
        key="table_select_sidebar"
    )
    selected_table_name = selected_table_display_name.lower()
    file_path = os.path.join(excel_folder, EXCEL_FILES[selected_table_display_name])

    st.title("School Data Management System")

    if not os.path.isdir(excel_folder):
         st.error(f"Error: The specified Excel folder does not exist: {excel_folder}")
         st.stop()

    if not os.path.exists(file_path):
        st.warning(f"Note: The Excel file '{EXCEL_FILES[selected_table_display_name]}' does not exist yet in {excel_folder}. It will be created if you add a record.")

    try:
        view_tab, add_tab, delete_tab = st.tabs([
            "View / Edit Data",
            "Add New Record",
            "Delete Record"
        ])

        with view_tab:
            st.subheader(f"View / Edit Existing {selected_table_display_name} Data")
            display_data_editor(selected_table_name, file_path)

        with add_tab:
            add_new_record_form(selected_table_name, file_path)

        with delete_tab:
            st.subheader(f"Delete Record from {selected_table_display_name}")
            df_delete = get_table_data(selected_table_name, file_path)
            pk_column_delete = PRIMARY_KEYS.get(selected_table_name)

            if pk_column_delete and not df_delete.empty:
                # Find the actual column name in the dataframe
                actual_pk_column = None
                for col in df_delete.columns:
                    if col.lower() == pk_column_delete.lower():
                        actual_pk_column = col
                        break
                
                if actual_pk_column:
                    valid_ids_to_delete = df_delete[actual_pk_column].dropna().astype(str).unique()
                    valid_ids_to_delete = [i for i in valid_ids_to_delete if i.strip() and i.lower() not in ('nan', 'nat')]

                    if valid_ids_to_delete:
                        record_to_delete = st.selectbox(
                            f"Select {actual_pk_column} of the record to delete",
                            options=sorted(valid_ids_to_delete),
                            key=f"delete_select_{selected_table_name}"
                        )
                        st.warning("Deleting a record is permanent in the Excel file.")
                        if st.button("Delete Selected Record", type="primary", key=f"delete_button_{selected_table_name}"):
                            if record_to_delete:
                                 deleted = delete_record(selected_table_name, file_path, record_to_delete)
                                 if deleted:
                                     st.rerun()
                                 else:
                                     st.error("Deletion failed. Check warnings/errors above.")
                            else:
                                 st.error("Please select a record ID to delete.")
                    else:
                        st.info("No records with valid IDs available to delete in the Excel file.")
                else:
                    st.error(f"Cannot find primary key column '{pk_column_delete}' in the Excel file.")
            elif df_delete.empty:
                st.info("The Excel file is empty or could not be read. No records to delete.")
            elif not pk_column_delete:
                 st.error(f"Primary Key not defined for {selected_table_name}. Cannot delete.")
            else:
                 st.error(f"Cannot setup delete options. Primary Key column '{pk_column_delete}' not found in {os.path.basename(file_path)}.")

    except Exception as e:
        st.error(f"An error occurred: {e}")

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state.get('logged_in', False):
        login_form()
    else:
        show_main_app()

if __name__ == "__main__":
    main()