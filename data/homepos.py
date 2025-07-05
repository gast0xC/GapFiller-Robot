import socket
import time
import argparse
# Configuration for TCP/IP with IAI PLC
IP = '192.168.0.20'
PORT = 1337
BUFFER_SIZE = 1024  # Define the buffer size for sending

# Conversion table for hexadecimal digits to 4-bit binary representation
hex_to_bin = {
    '0': '0000', '1': '0001', '2': '0010', '3': '0011',
    '4': '0100', '5': '0101', '6': '0110', '7': '0111',
    '8': '1000', '9': '1001', 'A': '1010', 'B': '1011',
    'C': '1100', 'D': '1101', 'E': '1110', 'F': '1111'
}
def is_axis_free(response):
    response_str = response.decode('utf-8')  # Decode bytes to string

    # Extract substrings representing hexadecimal values
    byte10 = response_str[8:10]
    byte26 = response_str[24:26]
    byte42 = response_str[40:42]

    # Convert each hexadecimal digit to its 4-bit binary representation
    binary_byte10 = ''.join([hex_to_bin[digit] for digit in byte10])
    binary_byte26 = ''.join([hex_to_bin[digit] for digit in byte26])
    binary_byte42 = ''.join([hex_to_bin[digit] for digit in byte42])

    # Get the LSB of each byte
    lsb_byte10 = int(binary_byte10[-1])
    lsb_byte26 = int(binary_byte26[-1])
    lsb_byte42 = int(binary_byte42[-1])

    # Return 1 if any of the LSBs is 1, otherwise return 0
    return int(lsb_byte10 == 1 or lsb_byte26 == 1 or lsb_byte42 == 1)

def send_cmd(s, cmd_name, cmd):
    message_hex = cmd.replace('H', '')
    cmd_bytes = bytes.fromhex(message_hex)
    
    # Split the message into chunks of BUFFER_SIZE
    for i in range(0, len(cmd_bytes), BUFFER_SIZE):
        chunk = cmd_bytes[i:i + BUFFER_SIZE]
        s.sendall(chunk)
    
    response = s.recv(1024)
    print(f'Sent {cmd_name}:', message_hex)
    print('Received:', response)
    return response

def main(random):
    servoon = "21H39H39H32H33H32H30H37H31H40H40H0DH0AH"
    servooff = "21H39H39H32H33H32H30H37H30H40H40H0DH0AH"
    dispenseroff = "21H39H39H32H34H41H30H31H33H31H30H40H40H0DH0AH"
    homereturn = "21H39H39H32H33H33H30H37H30H32H30H30H32H30H40H40H0DH0AH"
    axisstatus = "21H39H39H32H31H32H30H37H40H40H0DH0AH"
    # Create socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((IP, PORT))
            send_cmd(s, 'ServoOn', servoon)
            send_cmd(s, 'DispenserOff', dispenseroff)
            send_cmd(s, 'HomeReturn', homereturn)
            while is_axis_free(send_cmd(s, "AxisStatusQuery", axisstatus)):
                time.sleep(0.5)
            send_cmd(s, 'ServoOff', servooff)
        except ConnectionRefusedError:
            print("Connection refused. Make sure the robot is running and listening on the specified port.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Random input for homepos.')
    parser.add_argument('random', type=str, help='random')
    args = parser.parse_args()
    main(args.random)
    

