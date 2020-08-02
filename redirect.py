import sys
import os
import threading
import socket
import time
import copy

total = 0

buffer = []
data_ready = False
lock = threading.Lock()
condition = threading.Condition(lock)

def handle_tcp():
    global buffer
    global data_ready
    global condition
    global lock
    while True:
        try:
            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Establish connection to TCP server and exchange data
            print("Try to connect...")
            tcp_client.connect((sys.argv[2], int(sys.argv[3])))
            print("Connected")
            while True:
                with condition:
                    while not data_ready:
                        condition.wait()
                    for frame in buffer:
                        tcp_client.sendall(frame)
                    buffer = []
                    data_ready = False
        except:
            print("Failed")
            pass
        finally:
            tcp_client.close()
        time.sleep(5)
        with lock:
            buffer = []

tcp_thread = threading.Thread(target=handle_tcp)
tcp_thread.start()

sys.stdin = os.fdopen(sys.stdin.fileno(), 'rb', 0)

buffer_size = int(sys.argv[1])

try:
    while True:
        frame = sys.stdin.read(buffer_size)
        with condition:
            buffer.append(frame)
            data_ready = True
            condition.notify()
except KeyboardInterrupt:
    exit()

tcp_thread.join()
