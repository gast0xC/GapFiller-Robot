import mysql.connector
import re
import os
from typing import Optional, Tuple, List

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

def get_variant_id(customer_variant: str) -> Optional[int]:
    """
    Retrieve the ID of a variant from the database based on its name.

    Args:
        customer_variant (str): The name of the variant to look up.

    Returns:
        Optional[int]: The ID of the variant if found, otherwise None.
    """
    query = """
        SELECT idVariant
        FROM Variants
        WHERE variantName = %s
    """
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (customer_variant,))
            result = cursor.fetchone()
    return result[0] if result else None

def get_variant_thresholds(id_variant: int) -> Optional[str]:
    """
    Retrieve the variant thresholds from the database based on variant ID.

    Args:
        id_variant (int): The ID of the variant to look up.

    Returns:
        Optional[str]: The variant thresholds as a string if found, otherwise None.
    """
    query = """
        SELECT variantThresholds
        FROM Variants
        WHERE idVariant = %s
    """
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (id_variant,))
            result = cursor.fetchone()
    return result[0] if result else None

def parse_variant_thresholds(variant_thresholds_text: str) -> Tuple[int, List[float]]:
    """
    Parse the variant thresholds from the provided text and calculate the number of data points.

    Args:
        variant_thresholds_text (str): The variant thresholds in text format.

    Returns:
        Tuple[int, List[float]]: A tuple containing the number of data points and a list of thresholds.
    """
    lines = variant_thresholds_text.strip().split('\n')
    thresholds = [float(line.split(',')[1]) for line in lines]
    num_points = int(lines[-1].split(',')[0]) * 2
    return num_points, thresholds

def generate_commands(num_points: int, thresholds: List[float], phase: int) -> List[str]:
    """
    Generate a list of command strings for the specified phase based on number of points and thresholds.

    Args:
        num_points (int): The total number of data points.
        thresholds (List[float]): The list of thresholds for each data point.
        phase (int): The phase to generate commands for (1 or 2).

    Returns:
        List[str]: A list of command strings.
    
    Raises:
        ValueError: If the phase is not 1 or 2.
    """
    commands_list = []
    if num_points > 12:
        phase_1_end = num_points - 12
    else:
        phase_1_end = num_points

    phase_2_start = phase_1_end + 1

    # Ensure we skip the first 2 points and the last point
   # start_point = max(3, 1 if phase == 1 else phase_2_start)
   # end_point = num_points - 1

    if phase == 1:
        start_point = 1  # Skipping the first 2 points
        end_point = phase_1_end
    elif phase == 2:
        start_point = phase_2_start
        end_point = num_points   # Skipping the last point
    else:
        raise ValueError("Invalid phase value. Use 1 or 2.")

    print("##############phase: ", phase)
    print("num points ", num_points)
    print("phase 1 end " ,phase_1_end)
    print("phase 2 start", phase_2_start)
    print("start point", start_point)
    print("end point: ", end_point)


    # Iterate through points, skipping the last point
    for i in range(start_point, end_point + 1, 2):
        next_i = i + 1
        if next_i > end_point:
            break
        commands_list.append(f"""#####################################################################################################
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position{i + 2}", positions["position{i + 2}"])
                if not wait_for_axis_free(s): return  
                
                sem1.release()
                threshold_queue.put({thresholds[(i - 1) // 2]})
                send_cmd(s, "cmd_DispenserStartDirectOn{i // 2 + 1}", commands["cmd_DispenserStartDirectOn"])
                send_cmd(s, "position{next_i + 2}", positions["position{next_i + 2}"])
                if not wait_for_axis_free(s): return  

                sem2.acquire()
                send_cmd(s, "cmd_DispenserStartDirectOff{i // 2 + 1}", commands["cmd_DispenserStartDirectOff"])
                time.sleep(1)
                send_cmd(s, "position{i + 2}", positions["position{i + 2}"])
                """)
        
    return commands_list


