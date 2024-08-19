import time
import numpy as np
import matplotlib.pyplot as plt
from tifffile import imread, imsave, imwrite
from functions import process_channel
from decimal import Decimal

import tkinter as tk
from tkinter import ttk, filedialog
from threading import Thread
import matplotlib.pyplot as plt

import customtkinter as ctk

import os
import glob

class FileStatusComponent(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # self.configure(corner_radius=15, fg_color="#313232", bg_color="#313232")
        self.configure(corner_radius=15, fg_color="#313232")
        self.completed = 0

        self.remaining_count_text = tk.StringVar()
        self.remaining_count = ctk.CTkLabel(self, textvariable=self.remaining_count_text, text="0", font=("Arial Bold", 30))
        self.remaining_label = ctk.CTkLabel(self, text="Files Left", text_color=("black", "#606363"))

        self.completed_count_text = tk.StringVar()
        self.completed_count = ctk.CTkLabel(self, textvariable=self.completed_count_text, text="0", font=("Arial Bold", 30))
        self.completed_label = ctk.CTkLabel(self, text="Files Completed", text_color=("black", "#606363"))
        
        self.seconds_count_text = tk.StringVar()
        self.seconds_count = ctk.CTkLabel(self, textvariable=self.seconds_count_text, text="0", font=("Arial Bold", 30))
        self.seconds_label = ctk.CTkLabel(self, text="Seconds Left", text_color=("black", "#606363"))
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        
        self.remaining_count.grid(row=0, column=0, pady=(10, 0))
        self.remaining_label.grid(row=1, column=0, pady=(0, 10))
        
        self.completed_count.grid(row=0, column=1, pady=(10, 0))
        self.completed_label.grid(row=1, column=1, pady=(0, 10))
        
        self.seconds_count.grid(row=0, column=2, pady=(10, 0))
        self.seconds_label.grid(row=1, column=2, pady=(0, 10))

        self.set_default()

    def update_remaining_files(self, num):
        self.remaining_count_text.set(str(num))

    def update_completed_files(self):
        self.completed += 1
        self.completed_count_text.set(str(self.completed))

    def update_seconds_remaining(self, num):
        self.seconds_count_text.set(str(num))

    def set_default(self):
        self.processed_channels = {}
        self.remaining_count_text.set("0")
        self.seconds_count_text.set("0")
        self.completed_count_text.set(self.completed)
        self.completed = 0

# GUI application
class Application(ctk.CTk):
    def __init__(self):
        super().__init__()
        img = tk.PhotoImage(file='icon.png')
        self.iconphoto(True, img)
        # ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
        self.title("ClariTir: Z-Stack Formatter Suite")
        # self.geometry("500x400")
        self.geometry("800x800")

        self.fg_color = "#313232"
        self.processed_channels = {}

        self.file_status = FileStatusComponent(self)
        self.file_status.pack(pady=(20, 0), padx=20, fill=tk.X)
        self.file_currently_processing = None

        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=self.fg_color)
        self.status_banner_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, fg_color='#FF0000')
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        # self.status_banner_frame.pack(pady=0, padx=0, fill="x", expand=True)

        #default parameters for TDA image size
        self.xscale = 0.3107 #voxel size in um 
        self.yscale = 0.3107
        self.zstep = 2
        self.resolution = 3.2181 #pixels per um
        self.lsm510 = 0 #will be true if lsm510 used, otherwise false

        self.to_process = []

        self.create_widgets()

    def create_widgets(self):
        # Frame for the load directory button
        buttons_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, fg_color=self.fg_color)
        buttons_frame.pack(pady=20)
        buttons_frame.place(relx=0.5, rely=0.5, anchor='center')

        # New frame for the scaling suite
        scale_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, fg_color=self.fg_color)
        scale_frame.place(relx=0.5, rely=0.62, anchor='center')

        self.title_label = ctk.CTkLabel(self.main_frame, text="TDA Image Processor", font=("Arial", 30))
        self.title_label.place(relx=0.5, rely=0.32, anchor='center')  # Adjust this value so it's slightly above center

        self.instructions_label = ctk.CTkLabel(self.main_frame, 
                                        text="Begin by choosing either an image directory or a single image.", 
                                        wraplength=300)
        self.instructions_label.place(relx=0.5, rely=0.42, anchor='center')  # Adjust this value so it's below the title label
        
        self.scaling_label = ctk.CTkLabel(self.main_frame, text="Or specify scaling for your image/s here:", wraplength=300)
        self.scaling_label.place(relx=0.5, rely=0.57, anchor='center')  # Adjust this value so it's slightly above center
        
        # Place the 'Load Directory' button to the left side of the frame
        self.load_button = ctk.CTkButton(buttons_frame, text="Load Directory", command=self.load_directory)
        self.load_button.pack(side="left")

        # Add an 'or' label in between the buttons
        self.or_label = ctk.CTkLabel(buttons_frame, text="or")
        self.or_label.pack(side="left", padx=10)  # padx adds some space on both sides of the label

        # Place the 'Load Image' button to the right side of the or_label (but still to the left side of the frame)
        self.load_image_button = ctk.CTkButton(buttons_frame, text="Load Image", command=self.load_image)
        self.load_image_button.pack(pady=10, side="left")

        #adding a button to specify scaling and metadata
        self.load_scale_button = ctk.CTkButton(scale_frame, text = "Specify Scaling", command = self.specify_scaling)
        self.load_scale_button.pack(side="top") #place the button below the two other buttons

        # add a credit label to the bottom of the frame
        credit_label = ctk.CTkLabel(self.main_frame, text="Copyright: Penelope L. Tir, John L. McCambridge, 2024", font=("Arial", 10), text_color=("black", "#606363"))
        credit_label.place(relx=0.5, rely=0.95, anchor='center')

        self.is_shown = True

    def toggle_buttons(self):
        if self.is_shown:
            self.load_button.pack_forget()
            self.or_label.pack_forget()
            self.load_image_button.pack_forget()
            self.title_label.place_forget()
            self.instructions_label.place_forget()

            self.is_shown = False
        else:
            self.load_button.pack(side="left")
            self.or_label.pack(side="left", padx=10)
            self.load_image_button.pack(side="left")
            self.title_label.place(relx=0.5, rely=0.35, anchor='center')
            self.instructions_label.place(relx=0.5, rely=0.42, anchor='center')
            self.is_shown = True

    def run_process(self, file_path):
        self.image_data = imread(file_path)
        self.total_slices = self.image_data.shape[0]
        self.total_channels = self.image_data.shape[1]
        self.total_work = self.total_slices * self.total_channels
        self.last_delta = time.time()
        self.average_delta = 0

        self.deltas = []
        self.stamps = []
        self.averages = []

        self.remain_estimate = None

        print(f"total slices: {self.total_slices}")
        
        # remove previous preview images
        self.refresh_ui()

        # add a label which shows the current file being processed
        # self.current_file_label = ctk.CTkLabel(self.main_frame, text=f"Processing: {file_path}", font=("Arial", 10))
        # self.current_file_label.pack(pady=20)

        self.status_label = ttk.Label(self.main_frame, text=f"Processing: {file_path.split('/')[-1]}", font=("Arial", 15))

        # set the background color of the label to red
        self.status_label.configure(background='red')

        self.status_label.pack(pady=10)

        self.preview_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, fg_color=self.fg_color)
        self.preview_frame.pack(pady=20)

        self.reference_images = [ctk.CTkLabel(self.preview_frame, text="") for _ in range(self.total_channels)]
        self.preview_images = [ctk.CTkLabel(self.preview_frame, text="") for _ in range(self.total_channels)]
        self.preview_labels = [ctk.CTkLabel(self.preview_frame, text=f"Reference for Channel {i+1}", font=("Arial", 10)) for i in range(self.total_channels)]

        for i, (preview_image, preview_label, reference_image) in enumerate(zip(self.preview_images, self.preview_labels, self.reference_images)):
            preview_label.grid(row=0, column=i)  # Arrange the text labels in a row below the image labels
            reference_image.grid(row=1, column=i)  # Arrange the labels in a row
            preview_image.grid(row=2, column=i)  # Arrange the labels in a row

        self.progress = ttk.Progressbar(self.main_frame, length=500, mode='determinate')
        self.progress.pack(pady=20)

        # add label under the progress bar to show the progress
        self.progress_label = ttk.Label(self.main_frame, text="0%", font=("Arial Bold", 16))
        self.progress_label.pack(pady=0)

    def load_image(self):
        self.file_status.set_default()   

        file_path = filedialog.askopenfilename()
        print("Selected file: ", file_path)

        self.to_process.append(file_path)

        self.start_processing()
        self.toggle_buttons()

    def load_directory(self):     
        self.file_status.set_default()   
        directory = filedialog.askdirectory() # '/Users/johnmacdonald/Downloads/lsm-alignment-tool/easy' # filedialog.askdirectory()
        print("Selected directory: ", directory)

        for file in glob.glob(directory + "/*.lsm"):
            self.to_process.append(file)

        # print("To Process: " + str(self.to_process))
        # time.sleep(10)
        # self.remaining_text = tk.StringVar()
        # self.remaining_label = ctk.CTkLabel(self.main_frame, textvariable=self.remaining_text, font=("Arial", 16))
        # self.remaining_label.pack(pady=40)

        self.start_processing()
        self.toggle_buttons()

    def specify_scaling(self):
        #creation of the scaling window
        self.scaling_window = ctk.CTk()
        self.scaling_window.title("Scaling Suite")
        self.scaling_label = ctk.CTkLabel(self.scaling_window, text = "Microscope and Image Settings", font=("Arial", 18))
        self.scaling_label.pack(padx = 10, pady = 20)

        #frames to hold all the buttons in a column
        x_frame = ctk.CTkFrame(self.scaling_window, corner_radius=15, fg_color=self.fg_color)
        x_frame.pack(pady=5)
        y_frame = ctk.CTkFrame(self.scaling_window, corner_radius=15, fg_color=self.fg_color)
        y_frame.pack(pady=5)
        z_frame = ctk.CTkFrame(self.scaling_window, corner_radius=15, fg_color=self.fg_color)
        z_frame.pack(pady=5)
        microscope_frame = ctk.CTkFrame(self.scaling_window, corner_radius = 15, fg_color = self.fg_color)
        microscope_frame.pack(pady=5)

        #Label and entry widgets to specify sizes
        self.x_label = ctk.CTkLabel(x_frame, text="X Voxel")
        self.x_label.pack(side ="left", padx = 10)
        self.x_entry = ctk.CTkEntry(x_frame)
        self.x_entry.pack(side="left", padx=10)

        #Label and entry widgets to specify sizes
        self.y_label = ctk.CTkLabel(y_frame, text="Y Voxel")
        self.y_label.pack(side ="left", padx = 10)
        self.y_entry = ctk.CTkEntry(y_frame)
        self.y_entry.pack(side="left", padx=10)

        #Label and entry widgets to specify sizes
        self.z_label = ctk.CTkLabel(z_frame, text="Z-Step")
        self.z_label.pack(side ="left", padx = 10)
        self.z_entry = ctk.CTkEntry(z_frame)
        self.z_entry.pack(side="left", padx=10)

        #miscroscope checkboxes
        self.is_510 = tk.BooleanVar()
        self.is_880 = tk.BooleanVar()
        self.lsm_510 = tk.Checkbutton(microscope_frame, text="LSM510", variable=self.is_510)
        self.lsm_510.pack(side="left")
        self.lsm_880 = tk.Checkbutton(microscope_frame, text="LSM880", variable=self.is_880)
        self.lsm_880.pack(side="left", padx=10)

        #confirm button
        confirm_button = ctk.CTkButton(self.scaling_window, text="Confirm", command=self.get_entries)
        confirm_button.pack()
    
    def get_entries(self):
        self.zstep = self.z_entry.get()
        self.xscale = Decimal(self.x_entry.get())
        self.yscale = Decimal(self.y_entry.get())
        self.resolution = Decimal("1.00")/self.xscale
        if(self.is_510.get()):
            self.lsm510 = 1
        elif(self.is_880.get()):
            self.lsm510 = 0
        else:
            self.lsm510 = 0 #assumption that the scope works as normal
        self.scaling_window.destroy()

    def refresh_ui(self):
        self.processed_channels = {}
        if hasattr(self, 'preview_frame'):
            self.preview_frame.destroy()

        # remove previous progress bar
        if hasattr(self, 'progress'):
            self.progress.destroy()

        # remove previous progress label
        if hasattr(self, 'progress_label'):
            self.progress_label.destroy()
        
        # remove previous reference images
        if hasattr(self, 'reference_images'):
            for reference_image in self.reference_images:
                reference_image.destroy()

        # remove previous preview images
        if hasattr(self, 'preview_images'):
            for preview_image in self.preview_images:
                preview_image.destroy()

        # remove previous preview labels
        if hasattr(self, 'preview_labels'):
            for preview_label in self.preview_labels:
                preview_label.destroy()

        # remove previous status label
        if hasattr(self, 'status_label'):
            self.status_label.destroy()

    def start_processing(self, file_path=None):
        self.file_status.update_remaining_files(len(self.to_process))

        if len(self.to_process) == 0:
            # fix: save resultant image at end
            self.toggle_buttons()
            self.refresh_ui()
            # self.file_status.set_default()
            return

        if file_path is None:
            file_path = self.to_process.pop()

        # loads in all the image data
        self.run_process(file_path)
        

        # self.start_button['state'] = 'disabled'
        # self.start_button['text'] = 'Processing...'

        self.progress['maximum'] = self.total_work

        self.processing_threads = []

        for i in range(self.total_channels):
            # i need to know exactly which thread is processing what channel, so recombination is easier
            processing_thread = Thread(target=self.process_image, args=(i, file_path))
            processing_thread.start()
            
            self.processing_threads.append(processing_thread)

        self.after(100, self.check_progress)

    def update_time_estimate(self):
        delta = time.time() - self.last_delta
        work_remaining = int((1.0 - (self.progress['value'] / self.progress['maximum'])) * self.total_work)

        if delta < 0.2:
            self.deltas.append(delta)
            self.stamps.append(time.time())

            # let subset be the subset of self.deltas which contains deltas < 1 std dev

            if len(self.deltas) > 3:
                self.averages.append(np.mean(self.deltas[3:]))
                self.last_estimate = self.averages[-1] * work_remaining
                # print(delta, self.average_delta, self.remain_estimate, work_remaining)
                # use this to update the average delta

                self.new_estimate = self.averages[-1] * work_remaining
                suffix = "s" if int(self.new_estimate) > 1 else ""
                # self.remaining_text.set(f"{len(self.to_process)} files remaining / {self.completed} file{'s' if self.completed > 1 else ''} completed / {int(self.new_estimate)} second{suffix} remaining")
                # self.title(f"Image Processing App - {self.remaining_label['text']}")
                self.file_status.update_seconds_remaining(int(self.new_estimate))

        self.last_delta = time.time()
    # np = 1.22.0
    def process_image(self, channel, file_path):
        # bug here w.r.t the channel, redeclaring the array
        print("Processing channel {}".format(channel))
        self.file_currently_processing = file_path

        # track the time it takes to process the image in seconds
        start_time = time.time()
        processed_channel = process_channel(self.image_data[:, channel, :, :], channel, self.progress, self.progress_label, self.preview_images[channel], self.reference_images[channel], self.update_time_estimate)
        end_time = time.time()

        self.last_delta = end_time - start_time

        # no, processed_channels needs to be a map
        self.processed_channels[channel] = processed_channel

    def save_image(self):
        if len(self.processed_channels.keys()) == 0:
            print("Nothing to save!")
            return
        
        #modifying the ordering of the channels if it is the Luikart microscope, lsm510
        ordering = list(range(len(self.processed_channels.keys())))
        if(self.lsm510): #the lsm510 switches things around
            ordering[0], ordering[1] = ordering[1], ordering[0]

        new_image = np.array([self.processed_channels[x] for x in ordering])
        new_image = new_image.transpose((1, 0, 2, 3))
        
        tiff = np.array(new_image)
        tiff = tiff.astype(np.uint8)

        dpi = float(self.resolution) # int(pixels_per_micrometer * 25400)

        spacing = self.zstep
        image_metadata = {'axes':'ZCYX', 'mode':'color', 'unit': 'um', 'spacing': spacing}
        
        print("Saving: " + self.file_currently_processing)
        imwrite(f'./output/{self.file_currently_processing.split("/")[-1]}_DESPEC.tiff', tiff, resolution=(dpi, dpi), imagej = True, metadata=image_metadata)
        
        self.processed_channels = {}
        self.file_status.update_completed_files()

    def check_progress(self):
        if any([thread.is_alive() for thread in self.processing_threads]):
            self.after(100, self.check_progress)
        else:
            # Process your result here
            # thread = Thread(target=self.save_image, daemon=True)
            # thread.start()

            self.save_image()
            time.sleep(2)
           
            # set the progress bar to 100%
            self.progress['value'] = self.total_work

            self.start_processing()


if __name__ == "__main__":
    app = Application()
    app.mainloop()

# takes 53.261276960372925 seconds to fully run across image