import mysql.connector
import os
import glob
import argparse

def connect_to_database(database: str) -> mysql.connector.MySQLConnection:
    """
    Establish a connection to the specified MySQL database.

    Args:
        database (str): The name of the database to connect to.

    Returns:
        mysql.connector.MySQLConnection: The MySQL connection object.
    """
    return mysql.connector.connect(
        host='192.168.10.42',
        port=3377,
        user='jcontramestre',
        password='904OBol6PY0mcIpN',
        database=database
    )

def get_variant_id(customer_variant: str) -> int:
    """
    Retrieve the ID of a variant from the database based on its name.

    Args:
        customer_variant (str): The name of the variant to look up.

    Returns:
        int: The ID of the variant if found, otherwise None.
    """
    query = "SELECT idVariant FROM Variants WHERE variantName = %s"
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (customer_variant,))
            result = cursor.fetchone()
    return result[0] if result else None

def get_existing_thresholds(id_variant: int) -> str:
    """
    Retrieve existing thresholds for the given variant ID from the database.

    Args:
        id_variant (int): The ID of the variant.

    Returns:
        str: The existing thresholds in CSV format, or an empty string if none exist.
    """
    query = "SELECT variantThresholds FROM Variants WHERE idVariant = %s"
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (id_variant,))
            result = cursor.fetchone()
    return result[0] if result and result[0] else ""

def update_variant_program_and_thresholds(id_variant: int, new_variant_program: str, variant_thresholds: str) -> None:
    """
    Update the variant program and thresholds in the database for a given variant ID.

    Args:
        id_variant (int): The ID of the variant to update.
        new_variant_program (str): The new variant program to set.
        variant_thresholds (str): The new variant thresholds to set.
    """
    query = """
        UPDATE Variants
        SET variantProgram = %s,
            variantThresholds = %s
        WHERE idVariant = %s
    """
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (new_variant_program, variant_thresholds, id_variant))
            conn.commit()

def find_rspt_file(directory: str) -> str:
    """
    Find the first .rspt file in the specified directory.

    Args:
        directory (str): The directory to search for .rspt files.

    Returns:
        str: The path of the first .rspt file found, or None if no files are found.
    """
    rspt_files = glob.glob(os.path.join(directory, '*.rspt'))
    return rspt_files[0] if rspt_files else None

def filter_lines_with_decimals_from_content(content: str) -> list:
    """
    Filter lines from the content that contain decimal numbers and format them.

    Args:
        content (str): The content to filter.

    Returns:
        list: A list of filtered and formatted lines containing decimal numbers.
    """
    lines = content.splitlines()
    decimal_lines = [line for line in lines if any('.' in word for word in line.split(','))]
    
    processed_lines = []
    for line in decimal_lines:
        parts = line.split(',')
        new_line = parts[0] + ','  # Start with the first part and a comma
        for i in range(1, len(parts)):
            new_line += parts[i]
            if (i < len(parts) - 1 and 
                parts[i].strip().replace('.', '').isdigit() and 
                parts[i + 1].strip().replace('.', '').isdigit()):
                new_line += ',' 
        processed_lines.append(new_line.strip())  # Remove any trailing whitespace
    return processed_lines

def generate_variant_thresholds(variant_program: str, existing_thresholds: str) -> str:
    """
    Generate variant thresholds based on the filtered lines from the variant program.
    If existing thresholds are present, use them instead of generating new ones.

    Args:
        variant_program (str): The content of the variant program.
        existing_thresholds (str): Existing thresholds in CSV format.

    Returns:
        str: A string of thresholds in CSV format.
    """
    if existing_thresholds:
        return existing_thresholds

    filtered_lines = filter_lines_with_decimals_from_content(variant_program)
    total_lines = len(filtered_lines)
    num_thresholds = total_lines // 2
    thresholds = "\n".join(f"{i+1},0.3" for i in range(num_thresholds))
    return thresholds

def main(customer_variant: str) -> str:
    """
    Main function to update the variant program and thresholds for a given customer variant.

    Args:
        customer_variant (str): The name of the customer variant to update.

    Returns:
        str: A message indicating the result of the operation.
    """
    id_variant = get_variant_id(customer_variant)
    
    if not id_variant:
        return f"No variant found with name {customer_variant}."

    rspt_file = find_rspt_file('C:\\Users\\Model Shop\\Desktop') 
    if not rspt_file:
        return "No .rspt file found in the directory."

    with open(rspt_file, 'r') as file:
        variant_program = file.read()

    # Get existing thresholds from the database
    existing_thresholds = get_existing_thresholds(id_variant)

    # Generate variant thresholds based on the filtered variant program or use existing thresholds
    variant_thresholds = generate_variant_thresholds(variant_program, existing_thresholds)

    # Update the existing variant with the new variantProgram and variantThresholds
    update_variant_program_and_thresholds(id_variant, variant_program, variant_thresholds)
    
    return f"Variant {customer_variant} updated successfully."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update variant program and thresholds for a given customer variant.')
    parser.add_argument('customer_variant', type=str, help='Customer Variant to update')
    args = parser.parse_args()
    print(main(args.customer_variant))
