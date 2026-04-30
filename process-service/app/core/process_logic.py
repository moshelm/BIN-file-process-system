import logging

from pymavlink import mavutil


class Logic:
    def __init__(self):
        pass

    def process_file(self, file_name: str):
        mav = mavutil.mavlink_connection(file_name)
        msg_number = 1000
        msg_types = []
        while True:
            msg = mav.recv_match(blocking=True)
            msg_types.append(msg.get_type())
            if msg is None:
                break
        return msg_types
