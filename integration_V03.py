import cv2
import sys
import time
import os
from run_ncnn import NCNNRunner
import random

import board
import busio
from adafruit_pca9685 import PCA9685

# Setup PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pwm = PCA9685(i2c)
pwm.frequency = 50

# Motor channel grup
MOTOR_CHANNELS = {
    "motor_1": 1,
    "motor_2": 14,
    "motor_3": 3,
    "motor_4": 12,
    "motor_5": 5,
    "motor_6": 10
}

PWM_MIN = 700      # Motor mati / idle
PWM_MAX = 2000     # Motor full speed
PWM_MEDIUM = 1300  # Kecepatan sedang
PWM_SLOW = 1000    # Kecepatan lambat

# Toleransi jarak cylinder dan gawang (cm)
CYLINDER_CLOSE_DISTANCE = 150  # Jarak silinder untuk mundur
CYLINDER_AWAY_DISTANCE = 200   # Jarak silinder untuk ke kiri atau kanan
GATE_DISTANCE = 180
DISTANCE_TOLERANCE = 10

def set_motor_throttle(channel, throttle_us):
    pwm_value = int((throttle_us / 20000) * 65535)
    pwm.channels[channel].duty_cycle = pwm_value

def move_forward():
    # Motor 5 dan 6 untuk maju
    set_motor_throttle(MOTOR_CHANNELS["motor_5"], PWM_MEDIUM)
    set_motor_throttle(MOTOR_CHANNELS["motor_6"], PWM_MEDIUM)

def move_backward():
    # Motor 1 dan 2 untuk mundur
    set_motor_throttle(MOTOR_CHANNELS["motor_1"], PWM_MEDIUM)
    set_motor_throttle(MOTOR_CHANNELS["motor_2"], PWM_MEDIUM)

def move_left():
    # Motor 1 dan 5 untuk ke kiri
    set_motor_throttle(MOTOR_CHANNELS["motor_1"], PWM_MEDIUM)
    set_motor_throttle(MOTOR_CHANNELS["motor_5"], PWM_MEDIUM)

def move_right():
    # Motor 2 dan 6 untuk ke kanan
    set_motor_throttle(MOTOR_CHANNELS["motor_2"], PWM_MEDIUM)
    set_motor_throttle(MOTOR_CHANNELS["motor_6"], PWM_MEDIUM)

def move_down():
    # Motor 3 dan 12 untuk turun
    set_motor_throttle(MOTOR_CHANNELS["motor_3"], PWM_MAX)
    set_motor_throttle(MOTOR_CHANNELS["motor_4"], PWM_MAX)

def move_up():
    # Motor 3 dan 12 untuk naik
    set_motor_throttle(MOTOR_CHANNELS["motor_3"], PWM_MIN)
    set_motor_throttle(MOTOR_CHANNELS["motor_4"], PWM_MIN)

def stop_all_motors():
    # Semua motor mati
    for ch in MOTOR_CHANNELS.values():
        set_motor_throttle(ch, PWM_MIN)

def run_realtime_multiobj(model_path="obstacle_ncnn_model", confidence_thres=0.5, iou_thres=0.45, save_threshold=0.6):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Tidak dapat membuka kamera.")
        return

    detector = NCNNRunner(model_path)

    class_widths = {
        "Cylinder": 32,
        "Gate": 184
    }
    class_focus = {
        "Cylinder": 712,
        "Gate": 761
    }

    output_dir = "screenshots"
    os.makedirs(output_dir, exist_ok=True)

    screenshot_enabled = False

    print("Tekan 's' untuk AKTIF/NONAKTIFKAN screenshot otomatis.")
    print("Tekan 'q' untuk keluar.")

    # Arming semua motor ke PWM_MIN
    stop_all_motors()
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
            cylinder_distance = None

            for i in range(len(box_got)):
                box = box_got[i]
                score = score_got[i]
                class_id = class_id_got[i]
                x, y, w, h = int(box[0]), int(box[1]), int(box[2]), int(box[3])

                class_name = detector.class_names[class_id]
                W_cm = class_widths.get(class_name, None)
                f_px = class_focus.get(class_name, None)

                if W_cm is not None and f_px is not None and w != 0:
                    d_cm = (W_cm * f_px) / w
                else:
                    d_cm = None

                label_dist = f"{d_cm:.1f}cm" if d_cm is not None else "Unknown"

                label = f"{class_name} | {score:.2f} | w:{w}px | d:{label_dist}"
                cv2.rectangle(dimg, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(dimg, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (36, 255, 12), 2)

                if screenshot_enabled and score >= save_threshold:
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    filename = os.path.join(output_dir, f"detected_{class_name}_{timestamp}.jpg")
                    cv2.imwrite(filename, dimg)
                    print(f"[?] Foto disimpan: {filename}")

                if class_name == "Gate" and score >= confidence_thres:
                    gate_detected = True

                if class_name == "Cylinder" and score >= confidence_thres and d_cm is not None:
                    cylinder_distance = d_cm

            # Kontrol robot berdasarkan deteksi objek 
            if cylinder_distance is not None and abs(cylinder_distance - CYLINDER_AWAY_DISTANCE) <= DISTANCE_TOLERANCE:
                # Jika Cylinder terdeteksi pada jarak ~200 cm, robot bergerak ke kiri atau kanan untuk menghindar
                print(f"Cylinder terdeteksi pada jarak {cylinder_distance:.1f}cm. Robot menghindar...")
                if random.choice([True, False]):
                    move_left()
                else:
                    move_right()
                    
                while time.time() - start_escape_time < 10:
                    pass 
                robot_active = False
            elif gate_detected:
                # Jika Gate terdeteksi, robot akan bergerak lebih lambat
                print("Gate terdeteksi. Robot bergerak lebih lambat...")
                set_motor_throttle(MOTOR_CHANNELS["motor_5"], PWM_SLOW)
                set_motor_throttle(MOTOR_CHANNELS["motor_6"], PWM_SLOW)
            elif robot_active:
                # Robot bergerak maju jika tidak ada halangan
                move_forward()
                move_downS()


            # Tampilkan status FPS dan motor
            end_time = time.time()
            fps = 1 / (end_time - start_time)
            status = "Screenshot: ON" if screenshot_enabled else "Screenshot: OFF"
            cv2.putText(dimg, f"FPS: {fps:.2f} | {status}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 2)

            cv2.imshow("Deteksi + Kendali Motor", dimg)

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
        stop_all_motors()
        pwm.deinit()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    model_dir = sys.argv[1] if len(sys.argv) > 1 else "obstacle_ncnn_model"
    run_realtime_multiobj(model_path=model_dir)
