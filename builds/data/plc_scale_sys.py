import threading
import time
import socket
import serial
import queue
import logging
import re
import argparse

# Configure the logging system
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Configuration for TCP/IP with IAI PLC
ip = '192.168.0.20'
port = 1337

# Commands list
commands = {
    "cmd_AxisStatusQuery": "21H39H39H32H31H32H30H37H40H40H0DH0AH",
    "cmd_ServoOn": "21H39H39H32H33H32H30H37H31H40H40H0DH0AH",
    "cmd_ServoOff": "21H39H39H32H33H32H30H37H30H40H40H0DH0AH",
    "cmd_HomeReturn": "21H39H39H32H33H33H30H37H30H32H30H30H32H30H40H40H0DH0AH",
    "cmd_DispenserStartDirectOn": "21H39H39H32H34H41H30H31H33H31H31H40H40H0DH0AH",
    "cmd_DispenserStartDirectOff": "21H39H39H32H34H41H30H31H33H31H30H40H40H0DH0AH",
    "cmd_VCUbit1On": "21H39H39H32H34H41H30H31H33H32H31H40H40H0DH0AH",
    "cmd_VCUbit1Off": "21H39H39H32H34H41H30H31H33H32H30H40H40H0DH0AH",
    "cmd_VCUbit2On": "21H39H39H32H34H41H30H31H33H33H31H40H40H0DH0AH",
    "cmd_VCUbit2Off": "21H39H39H32H34H41H30H31H33H33H30H40H40H0DH0AH",
    "cmd_VCUbit3On": "21H39H39H32H34H41H30H31H33H34H31H40H40H0DH0AH",
    "cmd_VCUbit3Off": "21H39H39H32H34H41H30H31H33H34H30H40H40H0DH0AH",
    "cmd_SecurityBarsSensor": "21H39H39H32H30H42H30H30H30H30H30H30H30H46H40H40H0DH0AH",
    "cmd_ResetTriggerOn" : "21H39H39H32H34H41H30H31H33H35H31H40H40H0DH0AH",  
    "cmd_ResetTriggerOff" : "21H39H39H32H34H41H30H31H33H35H30H40H40H0DH0AH"
}

# Positions list
positions = {
    "position1": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H31H40H40H0DH0AH",
    "position2": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H32H40H40H0DH0AH",
    "position3": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H33H40H40H0DH0AH",
    "position4": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H34H40H40H0DH0AH",
    "position5": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H35H40H40H0DH0AH",
    "position6": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H36H40H40H0DH0AH",
    "position7": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H37H40H40H0DH0AH",
    "position8": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H38H40H40H0DH0AH",
    "position9": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H39H40H40H0DH0AH",
    "position10": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H41H40H40H0DH0AH",
    "position11": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H42H40H40H0DH0AH",
    "position12": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H43H40H40H0DH0AH",
    "position13": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H44H40H40H0DH0AH",
    "position14": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H45H40H40H0DH0AH",
    "position15": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H30H46H40H40H0DH0AH",
    "position16": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H30H40H40H0DH0AH",
    "position17": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H31H40H40H0DH0AH",
    "position18": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H32H40H40H0DH0AH",
    "position19": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H33H40H40H0DH0AH",
    "position20": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H34H40H40H0DH0AH",
    "position21": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H35H40H40H0DH0AH",
    "position22": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H36H40H40H0DH0AH",
    "position23": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H37H40H40H0DH0AH",
    "position24": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H38H40H40H0DH0AH",
    "position25": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H39H40H40H0DH0AH",
    "position26": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H41H40H40H0DH0AH",
    "position27": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H42H40H40H0DH0AH",
    "position28": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H43H40H40H0DH0AH",
    "position29": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H44H40H40H0DH0AH",
    "position30": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H45H40H40H0DH0AH",
    "position31": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H31H46H40H40H0DH0AH", 
    "position32": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H30H40H40H0DH0AH",
	"position33": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H31H40H40H0DH0AH",
	"position34": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H32H40H40H0DH0AH",
	"position35": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H33H40H40H0DH0AH",
	"position36": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H34H40H40H0DH0AH",
	"position37": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H35H40H40H0DH0AH",
	"position38": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H36H40H40H0DH0AH",
	"position39": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H37H40H40H0DH0AH",
	"position40": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H38H40H40H0DH0AH",
	"position41": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H39H40H40H0DH0AH",
	"position42": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H41H40H40H0DH0AH",
	"position43": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H42H40H40H0DH0AH",
	"position44": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H43H40H40H0DH0AH",
	"position45": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H44H40H40H0DH0AH",
	"position46": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H45H40H40H0DH0AH",
	"position47": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H32H46H40H40H0DH0AH",
	"position48": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H33H30H40H40H0DH0AH",
	"position49": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H33H31H40H40H0DH0AH",
	"position50": "21H39H39H32H33H37H30H37H30H30H30H30H30H30H30H30H30H30H30H30H30H33H32H40H40H0DH0AH"
}

