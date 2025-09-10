import openpyxl
import re

def generate_text_chunks_from_xlsx(file_path):
    """
    Reads an XLSX file, parses the data, and generates semantically rich text chunks for RAG.
    This version consolidates information per department and role to create more comprehensive chunks.
    
    Args:
        file_path (str): The path to the input XLSX file.
        
    Returns:
        A list of formatted text chunks as strings.
    """
    chunks = []
    
    # Define staff roles based on the provided spreadsheet structure
    staff_roles = [
        'HOD', 'Professors', 'Associate Professor', 'Assisstant Professor', 
        'Registrar', 'Consultants', 'Senior Registrar', 'PGRs', 'Hos'
    ]
    # Define department detail columns
    detail_cols = [
        'Notes', 'OPD DAYS', 'Emergency days', 'Diagnostic Facilities', 
        'Services & treatments offered', 'OPD Room'
    ]

    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

    # Map column names to their indices
    header = [cell.value for cell in sheet[1]]
    col_indices = {}
    for i, col_name in enumerate(header):
        if col_name and str(col_name).strip() in (staff_roles + detail_cols + ['Department']):
            col_indices[str(col_name).strip()] = i

    if 'Department' not in col_indices:
        print("Error: 'Department' column not found.")
        return []

    departments_data = {}
    current_department_name = None

    # Step 1: Aggregate all data by department
    for row_idx, row in enumerate(sheet.iter_rows(min_row=2)):
        department_cell = row[col_indices['Department']]
        department_cell_value = department_cell.value
        
        # Check for a new department
        if department_cell_value and str(department_cell_value).strip() not in ('nan', '...', ''):
            current_department_name = str(department_cell_value).strip()
            # Initialize the dictionary for the new department
            departments_data[current_department_name] = {
                'staff': {role: set() for role in staff_roles},
                'details': {detail: set() for detail in detail_cols},
                'links': {}
            }
            
            # Handle department hyperlink
            if department_cell.hyperlink and department_cell.hyperlink.target:
                departments_data[current_department_name]['links']['department'] = department_cell.hyperlink.target
        
        # Ensure we have a department to associate data with
        if not current_department_name:
            continue

        # Aggregate staff members and their links
        for role_name in staff_roles:
            if role_name in col_indices:
                cell = row[col_indices[role_name]]
                cell_value = cell.value

                if cell_value and str(cell_value).strip() not in ('nan', '...', ''):
                    staff_list = [name.strip() for name in str(cell_value).split(',')]
                    for name in staff_list:
                        clean_name = re.sub(r'(Dr\.|Dr|\?)+', '', name, flags=re.I).strip()
                        if clean_name:
                            departments_data[current_department_name]['staff'][role_name].add(clean_name)
                            # Add hyperlink if it exists for the cell
                            if cell.hyperlink and cell.hyperlink.target:
                                # A simplified way to store staff links
                                if clean_name not in departments_data[current_department_name]['links']:
                                    departments_data[current_department_name]['links'][clean_name] = cell.hyperlink.target
        
        # Aggregate department details
        for col_name in detail_cols:
            if col_name in col_indices:
                cell = row[col_indices[col_name]]
                cell_value = cell.value
                if cell_value and str(cell_value).strip() not in ('nan', '...', ''):
                    # Handle special case for '...' entries with hyperlinks
                    if str(cell_value).strip() == '...' and cell.hyperlink and cell.hyperlink.target:
                        departments_data[current_department_name]['details'][col_name].add(cell.hyperlink.target)
                    else:
                        departments_data[current_department_name]['details'][col_name].add(str(cell_value).strip())

    # Step 2: Generate the consolidated chunks
    for department, data in departments_data.items():
        # Department link chunk
        if 'department' in data['links']:
            chunks.append(f"The {department} department has an official page at: {data['links']['department']}.")
        
        # Staff chunks
        for role_name, names in data['staff'].items():
            if names:
                formatted_names = []
                for name in sorted(list(names)):
                    link = data['links'].get(name)
                    if link:
                        formatted_names.append(f"{name} ({link})")
                    else:
                        formatted_names.append(name)
                names_string = ", ".join(formatted_names)
                chunks.append(f"The {role_name}s in the {department} department are: {names_string}.")
        
        # Details chunks
        for detail_name, values in data['details'].items():
            if values:
                # Check for "..." links and format them
                if detail_name in data['links']:
                    link_values = ", ".join(sorted(list(values)))
                    link_chunks = f"The {detail_name} for the {department} department has additional resources at: {link_values}."
                    chunks.append(link_chunks)
                else:
                    values_string = ", ".join(sorted(list(values)))
                    if detail_name == 'Notes':
                        chunks.append(f"The {department} department notes are: {values_string}.")
                    elif detail_name == 'OPD DAYS':
                        chunks.append(f"The {department} department has OPD days: {values_string}.")
                    elif detail_name == 'Emergency days':
                        chunks.append(f"The {department} department has emergency services on these days: {values_string}.")
                    elif detail_name == 'Diagnostic Facilities':
                        chunks.append(f"The {department} department provides these diagnostic facilities: {values_string}.")
                    elif detail_name == 'Services & treatments offered':
                        chunks.append(f"The {department} department offers these services and treatments: {values_string}.")
                    elif detail_name == 'OPD Room':
                        chunks.append(f"The OPD room for the {department} department is {values_string}.")

    return chunks

def save_chunks_to_file(chunks, output_file="hospital_chunks.txt"):
    """
    Saves a list of text chunks to a text file, with each chunk on a new line.
    
    Args:
        chunks (list): A list of text strings.
        output_file (str): The name of the file to save the chunks to.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(f"{chunk}\n")
        print(f"Text chunks successfully saved to '{output_file}'")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    file_name = "SHL Departments data.xlsx"
    
    # Generate the text chunks
    text_chunks = generate_text_chunks_from_xlsx(file_name)
    
    # Save the chunks to a file
    if text_chunks:
        save_chunks_to_file(text_chunks)