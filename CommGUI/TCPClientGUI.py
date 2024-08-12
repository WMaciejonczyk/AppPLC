import tkinter as tk
from tkinter import messagebox
import socket
import threading
from datetime import datetime
import mysql.connector
import os
import struct
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class TCPFrame:
    def __init__(self, data):
        self.beginning = data[0]
        self.function = data[1]
        self.status = data[2]
        self.ts_send = data[3]
        self.number = data[4]
        self.version = data[5]
        self.length = data[6]
        self.ts_gen = data[7]
        self.buttons = data[8]
        self.actuators = data[9]
        self.balls = data[10]
        self.lamps = data[11]
        self.pneumatic = data[12]
        self.rest = data[13]
        self.hmi = data[14]
        self.activators = data[15]
        self.states = data[16]
        self.dead_mem = data[17]
        self.mom_pow = data[18]
        self.cum_en = data[19]
        self.mom_air = data[20]
        self.cum_air = data[21]
        self.alarms = data[22]
        self.end = data[23]

    def get_attributes_without_data(self):
        result = [self.beginning, self.function, self.status,
                  self.ts_send, self. number, self.version,
                  self.length, self.end]

        return result

    def get_data_attributes(self):
        result = [self.ts_gen, self.buttons, self.actuators, self.balls,
                  self.lamps, self.pneumatic, self.rest, self.hmi, self.activators,
                  self.states, self.dead_mem, self.mom_pow, self.cum_en, self.mom_air,
                  self.cum_air, self.alarms]

        return result

    def get_measurements(self):
        result = [self.mom_pow, self.cum_en, self.mom_air, self.cum_air]

        return result


class TCPClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP Client")

        self.mydb = mysql.connector.connect(
            host=os.getenv('MY_SQL_HOST'),
            user=os.getenv('MY_SQL_USER'),
            password=os.getenv('MY_SQL_PASS'),
            database=os.getenv('MY_SQL_DB')
        )

        self.client_socket = None
        self.connected = False
        self.ip = ""
        self.port = 0
        self.all_canvas = []
        self.all_diodes = []
        self.all_measurement_labels = []
        self.all_measurement_results = []
        self.received_tcp_frame = None

        self.global_session_counter = 0

        self.open_login_panel()

    def connect_to_server(self):
        self.ip = self.ip_entry.get()
        self.port = int(self.port_entry.get())

        if not self.ip or not self.port:
            messagebox.showerror("Input Error", "Proszę podaj adres IP oraz port.")
            return

        try:
            port = int(self.port)
            if port <= 0:
                raise ValueError("Input Error")
        except ValueError:
            messagebox.showerror("Input Error", "Port musi być liczbą całkowitą oraz być większy od zera.")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip, self.port))
            self.connected = True

            # Overwrite the main window content
            self.open_main_panel()

        except socket.error as e:
            messagebox.showerror("Connection Error", f"Nie udało się połączyć z serwerem: {e}")
            self.client_socket = None
            self.connected = False
            # self.update_all_diodes("red")

    def connect_to_server_start(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip, self.port))
            self.connected = True

        except socket.error as e:
            messagebox.showerror("Connection Error", f"Nie udało się połączyć z serwerem: {e}")
            self.client_socket = None
            self.connected = False

    def disconnect_from_server(self):
        if self.client_socket:
            self.client_socket.close()
        self.client_socket = None
        self.connected = False

        # Overwrite the main window content
        self.open_login_panel()

    def disconnect_from_server_stop(self):
        if self.client_socket:
            self.client_socket.close()
        self.client_socket = None
        self.connected = False

    def start_receiving(self):
        self.global_session_counter = 0
        self.connect_to_server_start()
        self.thread = threading.Thread(target=self.receive_data, daemon=True)
        self.thread.start()
        self.data_start_label.config(text="STOP", command=self.stop_receiving)

    def stop_receiving(self):
        self.disconnect_from_server_stop()
        self.data_output.config(text="Zatrzymano odbieranie danych", fg="red")
        self.data_start_label.config(text="START", command=self.start_receiving)

        for i in range(len(self.all_canvas)):
            for j in range(len(self.all_canvas[i])):
                self.all_canvas[i][j].itemconfig(self.all_diodes[i][j], fill="white")

        self.cycle_progress_label.config(text="---")
        self.progress.config(value=0)
        self.global_session_counter = 0

        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
            except AttributeError:
                self.disconnect_from_server_stop()
                break

    def data_widget(self):
        # Create text-label
        self.data_frame = tk.Frame(root)
        self.data_frame.grid(row=7, column=6, columnspan=4, padx=5, pady=5)

        self.data_start_label = tk.Button(self.data_frame, text="START", command=self.start_receiving)
        self.data_start_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.data_output = tk.Label(self.data_frame, text="Dane: -", fg="black")
        self.data_output.grid(row=0, column=2, padx=5, pady=5)

    def receive_data(self):
        while self.connected:
            try:
                # Receiving bytes from PLC
                data = self.client_socket.recv(76)
                # Parsing received bytes
                self.parse_data(data)
                # Modifying interface accordingly
                self.modify_GUI()
                # Updating database
                self.insert_row_into_db()
            except socket.error:
                self.disconnect_from_server_stop()

    def modify_GUI(self):
        try:
            if not self.received_tcp_frame:
                raise ValueError("No TCP frame data available!")

            # SELECTED MODE
            mode = format(self.received_tcp_frame.buttons, '04b')[::-1]
            found_mode = mode.find('1')
            self.front_button_label.config(text=self.front_buttons_texts[found_mode])

            # SELECTED STATE
            state = format(self.received_tcp_frame.states, '010b')[::-1]
            found_state = state.find('1')
            self.cycle_progress_label.config(text=self.cycle_progress_texts[found_state])
            self.progress.config(value=(found_state+1)*10)

            # UPDATING DIODES
            binary_form_actuators = format(self.received_tcp_frame.actuators, '016b')[::-1]
            binary_form_balls = format(self.received_tcp_frame.balls, '016b')[::-1]
            binary_form_pneumatic = format(self.received_tcp_frame.pneumatic, '016b')[::-1]

            binary_forms = [binary_form_actuators, binary_form_balls, binary_form_pneumatic]

            for i in range(3):
                list_of_canvas = self.all_canvas[i]
                list_of_diodes = self.all_diodes[i]
                for j in range(len(list_of_canvas)):
                    if int(binary_forms[i][j]) == 1:
                        list_of_canvas[j].itemconfig(list_of_diodes[j], fill="green")
                    else:
                        list_of_canvas[j].itemconfig(list_of_diodes[j], fill="white")

            # UPDATING MEASURED VALUES
            measurements = self.received_tcp_frame.get_measurements()
            for i in range(len(self.all_measurement_results)):
                self.all_measurement_results[i].config(text=f"{measurements[i]}")

            # UPDATE GRAPH
            self.update_graph()

        except ValueError:
            self.stop_receiving()

    def parse_data(self, data):
        def parse_timestamp(received_ts):
            year = int.from_bytes(received_ts[:2], byteorder='big')
            month = received_ts[2]
            day = received_ts[3]

            hours = received_ts[5]
            minutes = received_ts[6]
            seconds = received_ts[7]
            millis = int.from_bytes(received_ts[8:], byteorder="big") // 1_000_000

            dt = datetime(year, month, day, hours, minutes, seconds, millis * 1000)

            timestamp = dt.strftime(f'%Y-%m-%d %H:%M:%S.{millis:03d}')

            return timestamp

        tcp_frame = []

        try:
            # Checking if beginning and ending are correct
            first_char_beg = chr(data[0])
            second_char_beg = chr(data[1])
            first_char_end = chr(data[-2])
            second_char_end = chr(data[-1])
            if first_char_beg != second_char_end or second_char_beg != first_char_end:
                raise ValueError()

            tcp_frame.append(data[:2].decode('utf-8'))                      # BEGINNING
            tcp_frame.append(int.from_bytes(data[2:4], byteorder='big'))    # FUNCTION
            tcp_frame.append(int.from_bytes(data[4:6], byteorder='big'))    # STATUS
            tcp_frame.append(parse_timestamp(data[6:18]))                   # TIMESTAMP OF SENDING DATA

            seq_number = int.from_bytes(data[18:22], byteorder='big')
            if self.received_tcp_frame and (seq_number != self.received_tcp_frame.number + 1):
                raise ValueError("Wrong sequence number!")

            tcp_frame.append(seq_number)                                    # SEQUENCE NUMBER
            tcp_frame.append(int.from_bytes(data[22:24], byteorder='big'))  # VERSION

            # Checking if the attribute 'length' is correctly set
            length = int.from_bytes(data[24:26], byteorder='big')
            if length != len(data):
                raise ValueError()

            tcp_frame.append(length)

            # DATA PART
            tcp_frame.append(parse_timestamp(data[26:38]))                  # TIMESTAMP OF GENERATING DATA

            # BUTTONS, ACTUATORS, BALLS, LAMPS
            # Checking if mode (buttons) is correctly set
            mode = format(int.from_bytes(data[38:40]), '04b')
            if mode.count('1') != 1:
                raise ValueError()

            for i in range(4):
                tcp_frame.append(int.from_bytes(data[38 + i * 2:40 + i * 2], byteorder='big'))

            tcp_frame.append(int.from_bytes(data[46:50], byteorder='big'))  # PNEUMATIC

            # REST, HMI, ACTIVATORS, STATES, DEAD MEMORY, MOMENTARY POWER, CUMULATIVE ENERGY
            # MOMENTARY AIR CONSUMPTION

            # Checking if state is correctly set
            state = format(int.from_bytes(data[56:58]), '010b')[::-1]
            mode_int = int.from_bytes(data[38:40])
            if (state.count('1') == 0 and mode_int != 2) or state.count('1') > 1:
                raise ValueError()

            for i in range(8):
                tcp_frame.append(int.from_bytes(data[50 + i * 2:52 + i * 2], byteorder='big'))

            test = struct.unpack('f', data[66:70])[0]
            tcp_frame.append(struct.unpack('f', data[66:70])[0])     # CUMULATIVE AIR CONSUMPTION

            tcp_frame.append(int.from_bytes(data[70:74], byteorder='big'))   # ALARMS

            tcp_frame.append(data[-2:].decode('utf-8'))                      # END

        except ValueError:
            self.stop_receiving()

        frame = TCPFrame(tcp_frame)
        self.received_tcp_frame = frame
        if self.global_session_counter < 25:
            self.global_session_counter += 1
        if self.global_session_counter == 1:
            self.create_graph()
        else:
            self.update_graph()

    def insert_row_into_db(self):
        cursor = self.mydb.cursor()

        first_part = self.received_tcp_frame.get_attributes_without_data()

        frame_sql = 'INSERT INTO tcp_frame (`beginning`, `function`, `status`, `timestamp`, `number`, `version`, `length`, `ending`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'

        cursor.execute(frame_sql, first_part)
        self.mydb.commit()

        query = 'SELECT id FROM tcp_frame ORDER BY id DESC LIMIT 1'
        cursor.execute(query)
        foreign_key_tuple = cursor.fetchone()
        foreign_key = foreign_key_tuple[0]

        second_part = self.received_tcp_frame.get_data_attributes()
        data_sql = f"""
        INSERT INTO tcp_data (
            `data_id`, `gen_ts`, `buttons`, `actuators_sensors`, `balls_sensors`, `lamps`, `pneumatic_receivers`,
            `rest_receivers`, `HMI_buttons`, `activators`, `states`, `dead_memory`, `momentary_power`,
            `cumulative_energy`, `momentary_air`, `cumulative_air`, `alarms`
        ) VALUES (
            {foreign_key}, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        """

        cursor.execute(data_sql, second_part)
        self.mydb.commit()

        cursor.close()

    def open_login_panel(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Initialize with the entry frame
        self.entry_frame = tk.Frame(root)
        self.entry_frame.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")

        # IP Entry
        self.ip_label = tk.Label(self.entry_frame, text="Server IP:")
        self.ip_label.grid(row=0, column=0, padx=5, pady=5)
        self.ip_entry = tk.Entry(self.entry_frame)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        # Port Entry
        self.port_label = tk.Label(self.entry_frame, text="Port:")
        self.port_label.grid(row=1, column=0, padx=5, pady=5)
        self.port_entry = tk.Entry(self.entry_frame)
        self.port_entry.grid(row=1, column=1, padx=5, pady=5)

        # Connect Button
        self.connect_button = tk.Button(self.entry_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.grid(row=2, column=0, padx=5, pady=5)

    def open_main_panel(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        self.data_widget()

        self.front_buttons()

        self.actuators_sensors()

        self.balls_sensors()

        self.pneumatic_receivers()

        self.measurements()

        self.cycle_progress()

        # Disconnect Button
        self.disconnect_button = tk.Button(root, text="Disconnect", command=self.disconnect_from_server)
        self.disconnect_button.grid(row=6, column=6, columnspan=2, padx=5, pady=5)

    def create_graph(self):
        # Create a matplotlib figure
        self.figure = Figure(figsize=(5, 2), dpi=100)
        self.ax = self.figure.add_subplot(111)

        # Configure the graph appearance
        self.ax.set_title("Sample Graph")
        self.ax.set_xlabel("X Axis")
        self.ax.set_ylabel("Y Axis")

        # Embed the graph into the Tkinter window
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().grid(row=8, column=0, columnspan=12, padx=5, pady=5)

        self.update_graph()

    def update_graph(self):
        self.ax.clear()
        # Sample data for the graph
        cursor = self.mydb.cursor()

        query = f'SELECT * FROM (SELECT * FROM tcp_frame ORDER BY id DESC LIMIT {self.global_session_counter}) AS subquery ORDER BY id'
        cursor.execute(query)
        data = cursor.fetchall()
        ids = [row[0] for row in data]
        timestamps = [row[4].timestamp() for row in data]

        # Plot the data
        self.ax.plot(timestamps, ids, marker='o')

        self.canvas.draw()

    def front_buttons(self):
        # Frame for diode indicators
        self.front_buttons_frame = tk.Frame(root)
        self.front_buttons_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        # Texts and initial states
        self.front_buttons_texts = ["Automatyczny", "Ręczny", "Wyłączony", "Wyłączenie awaryjne"]

        # Create text-label
        title_label = tk.Label(self.front_buttons_frame, text="TRYB:")
        title_label.grid(row=0, column=0, padx=5, pady=5)
        self.front_button_label = tk.Label(self.front_buttons_frame, text=self.front_buttons_texts[2])
        self.front_button_label.grid(row=1, column=0, padx=5, pady=5)

    def actuators_sensors(self):
        # Frame for diode indicators
        actuators_frame = tk.Frame(root)
        actuators_frame.grid(row=0, column=2, columnspan=2, padx=5, pady=5)

        # Texts and initial states
        actuators_texts = ["Podnośnik w górze", "Podnośnik w dole", "Slajd w przodzie",
                           "Slajd w tyle", "Blokada w pozycji 1", "Blokada w pozycji 2"]

        # Create text-label and diode pairs
        actuators_diodes = []
        actuators_labels = []
        actuators_canvas = []
        for i, text in enumerate(actuators_texts):
            # Label with text
            label = tk.Label(actuators_frame, text=text)
            label.grid(row=i, column=0, padx=5, pady=5)

            # Canvas to draw the diode
            canvas = tk.Canvas(actuators_frame, width=30, height=30)
            canvas.grid(row=i, column=1, padx=5, pady=5)

            # Draw the initial diode (small circle)
            diode = self.draw_circle(canvas, 12, 15, 10, color="white")

            # Store references
            actuators_canvas.append(canvas)
            actuators_diodes.append(diode)
            actuators_labels.append(label)

        self.all_canvas.append(actuators_canvas)
        self.all_diodes.append(actuators_diodes)

    def balls_sensors(self):
        # Frame for diode indicators
        balls_frame = tk.Frame(root)
        balls_frame.grid(row=0, column=4, columnspan=2, padx=5, pady=5)

        # Texts and initial states
        balls_texts = ["Nieobecność detalu (pre-stop)", "Nieobecność detalu (stop)", "Nieobecność detalu (podnośnik)"]

        # Create text-label and diode pairs
        balls_diodes = []
        balls_labels = []
        balls_canvas = []
        for i, text in enumerate(balls_texts):
            # Label with text
            label = tk.Label(balls_frame, text=text)
            label.grid(row=i, column=0, padx=5, pady=5)

            # Canvas to draw the diode
            canvas = tk.Canvas(balls_frame, width=30, height=30)
            canvas.grid(row=i, column=1, padx=5, pady=5)

            # Draw the initial diode (small circle)
            diode = self.draw_circle(canvas, 12, 15, 10, color="white")

            # Store references
            balls_canvas.append(canvas)
            balls_diodes.append(diode)
            balls_labels.append(label)

        self.all_canvas.append(balls_canvas)
        self.all_diodes.append(balls_diodes)

    def pneumatic_receivers(self):
        # Frame for diode indicators
        receivers_frame = tk.Frame(root)
        receivers_frame.grid(row=0, column=6, columnspan=4, padx=5, pady=5)

        # Texts and initial states
        receivers_texts = ["POLECENIE - podnośnik w górze", "POLECENIE - podnośnik w dole",
                           "POLECENIE - slajd w przód", "POLECENIE - slajd w tył",
                           "POLECENIE - blokada w pozycję pre-stop w dole", "POLECENIE - blokada w pozycję stop w dole",
                           "POLECENIE - ssawka - zassanie", "POLECENIE - ssawka - wydmuch",
                           "Zawór dodatkowy 1", "Zawór dodatkowy 2", "Zawór dodatkowy 3", "Zawór dodatkowy 4"]

        # Create text-label and diode pairs
        receivers_diodes = []
        receivers_labels = []
        receivers_canvas = []

        j = 0
        for i, text in enumerate(receivers_texts):
            # Label with text
            if i < 6:
                label = tk.Label(receivers_frame, text=text)
                label.grid(row=i, column=0, padx=5, pady=5)

                # Canvas to draw the diode
                canvas = tk.Canvas(receivers_frame, width=30, height=30)
                canvas.grid(row=i, column=1, padx=5, pady=5)
            else:
                label = tk.Label(receivers_frame, text=text)
                label.grid(row=j, column=2, padx=5, pady=5)

                # Canvas to draw the diode
                canvas = tk.Canvas(receivers_frame, width=30, height=30)
                canvas.grid(row=j, column=3, padx=5, pady=5)
                j += 1
            # Draw the initial diode (small circle)
            diode = self.draw_circle(canvas, 12, 15, 10, color="white")

            # Store references
            receivers_canvas.append(canvas)
            receivers_diodes.append(diode)
            receivers_labels.append(label)

        self.all_canvas.append(receivers_canvas)
        self.all_diodes.append(receivers_diodes)

    def measurements(self):
        measurements_frame = tk.Frame(root)
        measurements_frame.grid(row=0, column=10, columnspan=2, padx=5, pady=5)

        # Texts and initial states
        measurements_texts = ["Moc czynna [W]:", "Zużycie całkowite energii [Wh]:", "Zużycie chwilowe powietrza [l/m]:", "Zużycie całkowite powietrza [l]:"]

        # Create text-label
        for i, text in enumerate(measurements_texts):
            # Label with text
            label = tk.Label(measurements_frame, text=text)
            label.grid(row=i, column=0, padx=5, pady=5)

            # Label with result
            result_label = tk.Label(measurements_frame, text="NaN")
            result_label.grid(row=i, column=1, padx=5, pady=5)

            # Store references
            self.all_measurement_labels.append(label)
            self.all_measurement_results.append(result_label)

    def cycle_progress(self):
        cycle_progress_frame = tk.Frame(root)
        cycle_progress_frame.grid(row=1, column=1, rowspan=2, padx=5, pady=5)

        # Texts and initial states
        initial_text = "---"

        self.cycle_progress_texts = ["Pozycja bazowa", "Piłka na prestop", "Piłka na stop", "Piłka na podnośniku",
                                     "Piłka na podnośniku - ssawka wysunięta", "Piłka na podnośniku - podniesiona",
                                     "Piłka przyssana", "Piłka przyssana - podnośnik w dole",
                                     "Piłka przyssana - ssawka wsunięta", "Wydmuch wykonany"]

        # Create text-label
        self.cycle_progress_label = tk.Label(cycle_progress_frame, text=initial_text)
        self.cycle_progress_label.grid(row=0, column=0, padx=5, pady=5)

        # Create progress bar
        self.progress = ttk.Progressbar(cycle_progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress['value'] = 0
        self.progress.grid(row=1, column=0, padx=5, pady=5)

    def draw_circle(self, canvas, x, y, radius, color="black"):
        # Calculate the bounding box coordinates
        x1 = x - radius
        y1 = y - radius
        x2 = x + radius
        y2 = y + radius

        # Draw the circle
        return canvas.create_oval(x1, y1, x2, y2, fill=color, outline="black")


if __name__ == "__main__":
    root = tk.Tk()
    gui = TCPClientGUI(root)
    root.mainloop()
