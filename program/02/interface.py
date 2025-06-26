import tkinter as tk
from tkinter import Label, Button
import cv2
from PIL import Image, ImageTk
from main import RobotControl
import os

class RobotControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Control and Object Detection")
        self.root.geometry("800x600")

        # Inisialisasi RobotControl
        self.robot_control = RobotControl()

        # Load images for buttons
        self.arrow_up_img = ImageTk.PhotoImage(Image.open("arrow_up.png").resize((50, 50)))
        self.arrow_down_img = ImageTk.PhotoImage(Image.open("arrow_down.png").resize((50, 50)))
        self.arrow_left_img = ImageTk.PhotoImage(Image.open("arrow_left.png").resize((50, 50)))
        self.arrow_right_img = ImageTk.PhotoImage(Image.open("arrow_right.png").resize((50, 50)))

        # Label untuk menampilkan feed kamera
        self.image_label = Label(self.root)
        self.image_label.pack(side=tk.TOP, pady=10)

        # Frame untuk tombol arah
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.LEFT, padx=20, pady=20)

        # Tombol panah
        self.move_up_btn = Button(control_frame, image=self.arrow_up_img, command=self.robot_control.move_up)
        self.move_up_btn.grid(row=0, column=1, padx=5, pady=5)

        self.move_left_btn = Button(control_frame, image=self.arrow_left_img, command=self.robot_control.move_left)
        self.move_left_btn.grid(row=1, column=0, padx=5, pady=5)

        self.move_down_btn = Button(control_frame, image=self.arrow_down_img, command=self.robot_control.move_down)
        self.move_down_btn.grid(row=1, column=1, padx=5, pady=5)

        self.move_right_btn = Button(control_frame, image=self.arrow_right_img, command=self.robot_control.move_right)
        self.move_right_btn.grid(row=1, column=2, padx=5, pady=5)

        # Tombol untuk maju dan mundur (bisa pakai ikon lain jika ada)
        self.move_forward_btn = Button(control_frame, text="Forward", command=self.robot_control.move_forward)
        self.move_forward_btn.grid(row=2, column=1, padx=5, pady=5)

        self.move_backward_btn = Button(control_frame, text="Backward", command=self.robot_control.move_backward)
        self.move_backward_btn.grid(row=3, column=1, padx=5, pady=5)

        self.stop_btn = Button(self.root, text="Stop", command=self.robot_control.stop_all_motors, bg="red", fg="white")
        self.stop_btn.pack(side=tk.BOTTOM, pady=10)

        # Memperbarui frame setiap 30ms
        self.update_frame()

    def update_frame(self):
        frame = self.robot_control.get_frame()
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img = ImageTk.PhotoImage(img)
            self.image_label.config(image=img)
            self.image_label.image = img
        self.root.after(30, self.update_frame)

    def close(self):
        self.robot_control.release_resources()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()
