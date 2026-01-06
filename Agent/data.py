import socket
import time
import json
import numpy as np
import threading
from typing import Optional

# Define host and port for the server
host = "127.0.0.1"  # Use your local or external IP address
port = 12345
CONNECTION_TIMEOUT = 5.0  # seconds
RECEIVE_TIMEOUT = 10.0  # seconds
BUFFER_SIZE = 4096  # Increased buffer size

current_data = []
server_socket: Optional[socket.socket] = None
client_socket: Optional[socket.socket] = None
is_connected = False

# Create a socket and bind it to the host and port
def create_host(callback):
    global server_socket, client_socket, is_connected
    
    while True:
        try:
            if server_socket:
                server_socket.close()
                
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
            server_socket.listen(1)  # Allow only one connection
            server_socket.settimeout(30.0)  # Timeout for accept()

            print(f"Listening for Unity connection on {host}:{port}...")

            # Accept a connection from Unity
            client_socket, client_address = server_socket.accept()
            client_socket.settimeout(RECEIVE_TIMEOUT)
            is_connected = True
            print(f"Accepted connection from {client_address}")

            # Call the callback function to signal the connection is established
            callback(client_socket)
            
        except socket.timeout:
            print("Waiting for Unity connection...")
            continue
        except Exception as e:
            print(f"Error in create_host: {e}")
            is_connected = False
            time.sleep(2)  # Wait before retrying


def get_state():
    global is_connected
    try:
        if not is_connected or client_socket is None:
            print("Warning: Not connected to Unity")
            return None
            
        # Send request
        message = "get_state"
        client_socket.sendall(message.encode("utf-8"))
        
        # Receive response
        data = client_socket.recv(BUFFER_SIZE).decode("utf-8")
        if not data:
            print("Warning: Received empty data from Unity")
            is_connected = False
            return None
            
        data = data.strip()
        data_list = data.split(',')
        current_data = []
        
        if data_list:
            result_list = []
            for element in data_list:
                element = element.strip()
                if not element:
                    continue
                    
                if element.isdigit():
                    result_list.append(int(element))
                elif element.replace('.', '', 1).replace('-', '', 1).isdigit():
                    result_list.append(float(element))
                elif element.lower() == 'true' or element.lower() == 'false':
                    result_list.append(element.lower() == 'true')
                else:
                    result_list.append(element)

            for value in result_list:
                if isinstance(value, (bool, int, float)):
                    float_value = float(value)
                    current_data.append(float_value)
                    
            current_data = np.array(current_data, dtype=float)
            return current_data
        else:
            print("Warning: Empty data list")
            return None
            
    except socket.timeout:
        print("Error: Timeout while getting state from Unity")
        is_connected = False
        return None
    except Exception as e:
        print(f"Error in get_state: {e}")
        is_connected = False
        return None


def convert_list(string):
    """Convert comma-separated string to list of integers"""
    try:
        l = string.split(",")
        l = [int(number.strip()) for number in l if number.strip()]
        return l
    except ValueError as e:
        print(f"Error converting list: {e}")
        return []


def play_step(step):
    global is_connected
    try:
        if not is_connected or client_socket is None:
            print("Warning: Not connected to Unity")
            return None
            
        # Send action
        to_send = f"play_step:{step}"
        client_socket.sendall(to_send.encode("utf-8"))
        
        # Receive response
        data = client_socket.recv(BUFFER_SIZE).decode("utf-8")
        if not data:
            print("Warning: Received empty data from Unity")
            is_connected = False
            return None
            
        data = data.strip()
        elements = data.split(':')

        if len(elements) < 2:
            print(f"Warning: Invalid response format: {data}")
            return None

        # Parse state data (first element)
        state_data = convert_list(elements[0])
        if not state_data:
            print("Warning: Could not parse state data")
            return None

        # Parse reward and done (second element)
        result_list = []
        for i in range(1, len(elements)):
            element = elements[i].strip()
            if is_float(element):
                result_list.append(float(element))
            elif element.lower() == 'true' or element.lower() == 'false':
                result_list.append(element.lower() == 'true')
            else:
                result_list.append(element)

        reward = result_list[0] if len(result_list) > 0 else 0.0
        done = result_list[1] if len(result_list) > 1 else False

        return np.array(state_data, dtype=float), reward, done
        
    except socket.timeout:
        print("Error: Timeout while playing step")
        is_connected = False
        return None
    except Exception as e:
        print(f"Error in play_step: {e}")
        is_connected = False
        return None


def is_float(s):
    """Check if string can be converted to float"""
    try:
        float(s)
        return True
    except ValueError:
        return False


def reset():
    """Send reset command to Unity"""
    global is_connected
    try:
        if not is_connected or client_socket is None:
            print("Warning: Not connected to Unity")
            return
            
        client_socket.sendall("reset".encode("utf-8"))
        print("Reset command sent to Unity")
    except Exception as e:
        print(f"Error in reset: {e}")
        is_connected = False

