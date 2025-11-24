import time
import threading

import os
import cv2
import time
import torch
import torch.nn as nn
from torchvision import models
from torchvision.transforms import transforms
import mediapipe as mp
import requests
import os

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
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.3)

    def faceDetection(self, image):
        # Convert BGR to RGB
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
            # Ensure bbox fits inside image
            x_end = min(x + bw, w)
            y_end = min(y + bh, h)
            return image[y:y_end, x:x_end]

        return None
                
    def Video2Images(self):
        video = cv2.VideoCapture(self.videoPath)
        original_fps = video.get(cv2.CAP_PROP_FPS)
        print(original_fps)
        self.fps = original_fps
        frame_interval = int(original_fps / self.fps) if original_fps > self.fps else 1
        
        frame_count = 0
        self.AllImages = []
        
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
            transforms.ToPILImage(),          # Convert numpy array to PIL Image
            transforms.Resize((224, 224)),    # Resize image
            transforms.ToTensor(),            # Convert PIL Image to tensor
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]), # Normalize
        ])
        return transform(image)

    def makePredictEmotions(self):
        device = torch.device("cpu")
        print(len(self.AllFaces))
        images_tensor = [self.preprocess_image(image) for image in self.AllFaces if image is not None]
        if len(images_tensor) == 0:
            return 
        images_tensor = torch.stack(images_tensor)
        images_tensor = images_tensor.to(device)
        self.model = self.model.to(device)
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(images_tensor.to(device))
        predicted_classes = torch.argmax(outputs, dim=1)

        listNoneFaceIndex = [i for i in range(len(self.AllFaces)) if self.AllFaces[i] is None]
        for index in sorted(listNoneFaceIndex, reverse=True):
            predicted_classes = predicted_classes.tolist()  
            predicted_classes.insert(index, -1)            
            predicted_classes = torch.tensor(predicted_classes) 
        self.emotions = predicted_classes
         
    def run(self):
        
        start = time.time()
        self.Video2Images()
        end = time.time()
        print(f"Video2Images() took {end - start:.3f} seconds")
        
        start = time.time()
        self.makePredictEmotions()
        end = time.time()
        print(f"makePredictEmotions() took {end - start:.3f} seconds")

        print(f"number Image:{len(self.AllImages)}")
        print(f"number face:{len(self.AllFaces)}")
        print(f"number emotion:{len(self.emotions)}")
        # You can add other processing steps here


model = models.mobilenet_v2(pretrained=True)
model.classifier[1] = nn.Linear(model.last_channel, 7)
state = torch.load(os.path.join(current_path,"ResnetDuck_Cbam_cuaTuan"), map_location=torch.device('cpu'))     
model.load_state_dict(state["net"])


def satisficationEvaluation(save_path):
    def task():
        print(f"start handle this: {save_path}")
        # rs = 0
        # for i in range(100):
        #     print(i)
        #     rs += 1
        #     time.sleep(1)
        # print("Done processing:", save_path)
        # Usage
        test = VideoEmotionHandle(save_path, model)
        test.run()
        class_name_count = {-1: 0, 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        
        for i in class_name_count.keys():
            class_name_count[i] = torch.sum(test.emotions == i).item() / len(test.emotions)

        satistifiedResult = {}
        for i in class_name_count.keys():
            satistifiedResult[class_names[i]] = class_name_count[i] 
            
        #print(class_name_count)
        
        positive = ( satistifiedResult['Surprise']*2 + satistifiedResult['Happy']*3 + satistifiedResult['Neutral'] )
        negative = ( satistifiedResult['Sad']*2 + satistifiedResult['Anger']*3 + satistifiedResult['Fear'])
        statisfication = round(100*positive/(positive+negative),1)
        
        url = f"{backend_url}/deliveryRecord/updateSatistifiedResult"
        data = {"statisfication": statisfication}
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()  # raise exception for HTTP errors
            print("Video URL sent successfully:")
            
            satisficationEvaluation(save_path)
        except requests.RequestException as e:
            print("Failed to send video URL:", e)
    # Run task in background thread
    thread = threading.Thread(target=task, daemon=True)
    thread.start()

    # Immediately return without waiting
    return True

if __name__ == "__main__":
    # Example video path
    video_path = "test_video.mp4"  # <-- replace with your actual video path

    # Call satisficationEvaluation (runs in background thread)
    satisficationEvaluation(video_path)