import cv2
import sys
import time
import os
from run_ncnn import NCNNRunner

import board
import busio
from adafruit_pca9685 import PCA9685

# Setup PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pwm = PCA9685(i2c)
pwm.frequency = 50

# Motor channel grup 1 (Cylinder)
MOTOR_CYLINDER_CHANNELS = [1, 14]

# Motor channel grup 2 (Gate)
MOTOR_GATE_CHANNELS = [5, 10]

PWM_MIN = 750      # Motor mati / idle
PWM_MEDIUM = 1300  # Kecepatan sedang
PWM_SLOW = 1000    # Kecepatan lambat

# Toleransi jarak cylinder (cm)
CYLINDER_TARGET_DISTANCE = 180
DISTANCE_TOLERANCE = 10

def set_motor_throttle(channel, throttle_us):
    pwm_value = int((throttle_us / 20000) * 65535)
    pwm.channels[channel].duty_cycle = pwm_value

def run_realtime_multiobj(model_path="yolo11n_ncnn_model", confidence_thres=0.5, iou_thres=0.45, save_threshold=0.6):
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
    for ch in MOTOR_CYLINDER_CHANNELS + MOTOR_GATE_CHANNELS:
        set_motor_throttle(ch, PWM_MIN)
    time.sleep(3)
    print("Motor siap...")

    motor_cylinder_active = False

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

            # Kontrol motor Cylinder channel 1 & 14
            if cylinder_distance is not None and abs(cylinder_distance - CYLINDER_TARGET_DISTANCE) <= DISTANCE_TOLERANCE:
                if not motor_cylinder_active:
                    print(f"Cylinder terdeteksi pada jarak {cylinder_distance:.1f}cm. Menyalakan motor channel 1 & 14...")
                motor_cylinder_active = True
                for ch in MOTOR_CYLINDER_CHANNELS:
                    set_motor_throttle(ch, PWM_MEDIUM)

                # Jika motor cylinder menyala, matikan motor gate
                for ch in MOTOR_GATE_CHANNELS:
                    set_motor_throttle(ch, PWM_MIN)
                status_gate_motor = "Motor gate channel 5 & 10: MATI (Cylinder motor menyala)"
            else:
                if motor_cylinder_active:
                    print("Cylinder tidak terdeteksi di jarak target. Mematikan motor channel 1 & 14 dan menyalakan motor gate...")
                motor_cylinder_active = False
                for ch in MOTOR_CYLINDER_CHANNELS:
                    set_motor_throttle(ch, PWM_MIN)

                # Motor gate menyala dengan kecepatan tergantung deteksi gate
                if gate_detected:
                    for ch in MOTOR_GATE_CHANNELS:
                        set_motor_throttle(ch, PWM_SLOW)
                    status_gate_motor = "Motor gate channel 5 & 10: LAMBAT (Gate detected)"
                else:
                    for ch in MOTOR_GATE_CHANNELS:
                        set_motor_throttle(ch, PWM_MEDIUM)
                    status_gate_motor = "Motor gate channel 5 & 10: SEDANG (No gate)"

            # Tampilkan status FPS dan motor
            end_time = time.time()
            fps = 1 / (end_time - start_time)
            status = "Screenshot: ON" if screenshot_enabled else "Screenshot: OFF"

            motor_cyl_status = "ON" if motor_cylinder_active else "OFF"

            cv2.putText(dimg, f"FPS: {fps:.2f} | {status}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)

            cv2.putText(dimg, f"Cylinder Motor (1&14): {motor_cyl_status}", (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            cv2.putText(dimg, status_gate_motor, (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

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
        for ch in MOTOR_CYLINDER_CHANNELS + MOTOR_GATE_CHANNELS:
            set_motor_throttle(ch, PWM_MIN)
        pwm.deinit()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    model_dir = sys.argv[1] if len(sys.argv) > 1 else "yolo11n_ncnn_model"
    run_realtime_multiobj(model_path=model_dir)
