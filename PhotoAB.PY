import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import pygame.camera
import os
import threading
import time
import cv2
import numpy as np
import subprocess

class PhotoBoothApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PhotoAB")
        self.root.geometry("400x500")
        self.root.resizable(True, True)
        
        self.resolution_options = [(160, 120), (320, 240), (640, 480), (800, 600), (1024, 768), (1280, 720), (1920, 1080)]
        self.interval_options = [1, 2, 3, 5]
        
        self.save_directory = tk.StringVar()
        self.resolution_var = tk.StringVar(root, value="1280x720")
        self.interval_var = tk.StringVar(root, value="3")
        self.is_capturing = False
        self.window_name = "PhotoAB"
        self.capture_thread = None
        
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Helvetica', 10))
        self.style.configure('TLabel', font=('Helvetica', 10))
        
        # Grid layout
        ttk.Label(root, text="Resolution:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.resolution_menu = ttk.Combobox(root, textvariable=self.resolution_var, values=["x".join(map(str, res)) for res in self.resolution_options], state="readonly")
        self.resolution_menu.grid(row=0, column=1, padx=5, pady=5)
        self.resolution_menu.current(5)
        
        ttk.Label(root, text="Interval (seconds):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.interval_menu = ttk.Combobox(root, textvariable=self.interval_var, values=self.interval_options, state="readonly")
        self.interval_menu.grid(row=1, column=1, padx=5, pady=5)
        self.interval_menu.current(2)
        
        ttk.Label(root, text="Save Directory:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.save_directory_label = ttk.Label(root, textvariable=self.save_directory, wraplength=300)
        self.save_directory_label.grid(row=2, column=1, padx=5, pady=5)
        
        self.start_button = ttk.Button(root, text="Start", command=self.start_capture)
        self.start_button.grid(row=3, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(root, text="Stop", command=self.stop_capture, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, padx=5, pady=5)
        
        self.save_button = ttk.Button(root, text="Select Folder", command=self.choose_save_directory)
        self.save_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="we")
        
        self.open_button = ttk.Button(root, text="Open Folder", command=self.open_save_directory)
        self.open_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="we")
        
        self.run_for_button = ttk.Button(root, text="Run For", command=self.run_for_duration)
        self.run_for_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="we")
        
        self.quit_button = ttk.Button(root, text="Quit", command=root.quit)
        self.quit_button.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="we")
        
    def start_capture(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        resolution_str = self.resolution_var.get().split("x")
        resolution = (int(resolution_str[0]), int(resolution_str[1]))
        interval = int(self.interval_var.get())
        
        self.is_capturing = True
        self.capture_thread = threading.Thread(target=self.capture_photos, args=(resolution, interval))
        self.capture_thread.start()
        
    def capture_photos(self, resolution, interval):
        try:
            pygame.camera.init()
            cam_list = pygame.camera.list_cameras()
            if not cam_list:
                print("No cameras detected.")
                return

            camera = pygame.camera.Camera(cam_list[0], resolution)
            camera.start()

            cv2.namedWindow(self.window_name)

            start_time = time.time()

            while self.is_capturing:
                frame = camera.get_image()
                frame = pygame.transform.scale(frame, resolution)
                frame = pygame.surfarray.array3d(frame)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Rotate and flip the image if necessary
                if frame.shape[0] > frame.shape[1]:
                    frame = np.rot90(frame, -1)
                    frame = np.fliplr(frame)  # Horizontal flip

                cv2.imshow(self.window_name, frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop_capture()

                current_time = time.time()
                if current_time - start_time >= interval:
                    start_time = current_time
                    if self.save_directory.get():
                        filename = f"photo_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                        cv2.imwrite(os.path.join(self.save_directory.get(), filename), frame)

            camera.stop()
            pygame.camera.quit()
            cv2.destroyAllWindows()
        except Exception as e:
            print("Error capturing photos:", e)
        
        self.start_button.config(state=tk.NORMAL)
                
    def stop_capture(self):
        if self.is_capturing:
            self.is_capturing = False

    def choose_save_directory(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.save_directory.set(folder_selected)

    def open_save_directory(self):
        folder_path = self.save_directory.get()
        if folder_path:
            os.startfile(folder_path)
        else:
            messagebox.showwarning("Warning", "No folder selected to save photos.")

    def run_for_duration(self):
        duration_dialog = DurationDialog(self.root)
        self.root.wait_window(duration_dialog.top)
        duration = duration_dialog.result

        if duration:
            self.start_capture()
            self.root.after(duration * 1000, self.stop_capture)

class DurationDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Duration")
        self.top.geometry("200x100")
        self.top.resizable(False, False)
        
        self.result = None
        
        ttk.Label(self.top, text="Duration (seconds):").pack(pady=5, anchor="center")
        self.duration_entry = ttk.Entry(self.top)
        self.duration_entry.pack(pady=5, anchor="center")
        
        self.confirm_button = ttk.Button(self.top, text="Confirm", command=self.confirm_duration)
        self.confirm_button.pack(pady=5, anchor="center")
        
    def confirm_duration(self):
        duration_str = self.duration_entry.get()
        try:
            duration = int(duration_str)
            if duration > 0:
                self.result = duration
                self.top.destroy()
            else:
                messagebox.showerror("Error", "Enter a valid value (greater than zero).")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid integer value.")

def main():
    root = tk.Tk()
    app = PhotoBoothApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
