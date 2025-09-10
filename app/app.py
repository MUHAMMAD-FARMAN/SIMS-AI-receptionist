# Import necessary libraries
import streamlit as st
import google.generativeai as genai
import mysql.connector
import os
import pandas as pd
import re # Import the regular expression module

# Set the page configuration for a better look and feel
st.set_page_config(
    page_title="Hospital Info Chatbot",
    page_icon="�",
    layout="wide"
)

# --- 1. Database Connection and Caching ---
# @st.cache_resource decorator caches the database connection to prevent
# reconnecting on every rerun. It is essential for performance.
@st.cache_resource
def get_database_connection():
    """
    Establishes and returns a MySQL database connection.
    Credentials are loaded from Streamlit's secrets.toml.
    """
    try:
        conn = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"]
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to the database: {e}")
        return None

# Attempt to get a database connection
db_conn = get_database_connection()

# --- 2. Gemini API Configuration and Prompts ---
# Use st.secrets to securely store your API key
API_KEY = st.secrets["gemini"]["api_key"]
genai.configure(api_key=API_KEY)

# Define the models to be used
sql_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="""
    You are a highly specialized AI assistant that translates natural language questions into valid MySQL queries. 
    Your sole purpose is to generate the SQL query and nothing else. Do not provide any conversational text, explanations, or code comments. 
    Respond only with the MySQL query.
    Make sure your SQL query does NOT include any markdown formatting (e.g., ```sql).
    
    Database Schema:
    - Table: `departments` (columns: `department_id`, `name`, `notes`)
    - Table: `doctors` (columns: `doctor_id`, `name`, `profile_url`)
    - Table: `staff_roles` (columns: `role_id`, `role_name`)
    - Table: `department_staff` (linking table; columns: `department_staff_id`, `department_id`, `doctor_id`, `role_id`)
    - Table: `department_facilities` (columns: `facility_id`, `department_id`, `opd_days`, `emergency_days`, `diagnostic_facilities`)

    Rules for queries:
    - Use JOINs to connect tables.
    - Use `LIKE` with wildcards (%) for partial name matches.
    - For questions about staff, always include the doctor's name, their role, and their department.
    - For questions about a specific doctor or role, use `doctors.name` or `staff_roles.role_name` in the `WHERE` clause.
    - For questions about facilities, always include the department name and all facility columns.
    - Make sure your query is correct and well-formed. Do not use complex or nested subqueries that might fail.
    - Ensure your query returns all relevant data for the user's request.
    """
)

response_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="""
    You are a friendly and helpful hospital and college staff expert. Your job is to answer questions based on the provided data. 
    If the data is empty, state that no information was found. 
    Format the response clearly using a friendly, conversational tone and bullet points where appropriate.
    """
)

# --- 3. Chatbot UI and Logic ---
st.title("Hospital Information Chatbot 🏥")
st.markdown("Ask me anything about the hospital's departments, staff, and facilities!")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process user input
if user_query := st.chat_input("Ask a question about the hospital..."):
    # Display user message
    st.chat_message("user").markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("assistant"):
        if db_conn is None:
            st.error("I'm sorry, I can't connect to the database right now. Please try again later.")
        else:
            with st.spinner("Thinking..."):
                try:
                    # Step 1: Generate the SQL query
                    sql_response = sql_model.generate_content(user_query)
                    sql_query = sql_response.text.strip()
                    
                    # --- Text processing to remove Markdown code block ---
                    # Use a regular expression to remove ```sql and ``` from the start and end of the string
                    sql_query = re.sub(r'```sql\s*', '', sql_query, flags=re.IGNORECASE).strip()
                    sql_query = re.sub(r'\s*```', '', sql_query).strip()
                    # --- End of text processing ---

                    st.info(f"Generated SQL Query:\n```sql\n{sql_query}\n```")

                    # Step 2: Execute the SQL query
                    cursor = db_conn.cursor()
                    cursor.execute(sql_query)
                    query_results = cursor.fetchall()
                    column_names = [i[0] for i in cursor.description]
                    
                    if query_results:
                        df = pd.DataFrame(query_results, columns=column_names)
                        result_str = df.to_string(index=False)
                    else:
                        result_str = "No results found."

                    # Step 3: Generate the final conversational response
                    prompt_for_response = f"""
                    User Question: {user_query}
                    Database Results:
                    {result_str}
                    """
                    final_response = response_model.generate_content(prompt_for_response)
                    st.markdown(final_response.text)
                    st.session_state.messages.append({"role": "assistant", "content": final_response.text})

                except Exception as e:
                    error_message = f"An error occurred: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})