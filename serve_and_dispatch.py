#!/usr/bin/python3

import socket
import asyncio
import ipaddress
import sys
import logging
import os
import time
import threading
from pathlib import Path
from datetime import datetime
from datetime import timedelta

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(screen_handler)
    return logger

LOGGER = setup_custom_logger("proxy")
camera_map = {"192.168.2.66": {"name": "ParkingCam", "streamer_port": 4900}, "192.168.2.52": {"name": "PorchCam", "streamer_port": 4901}, "192.168.2.18": {"name": "ShedCam", "streamer_port": 4902}}

class CameraDispatcher(asyncio.Protocol):
    def __init__(self, loop):
        self.loop = loop
        self.streaming_buffer = []
        self.data_ready = False
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def connection_made(self, transport):
        self.transport = transport
        self.peer = ipaddress.IPv4Address(self.transport.get_extra_info('peername')[0])
        self.camera_name = camera_map[str(self.peer)]["name"]
        self.streamer_port = camera_map[str(self.peer)]["streamer_port"]
        LOGGER.info("Connection from: " + self.camera_name + " (" + str(self.peer) + ")")
        self.sequence_id = -1
        self.video_file_name = "/dev/null"
        Path(self.camera_name + "/to_encode").mkdir(parents=True, exist_ok=True)
        self.video_path = Path(self.camera_name + "/in_progress")
        self.video_path.mkdir(parents=True, exist_ok=True)
        self.video_file = open(self.video_file_name, "wb")
        self.streaming_thread = threading.Thread(target=self.handle_stream_retransmit)
        self.streaming_thread.start()
        self.sequence_start_time = datetime.now()
        self.sequence_end_time = datetime.now()
    
    def connection_lost(self, exc):
        LOGGER.info("Connection with " + str(self.peer) + " closed")

    def seek_first_frame(self, data, offset):
        start_of_frame = data.find(b"\x00\x00\x00\x01", offset)
        if start_of_frame == -1:
            self.video_file.write(data)
            return b""
        else:
            self.video_file.write(data[:start_of_frame])
            return data[start_of_frame:]
            
    def seek_key_frame(self, frame, sequence_time):
        if len(frame) > 5 and int.from_bytes(frame[4:5], "big") == 0x27:
            if self.video_file_name != "/dev/null":
                self.video_file.close()
                os.rename(self.video_file_name, self.video_path / ("../to_encode/video" + str(f'{self.sequence_id:04}') + ".h264"))
                with open(self.video_path / ("../to_encode/video" + str(f'{self.sequence_id:04}') + ".txt"), 'w') as info_file:
                    info_file.write(str(int(self.sequence_start_time.timestamp())) + "," + str(int(sequence_time.timestamp())) + "," + self.camera_name)
            self.sequence_id += 1
            if self.sequence_id >= 168:
                self.sequence_id = 0
            self.video_file_name = self.video_path / ("video" + str(f'{self.sequence_id:04}') + ".h264")
            self.video_file = open(self.video_file_name, "wb")
            self.video_file.write(frame)
            self.sequence_start_time = sequence_time
            self.sequence_end_time = sequence_time + timedelta(seconds=3600)
            return b""
        else:
            return self.seek_first_frame(frame, 4)

    def data_received(self, data):
        with self.condition:
            self.streaming_buffer.append(data)
            self.data_ready = True
            self.condition.notify()
        # start_of_frame = data.find(b"\x00\x00\x00\x01")
        # while start_of_frame != -1 and start_of_frame + 5 < len(data):
        #     if int.from_bytes(data[start_of_frame+4:start_of_frame + 5], "big") != 0x21:
        #         print(hex(int.from_bytes(data[start_of_frame+4:start_of_frame + 5], "big")))
        #     data = data[start_of_frame+4:]
        #     start_of_frame = data.find(b"\x00\x00\x00\x01")
        sequence_time = datetime.now()
        if sequence_time >= self.sequence_end_time:
            frame = self.seek_first_frame(data, 0)
            while len(frame) > 0:
                frame = self.seek_key_frame(frame, sequence_time)
        else:
            self.video_file.write(data)
    
    def handle_stream_retransmit(self):
        while True:
            try:
                tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Establish connection to TCP server and exchange data
                tcp_client.connect(("localhost", self.streamer_port))
                streamming_connection_alive = True
                LOGGER.info(self.camera_name + " streaming connection established")
                while True:
                    with self.condition:
                        while not self.data_ready:
                            self.condition.wait()
                        for frame in self.streaming_buffer:
                            tcp_client.sendall(frame)
                        self.streaming_buffer = []
                        self.data_ready = False
            except:
                if streamming_connection_alive:
                    streamming_connection_alive = False
                    LOGGER.info(self.camera_name + " streaming connection lost")
                pass
            finally:
                tcp_client.close()
            time.sleep(5)
            with self.lock:
                self.streaming_buffer = []

loop = asyncio.get_event_loop()

coro = loop.create_server(lambda: CameraDispatcher(loop), "0.0.0.0", 5000)

server = loop.run_until_complete(coro)

print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
 
