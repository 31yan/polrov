from motor_control import MotorControl
from ncnn_runner import NCNNRunner
import cv2
import os
import time
import random

class RobotControl:
    def __init__(self, model_path="obstacle_ncnn_model", confidence_thres=0.8, iou_thres=0.45, save_threshold=0.6):
        self.model_path = model_path
        self.confidence_thres = confidence_thres
        self.iou_thres = iou_thres
        self.save_threshold = save_threshold

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Tidak dapat membuka kamera.")
            self.cap = None
            return

        self.detector = NCNNRunner(self.model_path)
        self.motor_control = MotorControl()

        self.output_dir = "screenshots"
        os.makedirs(self.output_dir, exist_ok=True)

        self.screenshot_enabled = False
        self.robot_active = True

    def run(self):
        if self.cap is None:
            print("Kamera tidak tersedia.")
            return

        print("Tekan 's' untuk AKTIF/NONAKTIFKAN screenshot otomatis.")
        print("Tekan 'q' untuk keluar.")

        self.motor_control.stop_all_motors()
        time.sleep(3)

        try:
            while True:
                start_time = time.time()
                ret, frame = self.cap.read()
                if not ret:
                    print("Gagal membaca frame.")
                    break

                im2 = self.detector.preprocess(frame)
                y = self.detector.predict(im2)
                r = self.detector.postprocess(frame, y, self.confidence_thres, self.iou_thres)

                dimg = frame.copy()
                box_got, score_got, class_id_got = r

                gate_detected = False
                cylinder_detected = False

                for i in range(len(box_got)):
                    box = box_got[i]
                    score = score_got[i]
                    class_id = class_id_got[i]
                    class_name = self.detector.class_names[class_id]

                    if class_name == "Gate" and score >= self.confidence_thres:
                        gate_detected = True

                    if class_name == "Cylinder" and score >= self.confidence_thres:
                        cylinder_detected = True

                if cylinder_detected:
                    print("Silinder terdeteksi. Robot bergerak ke kiri atau kanan secara acak...")
                    self.motor_control.move_down()
                    if random.choice([True, False]):
                        self.motor_control.move_left()
                        arah = "kiri"
                    else:
                        self.motor_control.move_right()
                        arah = "kanan"

                    print(f"Robot bergerak ke {arah} ...")
                    time.sleep(0)
                    self.motor_control.stop_all_motors()
                    self.robot_active = True

                elif gate_detected:
                    print("Gate terdeteksi. Robot bergerak lebih lambat...")
                    self.motor_control.set_motor_throttle(5, 1000)
                    self.motor_control.set_motor_throttle(6, 1000)

                elif self.robot_active:
                    self.motor_control.move_forward()

                end_time = time.time()
                fps = 1 / (end_time - start_time)
                status = "Screenshot: ON" if self.screenshot_enabled else "Screenshot: OFF"
                cv2.putText(dimg, f"FPS: {fps:.2f} | {status}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                cv2.imshow("POLROV", dimg)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.screenshot_enabled = not self.screenshot_enabled
                    print(f"[i] Screenshot sekarang {'AKTIF' if self.screenshot_enabled else 'NONAKTIF'}")

        except KeyboardInterrupt:
            print("Program dihentikan.")
        finally:
            print("Menghentikan semua motor dan membersihkan...")
            self.motor_control.stop_all_motors()
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()

    def move_forward(self):
        self.motor_control.move_forward()

    def move_backward(self):
        self.motor_control.move_backward()

    def move_left(self):
        self.motor_control.move_left()

    def move_right(self):
        self.motor_control.move_right()

    def move_up(self):
        self.motor_control.move_up()

    def move_down(self):
        self.motor_control.move_down()

    def stop_all_motors(self):
        self.motor_control.stop_all_motors()

    def get_frame(self):
        if self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

    def release_resources(self):
        self.stop_all_motors()
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    robot = RobotControl()
    robot.run()
