### TEST FILE FOR CAULDRON PROOF-OF-CONCEPT ###

### Overview ###
#
# Cauldron is an AI-assisted recipe development platform that allows users to generate and quickly iterate on new recipes. 
# Cauldron leverages multi-agent generative artificial intelligence tools to generate a desired foundational recipe from a provided prompt and optionally provided context. Cauldron then provides channels for both human and machine sensory feedback to iteratively refine the recipe.

# The system works as follows:
# 1. User provides a prompt and optionally context (i.e. custom ingredients, dietary restrictions, recipe sources, etc.)
# 2. The system (Cauldron) parses the request and determines what type of SQL query to execute on a local database of recipes, ingredients, and processes
# 3. Cauldron executes the query and returns a list of relevant information
# 4. Cauldron formats the returned information into a context for recipe generation
# 5. Cauldron generates a foundational recipe based on the context and prompt.
# 6. Cauldron provides the foundational recipe to the user for feedback
# 7. The user provides feedback on the recipe and the foundational recipe is tweaked until the user is satisfied
# 8. Cauldron provides interaction points for human feedback (in the form of written and spoken language) and machine feedback (in the form of sensory data provided by IoT devices)
# 9. The user is free to cook/bake the recipe and provide feedback on the final product
# 10. Cauldron intelligently uses this feedback to further refine the recipe as well as save a "snapshot" of the recipe attempt for future reference

### IMPORTS ###
import os
from util import SQLAgent, ChatBot, find_SQL_prompt, VoiceInterface
import warnings
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import serial
import threading
import time
from datetime import datetime

warnings.filterwarnings("ignore", message="Parent run .* not found for run .* Treating as a root run.")

### DEFINITIONS ###

class CauldronApp():
    
    def __init__(self, db_path, llm_model, assistant_prompt, assistant_temperature, verbose=False):
        self.db = db_path
        self.llm = llm_model
        self.SQLAgent = SQLAgent(llm_model, db_path, verbose=verbose)
        self.Assistant = ChatBot(llm_model, assistant_prompt, assistant_temperature)

### MAIN ###

#Parameter for chains & agents
db_path = "sqlite:///sql/recipes.db"
llm_model = "gpt-3.5-turbo"
assistant_prompt = "blake-goodwyn/cauldron-assistant-v0"
assistant_temperature = 0.0

# Constants for serial communication
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200
INITIAL_PERIOD = 1
ADC_BOUND = 7

app = CauldronApp(db_path, llm_model, assistant_prompt, assistant_temperature, verbose=True)

import tkinter as tk
from tkinter.scrolledtext import ScrolledText

