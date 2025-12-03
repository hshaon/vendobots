import time
import os
import cv2
import torch
import torch.nn as nn
from torchvision import models
from torchvision.transforms import transforms
import mediapipe as mp
import requests
from dotenv import load_dotenv


load_dotenv()
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

current_path = os.getcwd()
print(current_path)

class_names = {-1: "Uknown", 0:"Surprise", 1:"Fear", 2:"Disgust", 3:"Happy", 4:"Sad", 5:"Anger", 6:"Neutral"}
backend_url = os.getenv("BE_URL")

class VideoEmotionHandle:
    def __init__(self, videoPath, model):
        self.fps = 0
        self.videoPath = videoPath
        self.AllImages = [] 
        self.AllFaces = []
        self.emotions = []
        self.model = model
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.3
        )

    def faceDetection(self, image):
        results = self.face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.detections:
            return None

        h, w, _ = image.shape
        largest_box = None
        largest_area = 0
        
        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            x1 = int(bbox.xmin * w)
            y1 = int(bbox.ymin * h)
            box_w = int(bbox.width * w)
            box_h = int(bbox.height * h)
            area = box_w * box_h
            
            if area > largest_area:
                largest_area = area
                largest_box = (x1, y1, box_w, box_h)

        if largest_box:
            x, y, bw, bh = largest_box
            x = max(0, x)
            y = max(0, y)
            x_end = min(x + bw, w)
            y_end = min(y + bh, h)
            return image[y:y_end, x:x_end]

        return None
                

    def Video2Images(self):
        video = cv2.VideoCapture(self.videoPath)
        print(f"Processing video: {self.videoPath}")

        original_fps = video.get(cv2.CAP_PROP_FPS)
        print("Original FPS:", original_fps)

        self.fps = original_fps
        frame_interval = int(original_fps / self.fps) if original_fps > self.fps else 1
        
        frame_count = 0
        
        while True:
            success, frame = video.read()
            if not success:
                break
        
            if frame_count % frame_interval == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.AllImages.append(rgb_frame)
        
            frame_count += 1
        
        video.release()
        self.AllFaces = [self.faceDetection(image) for image in self.AllImages]


    def preprocess_image(self, image):
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406],
                                 [0.229, 0.224, 0.225]),
        ])
        return transform(image)

    def makePredictEmotions(self):
        device = torch.device("cpu")
        print("Faces detected:", len(self.AllFaces))

        images_tensor = [self.preprocess_image(i) for i in self.AllFaces if i is not None]
        if len(images_tensor) == 0:
            return 
        
        images_tensor = torch.stack(images_tensor).to(device)
        self.model = self.model.to(device)
        self.model.eval()

        with torch.no_grad():
            outputs = self.model(images_tensor)

        predicted_classes = torch.argmax(outputs, dim=1)

        none_indexes = [i for i in range(len(self.AllFaces)) if self.AllFaces[i] is None]
        predicted_classes = predicted_classes.tolist()
        for idx in none_indexes:
            predicted_classes.insert(idx, -1)

        self.emotions = torch.tensor(predicted_classes)

         
    def run(self):
        print("Starting emotion evaluation...")

        start = time.time()
        self.Video2Images()
        print("Video2Images time:", time.time() - start)

        start = time.time()
        self.makePredictEmotions()
        print("makePredictEmotions time:", time.time() - start)

        print("Images:", len(self.AllImages))
        print("Faces:", len(self.AllFaces))
        print("Emotions:", len(self.emotions))



# -----------------------------
# Model loading
# -----------------------------

model = models.mobilenet_v2(weights=None)
model.classifier[1] = nn.Linear(model.last_channel, 7)

state = torch.load(os.path.join(current_path, "ResnetDuck_Cbam_cuaTuan"), map_location="cpu")
model.load_state_dict(state["net"], strict=True)



# -----------------------------
# NO THREAD VERSION
# -----------------------------
def satisficationEvaluation(save_path):
    print(f"Start processing: {save_path}")

    handler = VideoEmotionHandle(save_path, model)
    handler.run()

    class_name_count = {i: 0 for i in class_names}

    for i in class_name_count.keys():
        class_name_count[i] = torch.sum(handler.emotions == i).item() / len(handler.emotions)

    satistifiedResult = {}
    for i in class_name_count.keys():
        satistifiedResult[class_names[i]] = round(class_name_count[i], 3)

    positive = (
        satistifiedResult['Surprise'] * 2 +
        satistifiedResult['Happy'] * 3 +
        satistifiedResult['Neutral']
    )
    negative = (
        satistifiedResult['Sad'] * 2 +
        satistifiedResult['Anger'] * 3 +
        satistifiedResult['Fear'] + satistifiedResult['Uknown']
    )
    statisfication = round(100 * positive / (positive + negative + 1e-10), 1)
    print("Satisfaction:", f'{statisfication}%')
    satistifiedResult['Satisfaction'] = f'{statisfication}%'

    # Send result to API
    url = f"{backend_url}/deliveryRecord/updateSatistifiedResult"
    data = {"statisfication": str(satistifiedResult), 
            "video_url": save_path }

    print(url)
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Satisfaction result sent successfully!")
    except requests.RequestException as e:
        print("Failed to send:", e)

    return statisfication



if __name__ == "__main__":
    video_path = r"C:\Tuan_use\vendobots\control_interface\transaction_records\transaction1_2025_11_24_13_43_46.mp4"
    satisficationEvaluation(video_path)