# Conversion table for hexadecimal digits to 4-bit binary representation
hex_to_bin = {
    '0': '0000', '1': '0001', '2': '0010', '3': '0011',
    '4': '0100', '5': '0101', '6': '0110', '7': '0111',
    '8': '1000', '9': '1001', 'A': '1010', 'B': '1011',
    'C': '1100', 'D': '1101', 'E': '1110', 'F': '1111'
}

# Configuration parameters for the serial communication
SERIAL_PORT = 'COM4'
BAUD_RATE = 9600
TIMEOUT = 1  # Read timeout in seconds

# Flag to signal thread termination
stop_event = threading.Event()

# Event to signal start of thread_two_func
start_event = threading.Event()

def open_serial_port(port, baud_rate, timeout):
    """
    Open the serial port with the specified parameters.
    
    Args:
        port (str): The serial port to open (e.g., '/dev/ttyUSB0').
        baud_rate (int): The baud rate for the serial communication.
        timeout (float): The timeout for the serial communication in seconds.
    
    Returns:
        serial.Serial: The opened serial port object, or None if an error occurs.
    """
    try:
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        ser.flush()  # Flush both input and output
        logging.info(f"Opened serial port: {ser.name}")
        return ser
    except serial.SerialException as e:
        logging.error(f"Error opening serial port {port}: {e}")
        return None

def send_data(ser, data):
    """
    Send data through the serial port.
    
    Args:
        ser (serial.Serial): The serial port object.
        data (str): The data to send.
    """
    if ser is None:
        logging.error("Cannot send data: serial port is not open")
        return

    try:
        ser.write(data.encode())
        logging.debug(f"Sent data: {data}")
    except serial.SerialTimeoutException as e:
        logging.error(f"Timeout error sending data: {e}")
    except serial.SerialException as e:
        logging.error(f"Serial error sending data: {e}")

def receive_data(ser):
    """
    Receive data from the serial port and extract the weight.
    
    Args:
        ser (serial.Serial): The serial port object.
    
    Returns:
        float: The received weight in grams, or None if no valid data is received.
    """
    try:
        # Read a line from the serial port
        raw_data = ser.readline().decode('utf-8', errors='ignore').strip()

        if raw_data:
            logging.debug(f"Raw data received from scale: {raw_data}")
            
            # Extract the unit
            unit_match = re.search(r'(g|kg)$', raw_data)
            if unit_match:
                unit = unit_match.group()
                logging.debug(f"Unit: {unit}")
            else:
                logging.debug("No unit found in received data")
                return None

            # Extract the numeric part, including an optional negative sign
            match = re.search(r'-?\d+(\.\d+)?', raw_data)
            if match:
                numeric_part = match.group()
                logging.debug(f"Extracted numeric part: {numeric_part}")

                try:
                    weight = float(numeric_part)
                    if unit == 'g':
                        return weight
                    else:
                        return weight * 1000  # Convert kg to grams
                except ValueError:
                    logging.error(f"Failed to convert numeric part to float: {numeric_part}")
                    return None
            else:
                logging.debug("No numeric part found in received data")
                return None
        else:
            logging.debug("No data received from scale")
            return None
    except serial.SerialException as e:
        logging.error(f"Error receiving data: {e}")
        return None



def close_serial_port(ser):
    """
    Close the serial port.
    
    Args:
        ser (serial.Serial): The serial port object.
    """
    if ser is not None and hasattr(ser, 'close'):
        try:
            ser.close()
            logging.info("Closed serial port")
        except serial.SerialException as e:
            logging.error(f"Error closing serial port: {e}")
    else:
        logging.error("Invalid serial port object")

