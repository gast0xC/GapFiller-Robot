import mysql.connector
import os
import glob
import argparse
from mysql.connector import connection

def connect_to_database(database: str) -> connection.MySQLConnection:
    """
    Establish a connection to the specified MySQL database.

    Args:
        database (str): Name of the database to connect to.

    Returns:
        connection.MySQLConnection: A MySQL connection object.
    """
    return mysql.connector.connect(
        host='136.16.182.41',
        port=3377,
        user='jcontramestre',
        password='904OBol6PY0mcIpN',
        database=database
    )

def get_compressor_details(serial_number: str) -> tuple:
    """
    Retrieve customer and customer variant details for a given compressor serial number.

    Args:
        serial_number (str): The serial number of the compressor.

    Returns:
        tuple: A tuple containing the customer and customer variant, or None if not found.
    """
    query = """
        SELECT Customer, Customer_Variant
        FROM Compressor_Build_Header
        WHERE Serial_Number = %s
    """
    with connect_to_database('CompressorDB') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (serial_number,))
            result = cursor.fetchone()
    return result

def check_variant_existence(customer_variant: str) -> tuple:
    """
    Check if a customer variant exists in the database.

    Args:
        customer_variant (str): The name of the customer variant to check.

    Returns:
        tuple: A tuple containing the variant ID and variant program if found, or None if not found.
    """
    query = """
        SELECT idVariant, variantProgram
        FROM Variants
        WHERE variantName = %s
    """
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (customer_variant,))
            result = cursor.fetchone()
    return result

def create_new_variant(customer_variant: str, variant_program: str, variant_thresholds: str) -> None:
    """
    Create a new customer variant in the database.

    Args:
        customer_variant (str): The name of the customer variant.
        variant_program (str): The program associated with the variant.
        variant_thresholds (str): The thresholds associated with the variant.

    Returns:
        None
    """
    query = """
        INSERT INTO Variants (variantName, variantProgram, variantThresholds)
        VALUES (%s, %s, %s)
    """
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (customer_variant, variant_program, variant_thresholds))
            conn.commit()

def find_rspt_file(directory: str) -> str:
    """
    Find the first .rspt file in the given directory.

    Args:
        directory (str): The directory to search in.

    Returns:
        str: Path to the first .rspt file if found, otherwise None.
    """
    rspt_files = glob.glob(os.path.join(directory, '*.rspt'))
    return rspt_files[0] if rspt_files else None

def filter_lines_with_decimals_from_content(content: str) -> list:
    """
    Filter lines from content that contain decimal numbers.

    Args:
        content (str): The content to filter.

    Returns:
        list: A list of filtered lines containing decimal numbers.
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

def generate_variant_thresholds(variant_program: str) -> str:
    """
    Generate variant thresholds from the variant program content.

    Args:
        variant_program (str): The content of the variant program.

    Returns:
        str: Generated thresholds as a string.
    """
    filtered_lines = filter_lines_with_decimals_from_content(variant_program)
    total_lines = len(filtered_lines)
    num_thresholds = total_lines // 2
    thresholds = "\n".join([f"{i+1},0.3" for i in range(num_thresholds)])
    return thresholds

def main(serial_number: str) -> str:
    """
    Main function to process compressor details and update variants.

    Args:
        serial_number (str): The serial number of the compressor.

    Returns:
        str: The customer variant or an error message if details are not found.
    """
    details = get_compressor_details(serial_number)
    if details:
        customer, customer_variant = details
        
        # Check if the Customer Variant exists in the Variants table
        variant_details = check_variant_existence(customer_variant)
        #IF THE VARIANT EXISTS, NO NEED TO DO THE THRESHOLDS OR THE RSPT FILE
        rspt_file = find_rspt_file('C:\\Users\\jcontram\\Desktop')  # Update the path as necessary
        #rspt_file = find_rspt_file('C:\\Users\\Model Shop\\Desktop') 
        if rspt_file:
            with open(rspt_file, 'r') as file:
                variant_program = file.read()

            if not variant_details:
                # Generate variant thresholds based on the filtered variant program
                variant_thresholds = generate_variant_thresholds(variant_program)

                # Create a new variant only if it doesn't exist
                create_new_variant(customer_variant, variant_program, variant_thresholds)

        return customer_variant
    else:
        return "No details found for the given Serial Number."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process compressor details and update variants.')
    parser.add_argument('serial_number', type=str, help='Serial Number of the compressor')
    args = parser.parse_args()
    print(main(args.serial_number))