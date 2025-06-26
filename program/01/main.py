import time
from motor_control import MotorControl
from ncnn_runner import NCNNRunner
import cv2

# Inisialisasi kontrol motor dan deteksi objek
motor_control = MotorControl()
detector = NCNNRunner(model_path="obstacle_ncnn_model")

def run_detection():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Menjalankan deteksi objek menggunakan NCNNRunner
        result = detector.run(frame)

        # Update confidence berdasarkan hasil deteksi
        cylinder_confidence = 0
        gate_confidence = 0
        for i in range(len(result[0])):
            class_name = detector.class_names[result[2][i]]
            score = result[1][i]

            # Update confidence untuk Cylinder dan Gate
            if class_name == "Cylinder" and score > cylinder_confidence:
                cylinder_confidence = score
            if class_name == "Gate" and score > gate_confidence:
                gate_confidence = score

        # Kontrol pergerakan robot berdasarkan confidence
        motor_control.move_based_on_confidence(cylinder_confidence, gate_confidence, 
                                                detector.Cylinder_CONFIDENCE_THRESHOLD, 
                                                detector.Gate_CONFIDENCE_THRESHOLD)

        # Tekan 'q' untuk keluar
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_detection()