def send_cmd(s, cmd_name, cmd):
    """
    Send a command to a PLC (Programmable Logic Controller) via a socket connection and log the response.
    
    Args:
        s (socket.socket): The socket object used for communication.
        cmd_name (str): The name of the command being sent, used for logging purposes.
        cmd (str): The command to be sent, represented as a hexadecimal string.
    
    Returns:
        bytes: The response received from the PLC.
    """
    try:
        # Remove 'H' from the command and convert to bytes
        cmd_bytes = bytes.fromhex(cmd.replace('H', ''))
        s.sendall(cmd_bytes)
        response = s.recv(1024)
        logging.info(f'Sent {cmd_name}: {cmd_bytes.hex()}')
        logging.info(f'Received: {response.hex()}')
        return response
    except (socket.error, ValueError) as e:
        logging.error(f"Error sending command {cmd_name}: {e}")
        return b''

def control_check(s):
    """
    Check the status of the security bars and axis. 

    Args:
        s (socket): The socket object for communication with the PLC.
    
    Returns:
        int: 1 if any axis LSB is 1 (axis not free), 0 if all axis LSBs are 0 (axis free), 
             and stop_event is set if security bars are triggered.
    """
    try:
        # Check security bars sensor status
        response_sec = send_cmd(s, "cmd_SecurityBarsSensor", commands["cmd_SecurityBarsSensor"])
        response_sec_str = response_sec.decode('ascii')
        
        if len(response_sec_str) >= 16:
            # Check 16th character for security bars
            if response_sec_str[16] != '8':
                return -1  # Stop system if security bars are triggered

        # Check axis status
        response_axis = send_cmd(s, "cmd_AxisStatusQuery", commands["cmd_AxisStatusQuery"])
        response_axis_str = response_axis.decode('utf-8')

        # List of indexes where the relevant bytes are located
        indexes = [8, 24, 40]

        # Check if any of the LSBs is 1 (axis not free)
        for index in indexes:
            byte_str = response_axis_str[index:index+2]  # Extract 2-character substring
            byte_value = int(byte_str, 16)  # Convert hex string to integer
            if byte_value & 1:  # Check LSB
                return 1  # Axis not free (any LSB is 1)

        return 0  # All axis LSBs are 0 (axis is free)
    
    except (UnicodeDecodeError, ValueError, IndexError) as e:
        logging.error(f"Error processing response: {e}")
        return 0


def stop_sys(s):
    """
    Sends the command to stop the motors and dispenser and set stop_event.
    """
    try:
        logging.info("Starting graceful shutdown...")
        if s:
            send_cmd(s, "cmd_ServoOff_STOPSYS", commands["cmd_ServoOff"])  # Stop motors
            send_cmd(s, "cmd_DispenserStartDirectOff_STOPSYS", commands["cmd_DispenserStartDirectOff"])
            
            send_cmd(s, "cmd_ResetTriggerOn_STOPSYS", commands["cmd_ResetTriggerOn"])
            time.sleep(1)
            send_cmd(s, "cmd_ResetTriggerOff_STOPSYS", commands["cmd_ResetTriggerOff"])
           # s.close()  no need to be here
            #logging.info("Socket connection closed.")
    except Exception as e:
        logging.error(f"Error during graceful shutdown: {e}")
    finally:
        logging.info("Shutdown process complete.")
        stop_event.set()  # Signal threads to stop


def wait_for_axis_free(s):
    """
    Continuously checks the axis status and handles the different statuses.

    Args:
        s (socket): The socket object for communication with the PLC.
    
    Returns:
        bool: Returns False if a critical stop is detected (status -1),
              Returns True when axis is free (status 0).
    """
    while True:
        status = control_check(s)
        
        if status == -1:
            stop_sys(s)
            logging.info("Critical stop detected. Returning to main loop.")
            return False  # Critical stop, go back to the main loop
        
        elif status == 0:
            return True  # Axis is free, proceed to next command
        
        else:
            time.sleep(0.5)  # Continue waiting if axis is not free


