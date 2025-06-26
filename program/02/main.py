from motor_control import MotorControl
from run_ncnn import NCNNRunner
import cv2
import os
import time
import random

class RobotControl:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.motor_control = MotorControl()

    def get_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

    def release_resources(self):
        if self.cap.isOpened():
            self.cap.release()

    # Fungsi kontrol motor
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

    def run_realtime_multiobj(model_path="obstacle_ncnn_model", confidence_thres=0.8, iou_thres=0.45, save_threshold=0.6):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Tidak dapat membuka kamera.")
            return

        detector = NCNNRunner(model_path)
        motor_control = MotorControl()

        output_dir = "screenshots"
        os.makedirs(output_dir, exist_ok=True)

        screenshot_enabled = False
        print("Tekan 's' untuk AKTIF/NONAKTIFKAN screenshot otomatis.")
        print("Tekan 'q' untuk keluar.")
        
        motor_control.stop_all_motors()
        time.sleep(3)

        robot_active = True
        try:
            while True:
                start_time = time.time()
                ret, frame = cap.read()
                if not ret:
                    print("Gagal membaca frame.")
                    break

                im2 = detector.preprocess(frame)
                y = detector.predict(im2)
                r = detector.postprocess(frame, y, confidence_thres, iou_thres)

                dimg = frame.copy()
                box_got, score_got, class_id_got = r

                gate_detected = False
                cylinder_detected = False

                for i in range(len(box_got)):
                    box = box_got[i]
                    score = score_got[i]
                    class_id = class_id_got[i]
                    class_name = detector.class_names[class_id]

                    if class_name == "Gate" and score >= confidence_thres:
                        gate_detected = True

                    if class_name == "Cylinder" and score >= confidence_thres:
                        cylinder_detected = True

                if cylinder_detected:
                    print("Silinder terdeteksi. Robot bergerak ke kiri atau kanan secara acak...")
                    motor_control.move_down()
                    if random.choice([True, False]):
                        motor_control.move_left()
                        arah = "kiri"
                    else:
                        motor_control.move_right()
                        arah = "kanan"

                    print(f"Robot bergerak ke {arah} ...")
                    time.sleep(0)  
                    motor_control.stop_all_motors()
                    robot_active = True

                elif gate_detected:
                    print("Gate terdeteksi. Robot bergerak lebih lambat...")
                    motor_control.set_motor_throttle(5, 1000)
                    motor_control.set_motor_throttle(6, 1000)

                elif robot_active:
                    motor_control.move_forward()

                end_time = time.time()
                fps = 1 / (end_time - start_time)
                status = "Screenshot: ON" if screenshot_enabled else "Screenshot: OFF"
                cv2.putText(dimg, f"FPS: {fps:.2f} | {status}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                cv2.imshow("POLROV", dimg)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    screenshot_enabled = not screenshot_enabled
                    print(f"[i] Screenshot sekarang {'AKTIF' if screenshot_enabled else 'NONAKTIF'}")

        except KeyboardInterrupt:
            print("Program dihentikan.")
        finally:
            print("Menghentikan semua motor dan membersihkan...")
            motor_control.stop_all_motors()
            cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    model_dir = "obstacle_ncnn_model"
    run_realtime_multiobj(model_path=model_dir)
