import tkinter as tk
from tkinter import Label, Button
import cv2
from PIL import Image, ImageTk
from main import RobotControl

class RobotControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Control and Object Detection")
        self.root.geometry("800x600")

        # Inisialisasi RobotControl
        self.robot_control = RobotControl()

        # Label untuk menampilkan feed kamera
        self.image_label = Label(self.root)
        self.image_label.pack()

        # Tombol untuk kontrol manual motor
        self.move_forward_btn = Button(self.root, text="Move Forward", command=self.robot_control.move_forward)
        self.move_forward_btn.pack()

        self.move_backward_btn = Button(self.root, text="Move Backward", command=self.robot_control.move_backward)
        self.move_backward_btn.pack()

        self.move_left_btn = Button(self.root, text="Move Left", command=self.robot_control.move_left)
        self.move_left_btn.pack()

        self.move_right_btn = Button(self.root, text="Move Right", command=self.robot_control.move_right)
        self.move_right_btn.pack()

        self.move_up_btn = Button(self.root, text="Move Up", command=self.robot_control.move_up)
        self.move_up_btn.pack()

        self.move_down_btn = Button(self.root, text="Move Down", command=self.robot_control.move_down)
        self.move_down_btn.pack()

        self.stop_btn = Button(self.root, text="Stop", command=self.robot_control.stop_all_motors)
        self.stop_btn.pack()

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