def thread_one_func(sem1, sem2, threshold_queue, phase):
    """
    The main function for thread one, which handles the PLC communication and axis movements.
    
    Args:
        sem1 (threading.Semaphore): Semaphore for synchronization with thread two.
        sem2 (threading.Semaphore): Semaphore for synchronization with thread two.
        threshold_queue (queue.Queue): Queue to receive threshold values from thread two.
    """
    # Create socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((ip, port))
            send_cmd(s, "cmd_ResetSecurityInterrupt", commands["cmd_ResetTriggerOn"])
            if not wait_for_axis_free(s): return  
            send_cmd(s, "cmd_ServoOn", commands["cmd_ServoOn"])
            if phase == 1:
                time.sleep(0.5)  # Added delay
                send_cmd(s, "cmd_HomeReturn", commands["cmd_HomeReturn"])
                send_cmd(s, "cmd_VCUbit1On", commands["cmd_VCUbit1On"])
                send_cmd(s, "cmd_VCUbit2Off", commands["cmd_VCUbit2Off"])
                send_cmd(s, "cmd_VCUbit3Off", commands["cmd_VCUbit3Off"])
                
                #####################################################################################################
                # Wait for axis to be free (or handle a critical stop)
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position1", positions["position1"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn1", commands["cmd_DispenserStartDirectOn"])
                time.sleep(12)
                send_cmd(s, "cmd_DispenserStartDirectOff1", commands["cmd_DispenserStartDirectOff"])
                time.sleep(5)
                send_cmd(s, "position2", positions["position2"])
                
                
                
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position3", positions["position3"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put(0.5)
                send_cmd(s, "cmd_DispenserStartDirectOn2", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position4", positions["position4"])
                if not wait_for_axis_free(s): return  

                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff2", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position3", positions["position3"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position5", positions["position5"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put(0.5)
                send_cmd(s, "cmd_DispenserStartDirectOn3", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position6", positions["position6"])
                if not wait_for_axis_free(s): return  
                
                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff3", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position5", positions["position5"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position7", positions["position7"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put(0.5)
                send_cmd(s, "cmd_DispenserStartDirectOn4", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position8", positions["position8"])
                if not wait_for_axis_free(s): return  
                
                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff4", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position7", positions["position7"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position9", positions["position9"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put(0.5)
                send_cmd(s, "cmd_DispenserStartDirectOn5", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position10", positions["position10"])
                if not wait_for_axis_free(s): return  
                
                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff5", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position9", positions["position9"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position11", positions["position11"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put(0.5)
                send_cmd(s, "cmd_DispenserStartDirectOn6", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position12", positions["position12"])
                if not wait_for_axis_free(s): return  

                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff6", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position11", positions["position11"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position13", positions["position13"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put(1)
                send_cmd(s, "cmd_DispenserStartDirectOn7", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position14", positions["position14"])
                if not wait_for_axis_free(s): return  
                
                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff7", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position13", positions["position13"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position15", positions["position15"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put(1)
                send_cmd(s, "cmd_DispenserStartDirectOn8", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position16", positions["position16"])
                if not wait_for_axis_free(s): return  

                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff8", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position15", positions["position15"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position17", positions["position17"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put(1)
                send_cmd(s, "cmd_DispenserStartDirectOn9", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position18", positions["position18"])
                if not wait_for_axis_free(s): return  
                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff9", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position17", positions["position17"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position19", positions["position19"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()

                threshold_queue.put(0.5)
                send_cmd(s, "cmd_DispenserStartDirectOn10", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position20", positions["position20"])
                if not wait_for_axis_free(s): return  
                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff10", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position19", positions["position19"])

                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position21", positions["position21"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put(0.5)
                send_cmd(s, "cmd_DispenserStartDirectOn11", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position22", positions["position22"])
                if not wait_for_axis_free(s): return  
                
                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff11", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position21", positions["position21"])
                if not wait_for_axis_free(s): return       
                send_cmd(s, "position35", positions["position35"])  
            if phase == 2:
                time.sleep(0.5)  # Added delay
                send_cmd(s, "cmd_HomeReturn", commands["cmd_HomeReturn"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position1", positions["position1"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn1", commands["cmd_DispenserStartDirectOn"])
                time.sleep(12)
                send_cmd(s, "cmd_DispenserStartDirectOff1", commands["cmd_DispenserStartDirectOff"])
                send_cmd(s, "position2", positions["position2"])

                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position23", positions["position23"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn12", commands["cmd_DispenserStartDirectOn"])
                sem1.release()
                threshold_queue.put(1)
                send_cmd(s, "position24", positions["position24"])
                if not wait_for_axis_free(s): return  

                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff12", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position23", positions["position23"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position25", positions["position25"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn13", commands["cmd_DispenserStartDirectOn"])
                sem1.release()
                threshold_queue.put(1)
                send_cmd(s, "position26", positions["position26"])
                if not wait_for_axis_free(s): return  

                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff13", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position25", positions["position25"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position27", positions["position27"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn14", commands["cmd_DispenserStartDirectOn"])
                sem1.release()
                threshold_queue.put(1)
                send_cmd(s, "position28", positions["position28"])
                if not wait_for_axis_free(s): return  

                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff14", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position27", positions["position27"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position29", positions["position29"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn15", commands["cmd_DispenserStartDirectOn"])
                sem1.release()
                threshold_queue.put(1)
                send_cmd(s, "position30", positions["position30"])
                if not wait_for_axis_free(s): return  

                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff15", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position29", positions["position29"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position31", positions["position31"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn16", commands["cmd_DispenserStartDirectOn"])
                sem1.release()
                threshold_queue.put(1)
                send_cmd(s, "position32", positions["position32"])
                if not wait_for_axis_free(s): return  

                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff16", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position31", positions["position31"])
                #####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position33", positions["position33"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn16", commands["cmd_DispenserStartDirectOn"])
                sem1.release()
                threshold_queue.put(1)
                send_cmd(s, "position34", positions["position34"])
                if not wait_for_axis_free(s): return  

                
                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff16", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position33", positions["position33"])
                if not wait_for_axis_free(s): return       
                send_cmd(s, "position35", positions["position35"])  

            if not wait_for_axis_free(s): return     
            send_cmd(s, "cmd_HomeReturn", commands["cmd_HomeReturn"])
            if not wait_for_axis_free(s): return  
            send_cmd(s, "cmd_ServoOff", commands["cmd_ServoOff"])
            
        except ConnectionRefusedError:
            print("Connection refused. Make sure the robot is running and listening on the specified port.")
        except Exception as e:
            print("An error occurred:", e)
        finally:
            # Signal the termination flag
            s.close()
            if not stop_event.is_set():
                
                stop_event.set()

def thread_two_func(ser, sem1, sem2, threshold_queue):
    """
    The main function for thread two, which handles the serial communication with the scale and adjusts for overread.

    Args:
        ser (serial.Serial): Serial object for communication with the scale.
        sem1 (threading.Semaphore): Semaphore for synchronization with thread one.
        sem2 (threading.Semaphore): Semaphore for synchronization with thread one.
        threshold_queue (queue.Queue): Queue to send threshold values to thread one.
    """
    if ser is None:
        return
    
    start_event.wait()  # Wait for signal to start
    overread_factor = 4.8  # Pressure factor - Hardcoded or configurable (?)
    default_threshold = 0.8  # Default threshold value in grams

    # overread_factor = scale reading / actual reading

    
    while not stop_event.is_set():
        sem1.acquire()  # Block until sem1 is released
        ser.flushInput()
        # Send "TI" (tare) command to tare the scale
        send_data(ser, "TI\r\n")  
        
        try:
            # Update the current threshold if there is a new value in the queue
            try:
                current_threshold = threshold_queue.get_nowait()
            except queue.Empty:
                current_threshold = default_threshold  # Use default threshold if none provided
            
            # Calculate preemptive threshold to account for overread
            preemptive_threshold = current_threshold + overread_factor # + or * ?
            logging.debug(f"{preemptive_threshold} current th * overread factor")
            weightt2 = 0  # Initialize weight to 0
            weight_received = False
           # a = 0
            # Loop to repeatedly send "SI" and check weight
            while not weight_received:
                if stop_event.is_set():
                    break  # Exit loop if termination is requested
                
                # Request current weight with "SI"
                send_data(ser, "SI\r\n")
                weightt2 = receive_data(ser)  # Receive weight in grams
                ser.flushInput()
                
                logging.debug(f"Received weight: {weightt2}")
                
                if weightt2 is not None and (0 < weightt2 < 70):
                    # Check if weight exceeds the preemptive threshold
                    if weightt2 > preemptive_threshold:
                        logging.debug(f"Weight {weightt2} exceeds the preemptive threshold {preemptive_threshold}. Releasing sem2.")
                        sem2.release()  # Release sem2 when weight exceeds preemptive threshold
                        weight_received = True
                #if weightt2 > 6000:
               #     a = a +1
               #     if a > 3:
                        
                time.sleep(0.05)
        except serial.SerialException as e:
            logging.error(f"Error during serial communication: {e}")
            break  # Exit loop in case of serial error
    
    # Optional: Put final weight into the result queue if needed
    # result_queue.put(weight)




def main(phase):
    """
    The main function to coordinate the operations of two threads:
    one for handling PLC communication and axis movements, and the other 
    for handling serial communication with a scale to measure weight.

    It initializes the serial port, semaphores, and queues for inter-thread 
    communication. It then starts the threads, waits for them to finish, and 
    ensures proper termination and cleanup.
    """
    try:
        start_time = time.time()
        timeout_duration = 10  
        # Open the serial port
        ser = open_serial_port(SERIAL_PORT, BAUD_RATE, TIMEOUT)
        if not ser:
            logging.error("Failed to open serial port.")
            return
        #weight = 1
       # if phase == 1:
            #while (weight != 0):
            #send_data(ser, "ZI\r\n")
                #time.sleep(0.5)
                #send_data(ser, "SI\r\n")
                #weight = receive_data(ser)
        stop_event.clear()
        initialWeight = 0
        finalWeight = 0
        res = 0
        if phase == 1:
            while initialWeight < 6000:
                if time.time() - start_time > timeout_duration:
                    logging.info("Timeout reached during weight measurement. Exiting program.")
                    return
                send_data(ser, "SI\r\n")
                initialWeight = receive_data(ser)
                time.sleep(0.5)
            logging.debug(f"initialWeight data in grams phase1: {initialWeight}")
        
        
        # enquanto o weight nao for maior que 6000 g, esperar, quando for, obter esse valor


        # Semaphores for synchronization
        sem1 = threading.Semaphore(0)
        sem2 = threading.Semaphore(0)
        threshold_queue = queue.Queue()

        # Create and start threads
        thread_one = threading.Thread(target=thread_one_func, args=(sem1, sem2, threshold_queue, phase))
        thread_two = threading.Thread(target=thread_two_func, args=(ser, sem1, sem2, threshold_queue))
        
        thread_one.start()
        thread_two.start()
        
        start_event.set()  # Signal thread_two_func to start

        # Wait for thread one to finish
        thread_one.join()
        if not stop_event.is_set():
            stop_event.set()
        # Signal thread two to terminate
        #stop_event.set()
        sem1.release()  # Ensure thread two can finish if waiting

        # Wait for thread two to finish
        thread_two.join()
        
        #obter os dados depois de tirar o compressor da balanca e fazer a diferenca do initialWeight com o finalWeight
        # sendo que e' necessario tirar a quantidade do IMS
        if phase == 2:
            send_data(ser, "TI\r\n")  # Send initial "TI" command to tare the scale
            while(finalWeight < 6000): #after 2 pr 3 SI, even though we tared and value is 0, the SI will get the last value when the scale was zeroed
                send_data(ser, "SI\r\n")
                finalWeight = receive_data(ser)
                #print(finalWeight)
                time.sleep(0.5)
            #send_data(ser, "SI\r\n")
            #finalWeight = receive_data(ser)
        #logging.debug(f"finalWeight data in grams: {finalWeight}")
        #logging.debug(f"initialWeight data in grams: {initialWeight}")
        #res = finalWeight - initialWeight    #initialWeight + finalWeight
        #logging.debug(f"res data in grams: {res}")
          #sendo que o resultado o IMS e' 20g mais ou menos
        #logging.debug(f"threads finised?")
        #file_path = 'C:\\Users\\Model Shop\\Desktop\\builds\\data\\saved_result.txt'
        file_path = 'C:\\Users\\jcontram\\Desktop\\gapfeelings\\data\\saved_result.txt'
        if phase == 1:
            with open(file_path, 'w') as file:
                file.write(str(initialWeight))
                logging.debug(f"initialWeight phase1: {initialWeight}")  
        if phase == 2:
            with open(file_path, 'r') as file:
                initialWeightaux = float(file.read())
                logging.debug(f"initialWeightaux phase2: {initialWeightaux}")  
            with open(file_path, 'w') as file:
                pass
            res = finalWeight - initialWeightaux - 8.6 # o IMS e' entre [8.6 ; 8.8]
            logging.debug(f"Final weight res = finalWeight - initialWeight - 8,7: {res}") # 8.65
            return res  
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    
    finally:
        # Ensure the serial port is closed and stop_event is cleared
        if ser:
            close_serial_port(ser)
        #stop_event.clear()
        logging.debug("Program finished and serial port closed.")

    # Get the final auxWeight from thread two
    #auxWeight = result_queue.get()
    #logging.info(f"Final accumulated weight (should be lighter than the real weight): {auxWeight}")
    #logging.info("Both threads have finished execution.")
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Set up argument parsing
    #parser = argparse.ArgumentParser(description='LabVIEW input handler')
    #parser.add_argument('phase', type=int, help='Integer input from LabVIEW')
    #args = parser.parse_args()
    phase = 2 
    # Call main with the parsed argument
    #main(args.phase)
    main(phase)
    #time.sleep(20)
    #phase2 = 2
    #main(phase2)
