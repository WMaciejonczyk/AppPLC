import tkinter as tk
from tkinter import messagebox
import socket
import threading
from datetime import datetime
import mysql.connector
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


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

                self.convert_to_binary(parsed_data)

                # self.insert_row_into_db(parsed_data)

                # if data:
                #     self.data_output.config(text=f"Dane: {data}", fg="green")
                # else:
                #     self.data_output.config(text=f"Dane: brak", fg="red")
            except socket.error:
                self.disconnect_from_server_stop()

    def convert_to_binary(self, data):
        try:
            # SELECTED MODE
            mode = format(data[8], '04b')
            if mode.count('1') != 1:
                raise ValueError()
            found_mode = mode.find('1')
            match found_mode:
                case 0:
                    self.front_button_label.config(text=self.front_buttons_texts[3])
                case 1:
                    self.front_button_label.config(text=self.front_buttons_texts[2])
                case 2:
                    self.front_button_label.config(text=self.front_buttons_texts[1])
                case 3:
                    self.front_button_label.config(text=self.front_buttons_texts[0])

            counter = -1
            list_of_wanted_indices = [0, 1, 3]
            # TODO: Count in power and energy consumptions later
            for i in list_of_wanted_indices:
                binary_form = format(data[i + 9], '016b')[::-1]
                counter += 1
                list_of_canvas = self.all_canvas[counter]
                list_of_diodes = self.all_diodes[counter]
                for j in range(len(list_of_canvas)):
                    # index = len(list_of_canvas) - j - 1
                    if int(binary_form[j]) == 1:
                        list_of_canvas[j].itemconfig(list_of_diodes[j], fill="green")
                    else:
                        list_of_canvas[j].itemconfig(list_of_diodes[j], fill="white")

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

        self.create_graph()

        # Disconnect Button
        self.disconnect_button = tk.Button(root, text="Disconnect", command=self.disconnect_from_server)
        self.disconnect_button.grid(row=6, column=6, columnspan=2, padx=5, pady=5)

    def create_graph(self):
        # Create a matplotlib figure
        self.figure = Figure(figsize=(5, 2), dpi=100)
        self.ax = self.figure.add_subplot(111)

        # Sample data for the graph
        cursor = self.mydb.cursor()

        query = 'SELECT * FROM tcp_frame LIMIT 100'
        cursor.execute(query)
        data = cursor.fetchall()
        ids = [row[0] for row in data]
        timestamps = [row[4].timestamp() for row in data]

        print(ids)
        print(timestamps)

        # Plot the data
        self.ax.plot(timestamps, ids, marker='o')

        # Configure the graph appearance
        self.ax.set_title("Sample Graph")
        self.ax.set_xlabel("X Axis")
        self.ax.set_ylabel("Y Axis")

        # Embed the graph into the Tkinter window
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().grid(row=7, column=0, columnspan=12, padx=5, pady=5)
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