class InteractiveDemo:
    def __init__(self, master):
        self.master = master
        self.running = True  # Flag to indicate that the app is running
        self.master.title("Cauldron Interactive Demo Application")
        self.master.geometry("1200x600")  # Adjust size as necessary

        # Voice interface
        self.voice_interface = VoiceInterface()

         # Set up the grid layout for the main window
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)

        # Setup the text input and response area in the top-left and bottom-left quadrants
        self.frame_text_interaction = tk.Frame(master)
        self.frame_text_interaction.grid(row=0, column=0, sticky='nsew', rowspan=2)  # Span two rows

        self.input_text = tk.Entry(self.frame_text_interaction)
        self.input_text.pack(fill=tk.X, padx=10, pady=10)

        self.output_text = ScrolledText(self.frame_text_interaction)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.send_button = tk.Button(self.frame_text_interaction, text="Send", command=self.process_input)
        self.send_button.pack(fill=tk.X, padx=10, pady=5)

        self.clear_button = tk.Button(self.frame_text_interaction, text="Clear", command=self.clear_output)
        self.clear_button.pack(fill=tk.X, padx=10, pady=5)

        # Transcription display in the upper right quadrant
        self.transcription_text = ScrolledText(master, height=10)
        self.transcription_text.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)

        # Recording Indicator
        self.canvas = tk.Canvas(master, width=20, height=20)
        self.recording_indicator = self.canvas.create_oval(5, 5, 20, 20, fill='red')
        self.canvas.itemconfig(self.recording_indicator, state='hidden')  # Initially hidden
        self.canvas.grid(row=0, column=1, sticky='ne', padx=10, pady=10)

        self.record_button = tk.Button(master, text="Record Audio", command=self.start_recording)
        self.record_button.grid(row=0, column=1, sticky='n', padx=10, pady=(50, 0))

        self.transcribe_button = tk.Button(master, text="Transcribe Audio", command=self.transcribe_audio)
        self.transcribe_button.grid(row=0, column=1, sticky='n', padx=10, pady=(90, 0))

        self.copy_to_chat_button = tk.Button(master, text="Copy to Chat Input", command=self.copy_transcription_to_chat)
        self.copy_to_chat_button.grid(row=0, column=1, sticky='n', padx=10, pady=(130, 0))

        # Sensor display components
        self.lights = []
        self.adc_texts = []
        self.setup_sensor_display(master)

        # Serial connection
        self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
        self.start_time = time.time()
        self.baseline = [0] * 8
        self.initial_readings = [[] for _ in range(8)]
        self.start_sensor_reading()

    def start_recording(self):
        """Start the recording in a separate thread to avoid UI blocking."""
        def hide_indicator():
            self.canvas.itemconfig(self.recording_indicator, state='hidden')  # Hide indicator

        self.canvas.itemconfig(self.recording_indicator, state='normal')  # Show indicator
        self.master.after(100, lambda: threading.Thread(target=lambda: self.voice_interface.record_audio(callback=hide_indicator)).start())

    def transcribe_audio(self):
        """Transcribe the recorded audio and display it."""
        transcription = self.voice_interface.transcribe_audio()
        self.transcription_text.delete("1.0", tk.END)  # Clear all text from the text box
        self.transcription_text.insert(tk.END, transcription + "\n")
        self.transcription_text.see(tk.END)

    def copy_transcription_to_chat(self):
        """
        Copies the contents of the transcription text box to the chatbot input text box.
        """
        # Get text from transcription_text ScrolledText widget
        transcription_text = self.transcription_text.get("1.0", tk.END).strip()

        # Clear existing content in the input_text Entry widget and insert the new text
        self.input_text.delete(0, tk.END)
        self.input_text.insert(0, transcription_text)

    def setup_sensor_display(self, parent):
        # Frame for sensor display in the lower right quadrant
        sensor_frame = tk.Frame(parent)
        sensor_frame.grid(row=1, column=1, sticky='nsew')
        
        # Configuring a 5x5 grid
        for i in range(5):
            sensor_frame.grid_rowconfigure(i, weight=1)
            sensor_frame.grid_columnconfigure(i, weight=1)

        # Specifying the positions of each sensor within the 5x5 grid
        sensor_positions = {
            1: (0, 2),
            0: (1, 2),
            2: (2, 0), 3: (2, 1),
            6: (2, 3), 7: (2, 4),
            4: (3, 2),
            5: (4, 2)
        }

        # Creating sensor displays
        self.lights = []
        self.adc_texts = []
        for sensor_id, (row, col) in sensor_positions.items():
            frame = tk.Frame(sensor_frame, bd=2, relief="ridge")
            frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')

            light_canvas = tk.Canvas(frame, bg="red", height=60, width=60)
            light_canvas.pack(fill='both', expand=True)
            
            adc_text = light_canvas.create_text(30, 30, text=f"ADC: 0", fill="white")
            self.adc_texts.append(adc_text)
            self.lights.append(light_canvas)

    def start_sensor_reading(self):
        threading.Thread(target=self.check_serial, daemon=True).start()

    def check_serial(self):
        while self.running:
            if self.ser.in_waiting:
                line = self.ser.readline()
                try:
                    decoded_line = line.decode('utf-8').strip().split('\t')
                    for i in range(8):
                        current_value = int(decoded_line[i * 3 + 1])
                        self.lights[i].itemconfig(self.adc_texts[i], text=f"ADC: {current_value}")
                        color = self.calculate_color(current_value, self.baseline[i])
                        self.lights[i].config(bg=color)
                except Exception as e:
                    print("Error:", e)
            time.sleep(0.01)

    def calculate_color(self, value, baseline):
        difference = abs(value - baseline)
        if difference < ADC_BOUND:
            return "#ff0000"  # Red for values within the bound
        else:
            green_intensity = int(max(0, 255 - int((difference - ADC_BOUND)) * 0.75))
            return f"#00{green_intensity:02x}00"

    def append_output_chat(self,chat_output):
        if "actions" in chat_output:
            for action in chat_output["actions"]:
                self.output_text.insert(tk.END, f"Calling Tool: `{action.tool}` with input `{action.tool_input}`\n")
        # Observation
        elif "steps" in chat_output:
            for step in chat_output["steps"]:
                self.output_text.insert(tk.END, f"Tool Result: `{step.observation}`\n")
        # Final result
        elif "output" in chat_output:
            self.output_text.insert(tk.END, f'Final Output: {chat_output["output"]}\n')
        else:
            self.output_text.insert(tk.END, chat_output)

        self.output_text.see(tk.END)

    def finalize_stream(self):
        self.execute_sql_commands()  # Execute collected SQL commands

    def process_input(self):
        user_input = self.input_text.get()
        if user_input.lower() == "exit":
            self.output_text.insert(tk.END, "Exiting...\n")
            self.master.quit()  # Close the application
        else:
            # Start streaming in a separate thread, properly passing the callback and on_complete functions
            thread = threading.Thread(target=lambda: app.Assistant.stream(user_input, self.append_output_chat, self.finalize_stream))
            thread.start()
            self.input_text.delete(0, tk.END)

    def execute_sql_commands(self):
        sqlQueries = find_SQL_prompt(self.output_text.get("1.0", "end-1c"))
        print(sqlQueries)
        thread = threading.Thread(target=lambda: app.SQLAgent.stream(sqlQueries, self.append_output_chat))
        thread.start()

    def clear_output(self):
        self.output_text.delete("1.0", tk.END)  # Clear all text from the output text box

    def on_close(self):
        """Clean up and close the application gracefully."""
        self.running = False  # Signal all threads to stop
        self.master.after(500, self.master.destroy)  # Delay to allow threads to terminate

        # Additional cleanup if necessary, like closing serial connections:
        if self.ser.is_open:
            self.ser.close()       

def main():
    root = tk.Tk()
    app = InteractiveDemo(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)  # Bind the close event
    root.mainloop()

if __name__ == "__main__":
    main()