def generate_thread_func_script(file_path, num_points, thresholds):
    """
    Generate and update the thread function script based on number of points and thresholds.

    Args:
        file_path (str): The path to the script file to be updated.
        num_points (int): The total number of data points.
        thresholds (List[float]): The list of thresholds for each data point.
    """
    phase_1_commands = generate_commands(num_points, thresholds, phase=1)
    phase_2_commands = generate_commands(num_points, thresholds, phase=2)
    commands_str_phase_1 = "".join(phase_1_commands)
    commands_str_phase_2 = "".join(phase_2_commands)
    
    thread_func_content = f"""def thread_one_func(sem1, sem2, threshold_queue, phase):
    \"\"\"
    The main function for thread one, which handles the PLC communication and axis movements.
    
    Args:
        sem1 (threading.Semaphore): Semaphore for synchronization with thread two.
        sem2 (threading.Semaphore): Semaphore for synchronization with thread two.
        threshold_queue (queue.Queue): Queue to receive threshold values from thread two.
    \"\"\"
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
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position1", positions["position1"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn1", commands["cmd_DispenserStartDirectOn"])
                time.sleep(12)
                send_cmd(s, "cmd_DispenserStartDirectOff1", commands["cmd_DispenserStartDirectOff"])
                time.sleep(5)
                send_cmd(s, "position2", positions["position2"])
                {commands_str_phase_1}
                if not wait_for_axis_free(s): return       
                send_cmd(s, "position{num_points+3}", positions["position{num_points+3}"])  
            if phase == 2:
                time.sleep(0.5)  # Added delay
                send_cmd(s, "cmd_HomeReturn", commands["cmd_HomeReturn"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "position1", positions["position1"])
                if not wait_for_axis_free(s): return  
                send_cmd(s, "cmd_DispenserStartDirectOn1", commands["cmd_DispenserStartDirectOn"])
                time.sleep(5)
                send_cmd(s, "cmd_DispenserStartDirectOff1", commands["cmd_DispenserStartDirectOff"])
                time.sleep(3)
                send_cmd(s, "position2", positions["position2"])
                {commands_str_phase_2}
                if not wait_for_axis_free(s): return       
                send_cmd(s, "position{num_points+3}", positions["position{num_points+3}"])  
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
                stop_event.set()"""
    
    # Print the generated function to the console
   # print(thread_func_content)

    # Read the existing script
    with open(file_path, 'r') as file:
        file_contents = file.read()

    # Find the start and end of the existing function
    start = file_contents.find('def thread_one_func')
    end = file_contents.find('stop_event.set()', start) + len('stop_event.set()')

    # Ensure we replace the entire function block
    if start != -1 and end != -1:
        updated_contents = file_contents[:start] + thread_func_content + file_contents[end:]
    else:
        print("Function not found or incomplete. Adding new function at the end.")
        updated_contents = file_contents + "\n\n" + thread_func_content

    # Write back to the file
    with open(file_path, 'w') as file:
        file.write(updated_contents)
    print(f"Updated 'thread_one_func' in {file_path}.")

def main(customer_variant: str) -> None:
    """
    Main function to update the thread function script based on variant thresholds.

    Args:
        customer_variant (str): The name of the customer variant to retrieve thresholds for.
    """
    id_variant = get_variant_id(customer_variant)
    if id_variant:
        variant_thresholds_text = get_variant_thresholds(id_variant)
        if variant_thresholds_text:
            num_points, thresholds = parse_variant_thresholds(variant_thresholds_text)
            script_path = 'C:\\Users\\Model Shop\\Desktop\\builds\\data\\plc_scale_sys.py'
            
            #script_path = 'C:\\Users\\jcontram\\Desktop\\gapfeelings\\data\\plc_scale_sys.py'
            #script_path = 'C:\\Users\\jcontram\\Desktop\\work\\robocop\\plc_scale_sys.py'
            generate_thread_func_script(script_path, num_points, thresholds)
            print(f"Generated thread_one_func script and saved to {script_path}")
        else:
            print("No thresholds found for the variant.")
    else:
        print(f"No variant found with name {customer_variant}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update thread_one_func script based on variant thresholds.')
    parser.add_argument('customer_variant', type=str, help='Customer Variant to retrieve thresholds for')
    args = parser.parse_args()
    #variant = "HICE_B_025"
   # main(variant)
    main(args.customer_variant)