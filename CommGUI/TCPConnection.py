import socket
import mysql.connector

server_address = ('192.168.20.160', 666)
mydb = mysql.connector.connect(
  host='localhost',
  user="root",
  password="root",
  database="plc_data"
)

server_address2 = ('192.168.0.1', 2000)

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as so:

        so.connect(server_address2)



        tcp_test = so.recv(1024)

        print(tcp_test)

    # List positions
    # 0 - beginning
    # 1 - function
    # 2 - status
    # 3 - timestamp
    # 4 - number
    # 5 - version
    # 6 - length
    ###### DATA SEGMENT ######
    # 7 - buttons
    # 8 - actuators' sensors
    # 9 - balls' sensors
    # 10 - lamps
    # 11 - pneumatic receivers
    # 12 - rest receivers
    # 13 - HMI buttons
    # 14 - activators
    # 15 - states
    # 16 - dead memory
    # 17 - momentary power
    # 18 - cumulative energy
    # 19 - momentary air
    # 20 - cumulative air
    # 21 - alarms
    ###### DATA SEGMENT ######
    # 22 - end

# def parse_frame(frame_list):
#     parsed_frame_list = []
#
#     for item in frame_list:
#         try:
#             # Attempt to convert to an integer
#             parsed_frame_list.append(int(item))
#         except ValueError:
#             # If conversion fails, keep the original string
#             parsed_frame_list.append(item)
#
#     return parsed_frame_list
#
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#
#     s.connect(server_address)
#
#     tcp_frame = s.recv(1024)
#
#     decoded_frame = tcp_frame.decode('utf-8')
#
#     frame_list = decoded_frame.split(";")
#
#     print(frame_list)
#
#     parsed_frame_list = parse_frame(frame_list)
#
#     print(parsed_frame_list)
#
#     except_data_list = parsed_frame_list[:7] + parsed_frame_list[21 + 1:]
#
#     data_list = parsed_frame_list[7:-1]
#
#     print(except_data_list)
#
#     print(data_list)
#     mycursor = mydb.cursor()
#
#     sql_frame = """
#     INSERT INTO tcp_frame (
#         `beginning`, `function`, `status`, `timestamp`, `number`, `version`, `length`, `data_id`, `ending`
#     ) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s)
#     """
#
#     mycursor.execute(sql_frame, filtered_list)
#
#     mydb.commit()
#
#     print(mycursor.rowcount, "record inserted.")
#
#     sql_data = f"INSERT INTO tcp_data (data_id, buttons, actuators_sensors, balls_sensors, lamps, pneumatic_receivers, rest_receivers, HMI_buttons, activators, states, dead_memory, momentary_power, cumulative_energy, momentary_air, cumulative_air, alarms) VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
#     mycursor.execute(sql_data, data)
#
#     mydb.commit()
#
#     print(mycursor.rowcount, "record inserted.")