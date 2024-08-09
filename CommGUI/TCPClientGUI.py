import tkinter as tk
from tkinter import messagebox
import socket
import threading
from datetime import datetime
import mysql.connector
import os

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
        self.connect_to_server_start()
        self.thread = threading.Thread(target=self.receive_data, daemon=True)
        self.thread.start()
        self.data_start_label.config(text="STOP", command=self.stop_receiving)


    def stop_receiving(self):
        self.disconnect_from_server_stop()
        self.data_output.config(text="Zatrzymano odbieranie danych", fg="red")
        self.data_start_label.config(text="START", command=self.start_receiving)

        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
            except AttributeError:
                self.disconnect_from_server_stop()
                break


    # def update_all_diodes(self, color):
    #     # Update all diode colors based on the provided color
    #     for diode in self.diodes:
    #         self.diode_frame.canvas.itemconfig(diode, fill=color)
    #
    # def toggle_all_states(self):
    #     # Toggle all states between 0 and 1
    #     self.states = [1 - state for state in self.states]
    #     # self.update_all_diodes()

    # def update_all_diodes(self):
    #     Update diode colors based on the current states
    #     for diode, state in zip(self.diodes, self.states):
    #         color = "green" if state == 1 else "red"
    #         self.diode_frame.canvas.itemconfig(diode, fill=color)

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
                data = self.client_socket.recv(74)
                parsed_data = self.parse_data(data)

                self.insert_row_into_db(parsed_data)

                # if data:
                #     self.data_output.config(text=f"Dane: {data}", fg="green")
                # else:
                #     self.data_output.config(text=f"Dane: brak", fg="red")
            except socket.error:
                self.disconnect_from_server_stop()

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
        tcp_frame.append(data[:2].decode('utf-8'))                      # BEGINNING
        tcp_frame.append(int.from_bytes(data[2:4], byteorder='big'))    # FUNCTION
        tcp_frame.append(int.from_bytes(data[4:6], byteorder='big'))    # STATUS
        tcp_frame.append(parse_timestamp(data[6:18]))                   # TIMESTAMP OF SENDING DATA
        tcp_frame.append(int.from_bytes(data[18:22], byteorder='big'))  # SEQUENCE NUMBER
        tcp_frame.append(int.from_bytes(data[22:24], byteorder='big'))  # VERSION
        tcp_frame.append(int.from_bytes(data[24:26], byteorder='big'))  # LENGTH

        # DATA PART
        tcp_frame.append(parse_timestamp(data[26:38]))                  # TIMESTAMP OF GENERATING DATA
        # BUTTONS, ACTUATORS, BALLS, LAMPS
        for i in range(4):
            tcp_frame.append(int.from_bytes(data[38 + i * 2:40 + i * 2], byteorder='big'))

        tcp_frame.append(int.from_bytes(data[46:50], byteorder='big'))  # PNEUMATIC

        # REST, HMI, ACTIVATORS, STATES, DEAD MEMORY, MOMENTARY POWER, CUMULATIVE ENERGY
        # MOMENTARY AIR CONSUMPTION, CUMULATIVE AIR CONSUMPTION
        for i in range(9):
            tcp_frame.append(int.from_bytes(data[50 + i * 2:52 + i * 2], byteorder='big'))

        tcp_frame.append(int.from_bytes(data[68:72], byteorder='big'))  # ALARMS

        tcp_frame.append(data[-2:].decode('utf-8'))                      # END

        return tcp_frame

    def insert_row_into_db(self, data):
        cursor = self.mydb.cursor()

        first_part = data[:7]
        first_part.append(data[-1])

        frame_sql = 'INSERT INTO tcp_frame (`beginning`, `function`, `status`, `timestamp`, `number`, `version`, `length`, `ending`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'

        cursor.execute(frame_sql, first_part)
        self.mydb.commit()

        query = 'SELECT id FROM tcp_frame ORDER BY id DESC LIMIT 1'
        cursor.execute(query)
        foreign_key_tuple = cursor.fetchone()
        foreign_key = foreign_key_tuple[0]

        second_part = data[7:-1]
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

        # Disconnect Button
        self.disconnect_button = tk.Button(root, text="Disconnect", command=self.disconnect_from_server)
        self.disconnect_button.grid(row=6, column=6, columnspan=2, padx=5, pady=5)

    def front_buttons(self):
        # Frame for diode indicators
        self.front_buttons_frame = tk.Frame(root)
        self.front_buttons_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        # Texts and initial states
        self.front_buttons_texts = ["Automatyczny", "Manualny", "Wyłączony"]

        # Create text-label
        title_label = tk.Label(self.front_buttons_frame, text="TRYB:")
        title_label.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Label(self.front_buttons_frame, text=self.front_buttons_texts[2])
        label.grid(row=1, column=0, padx=5, pady=5)

    def actuators_sensors(self):
        # Frame for diode indicators
        self.actuators_frame = tk.Frame(root)
        self.actuators_frame.grid(row=0, column=2, columnspan=2, padx=5, pady=5)

        # Texts and initial states
        self.actuators_texts = ["Podnośnik w górze", "Podnośnik w dole", "Slajd w przodzie",
                      "Blokada w pozycji 1", "Blokada w pozycji 2"]
        self.actuators_states = [0] * len(self.actuators_texts)  # All start with state 0

        # Create text-label and diode pairs
        self.actuators_diodes = []
        self.actuators_labels = []
        for i, text in enumerate(self.actuators_texts):
            # Label with text
            label = tk.Label(self.actuators_frame, text=text)
            label.grid(row=i, column=0, padx=5, pady=5)

            # Canvas to draw the diode
            canvas = tk.Canvas(self.actuators_frame, width=30, height=30)
            canvas.grid(row=i, column=1, padx=5, pady=5)

            # Draw the initial diode (small circle)
            diode = self.draw_circle(canvas, 10, 15, 5, color="red")

            # Store references
            self.actuators_diodes.append(diode)
            self.actuators_labels.append(label)

    def balls_sensors(self):
        # Frame for diode indicators
        self.balls_frame = tk.Frame(root)
        self.balls_frame.grid(row=0, column=4, columnspan=2, padx=5, pady=5)

        # Texts and initial states
        self.balls_texts = ["Nieobecność detalu (pre-stop)", "Nieobecność detalu (stop)", "Nieobecność detalu (podnośnik)"]
        self.balls_states = [0] * len(self.balls_texts)  # All start with state 0

        # Create text-label and diode pairs
        self.balls_diodes = []
        self.balls_labels = []
        for i, text in enumerate(self.balls_texts):
            # Label with text
            label = tk.Label(self.balls_frame, text=text)
            label.grid(row=i, column=0, padx=5, pady=5)

            # Canvas to draw the diode
            canvas = tk.Canvas(self.balls_frame, width=30, height=30)
            canvas.grid(row=i, column=1, padx=5, pady=5)

            # Draw the initial diode (small circle)
            diode = self.draw_circle(canvas, 10, 15, 5, color="red")

            # Store references
            self.balls_diodes.append(diode)
            self.balls_labels.append(label)

    def pneumatic_receivers(self):
        # Frame for diode indicators
        self.receivers_frame = tk.Frame(root)
        self.receivers_frame.grid(row=0, column=6, columnspan=4, padx=5, pady=5)

        # Texts and initial states
        self.receivers_texts = ["POLECENIE - podnośnik w górze", "POLECENIE - podnośnik w dole",
                                "POLECENIE - slajd w przód", "POLECENIE - slajd w tył",
                                "POLECENIE - blokada w pozycję pre-stop w dole", "POLECENIE - blokada w pozycję stop w dole",
                                "POLECENIE - ssawka - zassanie", "POLECENIE - ssawka - wydmuch",
                                "Zawór dodatkowy 1", "Zawór dodatkowy 2", "Zawór dodatkowy 3", "Zawór dodatkowy 4"]
        self.receivers_states = [0] * len(self.receivers_texts)  # All start with state 0

        # Create text-label and diode pairs
        self.receivers_diodes = []
        self.receivers_labels = []

        j = 0
        for i, text in enumerate(self.receivers_texts):
            # Label with text
            if (i < 6):
                label = tk.Label(self.receivers_frame, text=text)
                label.grid(row=i, column=0, padx=5, pady=5)

                # Canvas to draw the diode
                canvas = tk.Canvas(self.receivers_frame, width=30, height=30)
                canvas.grid(row=i, column=1, padx=5, pady=5)
            else:
                label = tk.Label(self.receivers_frame, text=text)
                label.grid(row=j, column=2, padx=5, pady=5)

                # Canvas to draw the diode
                canvas = tk.Canvas(self.receivers_frame, width=30, height=30)
                canvas.grid(row=j, column=3, padx=5, pady=5)
                j += 1
            # Draw the initial diode (small circle)
            diode = self.draw_circle(canvas, 10, 15, 5, color="red")

            # Store references
            self.receivers_diodes.append(diode)
            self.receivers_labels.append(label)

    def measurements(self):
        self.measurements_frame = tk.Frame(root)
        self.measurements_frame.grid(row=0, column=10, columnspan=2, padx=5, pady=5)

        # Texts and initial states
        self.measurements_texts = ["Moc czynna [W]:", "Zużycie całkowite energii [Wh]:", "Zużycie chwilowe powietrza [l/m]:", "Zużycie całkowite powietrza [l]:"]

        # Create text-label
        self.measurements_labels = []
        self.measurements_results = []
        for i, text in enumerate(self.measurements_texts):
            # Label with text
            label = tk.Label(self.measurements_frame, text=text)
            label.grid(row=i, column=0, padx=5, pady=5)

            # Label with result
            result_label = tk.Label(self.measurements_frame, text="NaN")
            result_label.grid(row=i, column=1, padx=5, pady=5)

            # Store references
            self.measurements_labels.append(label)
            self.measurements_results.append(result_label)

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

