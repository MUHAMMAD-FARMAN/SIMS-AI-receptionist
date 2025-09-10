import openpyxl
import re

def generate_sql_from_xlsx(file_path):
    """
    Reads an XLSX file using openpyxl, parses the data, and generates SQL INSERT statements.

    Args:
        file_path (str): The path to the input XLSX file.

    Returns:
        A list of SQL statements as strings.
    """
    sql_statements = []

    # Dictionaries to store data and prevent duplicates
    departments_data = {}
    # Stores unique doctors: {unique_key: {'name': '...', 'url': '...'}}
    doctors_data = {} 
    facilities_data = {}
    
    # List to store links between department, doctor, and role
    staff_links_to_insert = []
    
    # Store roles to insert them later
    staff_roles = ['HOD', 'Professors', 'Associate Professor', 'Assisstant Professor', 'Registrar', 'Consultants', 'Senior Registrar', 'PGRs', 'Hos']

    # Load the workbook and get the active sheet
    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

    # Map column names to their indices
    header = [cell.value for cell in sheet[1]]
    role_indices = {role: header.index(role) + 1 for role in staff_roles if role in header}
    dept_index = header.index('Department') + 1 if 'Department' in header else -1
    notes_index = header.index('Notes') + 1 if 'Notes' in header else -1
    opd_index = header.index('OPD  DAYS') + 1 if 'OPD  DAYS' in header else -1
    emergency_index = header.index('Emergency days') + 1 if 'Emergency days' in header else -1
    diagnostic_index = header.index('Diagnostic Facilities') + 1 if 'Diagnostic Facilities' in header else -1
    
    if dept_index == -1:
        print("Error: 'Department' column not found.")
        return []

    current_department_name = None

    for row_idx, row in enumerate(sheet.iter_rows(min_row=2)):
        # Determine the current department
        department_cell_value = row[dept_index - 1].value
        if department_cell_value and department_cell_value != 'nan':
            current_department_name = department_cell_value.strip()

        if current_department_name:
            # Handle department notes
            if current_department_name not in departments_data:
                notes = row[notes_index - 1].value if notes_index != -1 and row[notes_index - 1].value else ''
                departments_data[current_department_name] = notes.strip()

            # Handle facilities
            opd_days_value = row[opd_index - 1].value if opd_index != -1 else ''
            emergency_days_value = row[emergency_index - 1].value if emergency_index != -1 else ''
            diagnostic_facilities_value = row[diagnostic_index - 1].value if diagnostic_index != -1 else ''

            if any([opd_days_value, emergency_days_value, diagnostic_facilities_value]):
                if current_department_name not in facilities_data:
                    facilities_data[current_department_name] = {'opd': [], 'emergency': [], 'diagnostic': []}
                
                if opd_days_value:
                    facilities_data[current_department_name]['opd'].append(opd_days_value)
                if emergency_days_value:
                    facilities_data[current_department_name]['emergency'].append(emergency_days_value)
                if diagnostic_facilities_value:
                    facilities_data[current_department_name]['diagnostic'].append(diagnostic_facilities_value)

            # Process staff
            for role_name, col_index in role_indices.items():
                cell = row[col_index - 1]
                staff_string = cell.value
                
                if staff_string and staff_string != 'nan':
                    staff_list = [name.strip() for name in str(staff_string).split(',')]
                    
                    for name in staff_list:
                        clean_name = re.sub(r'(Dr\.|Dr|\?)+', '', name, flags=re.I).strip()
                        
                        if clean_name:
                            profile_url = None
                            # Check for a hyperlink in the cell
                            if cell.hyperlink and cell.hyperlink.target:
                                profile_url = cell.hyperlink.target
                            
                            # Create a unique key for the doctor based on name, role, and department
                            unique_doctor_key = f"{clean_name}|{role_name}|{current_department_name}|{row_idx}"

                            # Add the doctor to the doctors_data dictionary if they are not already there
                            if unique_doctor_key not in doctors_data:
                                doctors_data[unique_doctor_key] = {
                                    'name': clean_name, 
                                    'url': profile_url
                                }
                            
                            # Append to the list of links to be inserted into department_staff
                            staff_links_to_insert.append({
                                'department': current_department_name,
                                'unique_key': unique_doctor_key,
                                'role': role_name
                            })

    # Generate INSERT statements for `staff_roles`
    for role in staff_roles:
        sql_statements.append(f"INSERT INTO staff_roles (role_name) VALUES ('{role}');")
        
    # Generate INSERT statements for `departments`
    for name, notes in departments_data.items():
        sql_statements.append(f"INSERT INTO departments (name, notes) VALUES ('{name}', '{notes}');")
    
    # Generate INSERT statements for `doctors`
    for key, data in doctors_data.items():
        url_part = f", '{data['url']}'" if data['url'] else ", NULL"
        # We need to make the name unique for insertion. Let's append the unique_key.
        # This will make sure each doctor gets their own record
        unique_name_for_insertion = f"{data['name']} ({key.split('|')[-1]})"
        sql_statements.append(f"INSERT INTO doctors (name, profile_url) VALUES ('{unique_name_for_insertion}'{url_part});")

    # Generate INSERT statements for `department_facilities`
    for department_name, data in facilities_data.items():
        opd_str = ', '.join(data['opd']).strip(', ')
        emergency_str = ', '.join(data['emergency']).strip(', ')
        diagnostic_str = ', '.join(data['diagnostic']).strip(', ')
        
        sql_statements.append(f"""
        INSERT INTO department_facilities (department_id, opd_days, emergency_days, diagnostic_facilities)
        VALUES (
            (SELECT department_id FROM departments WHERE name = '{department_name}'),
            '{opd_str}',
            '{emergency_str}',
            '{diagnostic_str}'
        );
        """)
    
    # Generate INSERT statements for `department_staff` (linking table)
    for link in staff_links_to_insert:
        unique_name = f"{doctors_data[link['unique_key']]['name']} ({link['unique_key'].split('|')[-1]})"
        sql_statements.append(f"""
        INSERT INTO department_staff (department_id, doctor_id, role_id)
        VALUES (
            (SELECT department_id FROM departments WHERE name = '{link['department']}'),
            (SELECT doctor_id FROM doctors WHERE name = '{unique_name}'),
            (SELECT role_id FROM staff_roles WHERE role_name = '{link['role']}')
        );
        """)

    return sql_statements

def save_sql_to_file(statements, output_file="hospital_inserts.sql"):
    """
    Saves a list of SQL statements to a text file.

    Args:
        statements (list): A list of SQL statements.
        output_file (str): The name of the file to save the statements to.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for statement in statements:
                f.write(f"{statement}\n\n")
        print(f"SQL statements successfully saved to '{output_file}'")
    except Exception as e:
        print(f"Error saving file: {e}")

# The filename from your uploaded spreadsheet
file_name = "Departments data (Repaired).xlsx"

# Generate the SQL statements
sql_inserts = generate_sql_from_xlsx(file_name)

# Save the SQL statements to a file
save_sql_to_file(sql_inserts)
