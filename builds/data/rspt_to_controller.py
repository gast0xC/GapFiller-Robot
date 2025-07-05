import socket
import os
import mysql.connector
import argparse

# Configuration for TCP/IP with IAI PLC
IP = '192.168.0.20'
PORT = 1337

# Mapping dictionary for hex conversion
MAPPING = {
    '3AH': '41H',
    '3BH': '42H',
    '3CH': '43H',
    '3DH': '44H',
    '3EH': '45H',
    '3FH': '46H'
}

def pad_hex_to_custom_format(value, length):
    # Convert value to hex, remove '0x', pad it, and then convert to custom format
    hex_value = format(value, 'X')
    padded_hex = hex_value.zfill(length)
    return ''.join([convert_hex_to_custom_format(hex(int(char, 16))) for char in padded_hex])


def add_positions(processed_file, total_lines):
    positions = []
    for i in range(total_lines):
        # Extract the elements from the processed file line
        line_parts = processed_file[i].split(',')
        
        # Pad and convert '07' and '0020' to custom format
        constant_part = (
            pad_hex_to_custom_format(7, 2)   # 07 should be 30H37H
            #pad_hex_to_custom_format(20, 4) +  # 0020 should be 30H30H32H30H
            #pad_hex_to_custom_format(20, 4) +  # 0020 should be 30H30H32H30H
            #pad_hex_to_custom_format(20, 4)  # 0020 should be 30H30H32H30H
        )
        
        # Use the 2nd, 3rd, and 4th elements of the current line
        second_elem = line_parts[1]
        third_elem = line_parts[2]
        fourth_elem = line_parts[3]
        fiveth_elem = line_parts[4]
        sixth_elem = line_parts[5]
        seventh_elem = line_parts[6]
        
        # Create the position string and add it to the list
        position = constant_part + second_elem + third_elem + fourth_elem + fiveth_elem + sixth_elem + seventh_elem
        positions.append(position) 
    
    return ''.join(positions)

def filter_lines_with_decimals_from_content(content):
    lines = content.split('\n')
    decimal_lines = [line for line in lines if any('.' in word for word in line.split(','))]
    
    processed_lines = []
    for line in decimal_lines:
        parts = line.split(',')
        new_line = parts[0] + ',' # Add the first part and a comma
        for i in range(1, len(parts)):
            new_line += parts[i]
            if i < len(parts) - 1 and parts[i].strip().replace('.', '').isdigit() and parts[i + 1].strip().replace('.', '').isdigit():
                new_line += ','
        processed_lines.append(new_line.strip()) # Remove any trailing whitespace
    return processed_lines

def convert_hex_to_custom_format(hex_string):
    hex_string = hex_string[2:]
    result = ''.join(format(int('3' + char, 16), 'x') + 'H' for char in hex_string)
    pairs = [result.upper()[i:i+3] for i in range(0, len(result), 3)]
    transformed_pairs = [MAPPING.get(pair, pair) for pair in pairs]
    transformed_string = ''.join(transformed_pairs)
    return transformed_string

def pad_to_length(string, length, pad_char='30H'):
    return pad_char * (length - len(string)//3) + string

def process_file(file_content):
   
    output = filter_lines_with_decimals_from_content(file_content)

    if not output:
        print("No lines with decimals found.")
        return [], 0

    processed_file = []
    for line in output:
        parts = line.split(',')
        new_parts = []
        for i, part in enumerate(parts):
            try:
                clean_part = part.replace('.', '')
                element_hex = hex(int(clean_part))
                new_part = convert_hex_to_custom_format(element_hex)
                # Apply custom padding based on index
                if i == 0:
                    new_part = pad_to_length(new_part, 3)
                elif i in [1, 2, 3]:
                    new_part = pad_to_length(new_part, 4)
                else:
                    new_part = pad_to_length(new_part, 8)
                new_parts.append(new_part)
            except ValueError:
                if i == 0:
                    new_parts.append(pad_to_length(part.strip(), 3))
                else:
                    new_parts.append(pad_to_length(part.strip(), 8))
        processed_file.append(','.join(new_parts))
    
    # Printing the final CSV content
    for line in processed_file:
        print(line)
    
    total_lines = len(processed_file)
    return processed_file, total_lines

def construct_message(header, station, message_id, content, sc, processed_file, total_lines):
    # Convert header to hexadecimal notation with H
    header_hex = f"{ord(header):02X}H"
    # Convert station, message_id, and SC to hexadecimal notation with H
    station_hex = ''.join([f"{ord(char):02X}H" for char in station])
    message_id_hex = ''.join([f"{ord(char):02X}H" for char in message_id])
    content_hex = ''.join([f"{ord(char):02X}H" for char in content])
    sc_hex = ''.join([f"{ord(char):02X}H" for char in sc])
    # Fixed CR and LF
    cr_hex = "0DH"
    lf_hex = "0AH"
    # Get all positions
    all_positions_hex = add_positions(processed_file, total_lines)
    # Concatenate all parts
    message = header_hex + station_hex + message_id_hex + content_hex + all_positions_hex + sc_hex + cr_hex + lf_hex
    return message

def pad_to_three_chars(value):
    return str(value).zfill(3)

def send_cmd(s, cmd_name, cmd):
    message_hex = cmd.replace('H', '')
    cmd_bytes = bytes.fromhex(message_hex)
    s.sendall(cmd_bytes)
    response = s.recv(1024)
    print(f'Sent {cmd_name}:', message_hex)
    print('Received:', response)
    return response

def get_rspt_file_from_db(variant):
    conn = mysql.connector.connect(
        host='136.16.182.41',
        port=3377,
        user='jcontramestre',
        password='904OBol6PY0mcIpN',
        database='GapfillerRobot'
    )
    
    cursor = conn.cursor()
    query = "SELECT variantProgram FROM Variants WHERE variantName = %s"
    cursor.execute(query, (variant,))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if result:
        return result[0] # Return the .rspt file content as a string
    else:
        raise ValueError(f"No variant found with name {variant}")

def main(variant):
    try:
        file_content = get_rspt_file_from_db(variant)
    except ValueError as e:
        print(f"Error: {str(e)}")
        return str(e), 0
    
    processed_file, total_lines = process_file(file_content)

    header = '!'
    station = '99'
    message_id = '244'
    content = '001' + pad_to_three_chars(total_lines)
    sc = '@@'
    print("Total lines in processed file:", total_lines)
    print(total_lines)  # Ensure this line outputs the value alone for LabView
    message = construct_message(header, station, message_id, content, sc, processed_file, total_lines)
    print(message)

    # Create socket object
   # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
   #     try:
   #         s.connect((IP, PORT))
   #         send_cmd(s, 'OverwriteController', message)
   #     except ConnectionRefusedError:
   #         print("Connection refused. Make sure the robot is running and listening on the specified port.")
   #     except Exception as e:
   #         print(f"An error occurred: {str(e)}")
    total_lines = total_lines - 3
    print(total_lines)
    return str(total_lines)

if __name__ == "__main__":
    #parser = argparse.ArgumentParser(description="Process variant .rspt file and send command to PLC.")
    #parser.add_argument('variant', type=str, help="The variant name to process.")
    #args = parser.parse_args()
    variant = "AMG_EA_B2"
    main(variant)
    #main(args.variant)
