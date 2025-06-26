import ncnn as pyncnn
import yaml
import os
import sys
import numpy as np
import torch
import cv2
import random
import time

# Pengaturan lebar objek (dalam cm) dan panjang fokus kamera (dalam piksel) untuk objek Cylinder dan Gate
class_widths = {
    "Cylinder": 32,  # Lebar silinder dalam cm
    "Gate": 86       # Lebar gerbang dalam cm
}

class_focus = {
    "Cylinder": 712,  # Panjang fokus silinder dalam piksel
    "Gate": 686       # Panjang fokus gerbang dalam piksel
}

class NCNNRunner:
    def __init__(self, model_path, use_gpu=False):
        """
        Menginisialisasi model NCNN dan memuat file yang diperlukan untuk prediksi.
        """
        self.model_path = model_path
        self.net = pyncnn.Net()
        self.net.opt.use_vulkan_compute = use_gpu  # Menyalakan dukungan GPU jika tersedia
        param_path = os.path.join(model_path, "model.ncnn.param")
        
        # Memeriksa apakah file parameter model ada
        if not os.path.exists(param_path):
            print("param file not found")
            sys.exit(1)
        self.net.load_param(param_path)

        model_bin = os.path.join(model_path, "model.ncnn.bin")
        # Memeriksa apakah file binary model ada
        if not os.path.exists(model_bin):
            print("bin file not found")
            sys.exit(1)
        self.net.load_model(model_bin)

        self.metadata = os.path.join(model_path, "metadata.yaml")
        # Memeriksa apakah file metadata ada
        if not os.path.exists(self.metadata):
            print("metadata file not found")
            sys.exit(1)
        
        # Memuat informasi tentang kelas objek dan ukuran input model
        with open(self.metadata, 'r') as f:
            data = yaml.safe_load(f)
        self.model_input_shape = data["imgsz"]
        self.class_names = data["names"]

        # Menetapkan ambang batas confidence untuk masing-masing objek
        self.Cylinder_CONFIDENCE_THRESHOLD = 0.85
        self.Gate_CONFIDENCE_THRESHOLD = 0.80

    def pre_transform(self, img):
        """
        Memproses gambar input dengan mengubah ukuran dan menambahkan padding agar sesuai dengan ukuran input model.
        """
        shape = img.shape[:2]  # Mendapatkan bentuk gambar [tinggi, lebar]
        new_shape = self.model_input_shape  # Ukuran yang diinginkan
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])  # Rasio skala

        # Menghitung padding
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
        dw /= 2  # Membagi padding ke dua sisi
        dh /= 2

        # Resize dan padding gambar
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        img = cv2.copyMakeBorder(img, int(round(dh - 0.1)), int(round(dh + 0.1)), 
                                  int(round(dw - 0.1)), int(round(dw + 0.1)), 
                                  cv2.BORDER_CONSTANT, value=(114, 114, 114))
        return img

    def preprocess(self, img):
        """
        Memproses gambar sebelum dimasukkan ke dalam model NCNN.
        """
        img2 = np.stack([self.pre_transform(img)])  # Mengubah format gambar
        img2 = img2[..., ::-1].transpose((0, 3, 1, 2))  # Mengubah BGR ke RGB dan format array
        img2 = np.ascontiguousarray(img2)  # Memastikan array bersifat contiguous
        img2 = torch.from_numpy(img2)
        img2 = img2.float()
        img2 /= 255  # Menormalkan gambar ke rentang [0, 1]
        return img2

    def predict(self, img2):
        """
        Melakukan prediksi pada gambar yang sudah diproses.
        """
        b, ch, h, w = img2.shape  # Mendapatkan informasi dimensi gambar
        mat_in = pyncnn.Mat(img2[0].cpu().numpy())  # Mengonversi gambar ke format NCNN
        with self.net.create_extractor() as ex:
            ex.input(self.net.input_names()[0], mat_in)  # Memasukkan gambar ke dalam model
            output = [np.array(ex.extract(x)[1])[None] for x in sorted(self.net.output_names())]
        return output

    def postprocess(self, input_image, output, confidence_thres, iou_thres):
        """
        Memproses hasil prediksi untuk mengekstrak bounding boxes dan ID kelas.
        """
        outputs = np.transpose(np.squeeze(output[0]))
        rows = outputs.shape[0]
        boxes, scores, class_ids = [], [], []

        input_image_height, input_image_width = input_image.shape[:2]
        model_input_height, model_input_width = self.model_input_shape
        ratio = (input_image_width / model_input_width, input_image_height / model_input_height)

        # Memproses output dan memfilter berdasarkan threshold confidence
        for i in range(rows):
            classes_scores = outputs[i][4:]
            max_score = np.amax(classes_scores)
            if max_score >= confidence_thres:
                class_id = np.argmax(classes_scores)
                x, y, w, h = outputs[i][:4]
                left = (x - w / 2)
                top = (y - h / 2)
                boxes.append([left, top, w, h])
                scores.append(max_score)
                class_ids.append(class_id)

        # Non-Maximum Suppression
        indices = cv2.dnn.NMSBoxes(boxes, scores, confidence_thres, iou_thres)

        # Mengambil box yang terpilih berdasarkan NMS
        boxes = np.array(boxes)[indices]
        scores = np.array(scores)[indices]
        class_ids = np.array(class_ids)[indices]

        # Menghapus padding dari bounding box
        for b in boxes:
            b[0] -= self.dw
            b[1] -= self.dh

        # Kembalikan tiga elemen terpisah
        return boxes, scores, class_ids

    def calculate_distance(self, class_name, width, focal_length):
        """
        Menghitung jarak ke objek berdasarkan lebar objek dan panjang fokus kamera.
        """
        W_cm = class_widths.get(class_name)  # Mendapatkan lebar objek dalam cm
        if W_cm:
            return (W_cm * focal_length) / width  # Menghitung jarak menggunakan rumus
        return None  # Jika nama kelas tidak ada dalam dictionary

    def run(self, input_image, show=True, confidence_thres=0.5, iou_thres=0.45):
        """
        Menjalankan seluruh pipeline deteksi objek pada gambar input.
        """
        im2 = self.preprocess(input_image)  # Preprocessing gambar
        output = self.predict(im2)  # Prediksi objek
        boxes, scores, class_ids = self.postprocess(input_image, output, confidence_thres, iou_thres)  # Memproses hasil prediksi

        # Menghitung jarak untuk setiap objek
        for i in range(len(boxes)):
            class_name = self.class_names[class_ids[i]]
            x, y, w, h = boxes[i]
            focal_length = class_focus.get(class_name, 700)  # Mengambil panjang fokus berdasarkan objek
            distance = self.calculate_distance(class_name, w, focal_length)  # Menghitung jarak
            print(f"Jarak ke {class_name}: {distance} cm")

        if show:
            self.show(input_image, (boxes, scores, class_ids))  # Menampilkan hasil deteksi
        return boxes, scores, class_ids

    def show(self, input_image, output):
        """
        Menampilkan gambar dengan bounding box dan label kelas.
        """
        boxes, scores, class_ids = output  # Memastikan output sudah berisi 3 elemen yang benar
        dimg = input_image.copy()

        for i in range(len(boxes)):
            x, y, w, h = boxes[i]
            score = scores[i]
            class_id = class_ids[i]
            cv2.rectangle(dimg, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 0), 2)
            cv2.putText(dimg, f"{self.class_names[class_id]} {score:.2f}", 
                        (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        # Simpan gambar hasil deteksi
        cv2.imwrite("result.png", dimg)
        
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10,10))
        dimgv = cv2.cvtColor(dimg, cv2.COLOR_BGR2RGB)
        plt.imshow(dimgv)
        plt.show()

# Menjalankan program utama untuk deteksi objek
if __name__ == "__main__":
    fileName = "person.jpeg"  # Ganti dengan gambar yang sesuai
    im = cv2.imread(fileName)
    if im is None:
        print("cv2.imread failed")
        exit(1)

    model_path = "obstacle_ncnn_model"  # Tentukan path model
    m = NCNNRunner(model_path)
    m.run(im)
    print("finish")
