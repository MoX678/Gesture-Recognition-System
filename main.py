import cv2 as cv
import keyboard
import mediapipe as mp
import numpy as np
import threading
import math
import time
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
import pyautogui
from collections import deque
import gui

# Constants
PINCH_COOLDOWN = 1.0
PINCH_THRESHOLD = 30
SWIPE_THRESHOLD = 50
COOLDOWN = 1.0
smooth_factor = 3
SCROLL_INTERVAL = 0.05
ACTIVATION_DURATION = 5 

# Global variables with thread-safe locks
frame_lock = threading.Lock()
current_frame = None
results_lock = threading.Lock()
latest_results = None
running = True
detection_active = True
last_activation_time = 0

# MediaPipe setup
mp_hands = mp.solutions.hands
mp.solutions.hands.Hands().close()
mp_drawing = mp.solutions.drawing_utils
# Audio setup

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, 0, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()
minVol, maxVol = volRange[0], volRange[1]


class VideoCaptureThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.cap = cv.VideoCapture(0)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv.CAP_PROP_FPS, 30)

    def run(self):
        global current_frame, running
        while running:
            ret, frame = self.cap.read()
            if ret:
                with frame_lock:
                    current_frame = cv.flip(frame, 1)
        self.cap.release()

class HandProcessingThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=1
        )

    def run(self):
        global latest_results, running
        while running:
            with frame_lock:
                frame = current_frame.copy() if current_frame is not None else None
            
            if frame is not None:
                rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                with results_lock:
                    latest_results = results

class CvFpsCalc:
    def __init__(self, buffer_len=1):
        self._start_tick = cv.getTickCount()
        self._freq = 1000.0 / cv.getTickFrequency()
        self._difftimes = deque(maxlen=buffer_len)

    def get(self):
        current_tick = cv.getTickCount()
        different_time = (current_tick - self._start_tick) * self._freq
        self._start_tick = current_tick

        self._difftimes.append(different_time)
        fps = 1000.0 / (sum(self._difftimes) / len(self._difftimes))
        return round(fps, 2)

def detect_swipe(prev_x, curr_x, threshold):
    displacement = curr_x - prev_x
    if abs(displacement) > threshold:
        return "right" if displacement > 0 else "left"
    return None

def detect_fingers(hand_landmarks):
    fingers = []
    fingers.append(1 if hand_landmarks.landmark[4].x < hand_landmarks.landmark[2].x else 0)
    for tip, base in zip([8, 12, 16, 20], [6, 10, 14, 18]):
        fingers.append(1 if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[base].y else 0)
    return fingers

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def draw_info(image, fps, mode):
    status_color = (0, 255, 0) if detection_active else (0, 0, 255)
    status_text = f"Active ({mode})" if detection_active else "INACTIVE"
    
    cv.putText(image, f"FPS: {fps}", (10, 30), 
              cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv.putText(image, status_text, (10, 70), 
              cv.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
    return image

def detect_pinch(index_tip, thumb_tip, threshold=PINCH_THRESHOLD):
    distance = calculate_distance(index_tip, thumb_tip)
    return distance < threshold


def handle_activation():
    global detection_active, last_activation_time
    detection_active = not detection_active
    if detection_active:
        last_activation_time = time.time()
        

# Set up global hotkey
keyboard.add_hotkey('ctrl+space', handle_activation)
keyboard_thread = threading.Thread(target=keyboard.wait)
keyboard_thread.daemon = True
keyboard_thread.start()

def main():
    global running, detection_active, last_activation_time
    screen_width, screen_height = pyautogui.size()
    cv_fps = CvFpsCalc(buffer_len=10)
    
    # Start threads
    video_thread = VideoCaptureThread()
    processing_thread = HandProcessingThread()
    video_thread.start()
    processing_thread.start()

    # Local variables
    mode = 'N'
    active = 0
    prev_index_x = None
    last_swipe_time = 0
    last_pinch_time = 0
    last_scroll_time = 0
    volBar = 400
    volPer = 0

    while running:
        
        fps = cv_fps.get()
        frame = None
        results = None
        
        if detection_active:
            detection_active = True
            
        
        with frame_lock:
            if current_frame is not None:
                frame = current_frame.copy()
        
        with results_lock:
            results = latest_results

        if frame is not None and results is not None:
            status_text = "Active" if detection_active else "Inactive"
            if detection_active:
              
            
              if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    fingers = detect_fingers(hand_landmarks)
                    
                    index_tip = hand_landmarks.landmark[8]
                    index_x, index_y = int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0])
                    thumb_tip = hand_landmarks.landmark[4]
                    thumb_x, thumb_y = int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0])
                    current_time = time.time()

                    # Pinch detection
                    if current_time - last_pinch_time > PINCH_COOLDOWN:
                        if detect_pinch((index_x, index_y), (thumb_x, thumb_y)):
                            
                            last_pinch_time = current_time
                            cv.circle(frame, (index_x, index_y), 10, (0, 0, 255), -1)
                            cv.putText(frame, "Pinch Detected", (50, 150), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                            pyautogui.hotkey('space')
                            

                    # Swipe detection
                    if prev_index_x is not None:
                        if current_time - last_swipe_time > COOLDOWN:
                            swipe_direction = detect_swipe(prev_index_x, index_x, SWIPE_THRESHOLD)
                            if swipe_direction:
                                last_swipe_time = current_time
                                if swipe_direction == "right":
                                    pyautogui.hotkey('ctrl', 'right')
                                else:
                                    pyautogui.hotkey('ctrl', 'left')
                                
                    prev_index_x = index_x

                    # Mode detection
                    if fingers == [1, 1, 1, 1, 1]:
                        mode = 'N'
                        active = 0
                        mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2)
                )
                    elif fingers == [1, 1, 0, 0, 0] and active == 0:
                        mode = 'Volume'
                        active = 1
                    elif fingers == [0, 1, 1, 0, 0] and active == 0:
                        mode = 'Scroll'
                        active = 1
                    elif fingers == [0, 1, 0, 0, 0] and active == 0:
                        mode = 'Cursor'
                        active = 1

                    # Mode handling
                    if mode == 'Cursor':
                        target_x = int(index_tip.x * screen_width)
                        target_y = int(index_tip.y * screen_height)
                        pyautogui.moveTo(target_x, target_y)

                    elif mode == 'Volume':
                        length = math.hypot(index_x - thumb_x, index_y - thumb_y)
                        vol = np.clip(np.interp(length, [20, 150], [minVol, maxVol]), minVol, maxVol)
                        volBar = np.clip(np.interp(length, [50, 200], [400, 150]), 150, 400)
                        volPer = np.clip(np.interp(length, [50, 200], [0, 100]), 0, 100)
                        volume.SetMasterVolumeLevel(vol, None)
                        cv.circle(frame, (thumb_x, thumb_y), 10, (0, 255, 0), cv.FILLED)
                        cv.circle(frame, (index_x, index_y), 10, (0, 255, 0), cv.FILLED)
                        cv.line(frame, (thumb_x, thumb_y), (index_x, index_y), (0, 255, 0), 3)
                        cv.rectangle(frame, (50, 150), (85, 400), (0, 255, 0), 3)
                        cv.rectangle(frame, (50, int(volBar)), (85, 400), (0, 255, 0), cv.FILLED)
                        cv.putText(frame, f'{int(volPer)}%', (40, 450), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    elif mode == 'Scroll' and current_time - last_scroll_time > SCROLL_INTERVAL:
                        if current_time - last_scroll_time > SCROLL_INTERVAL:
                             middle_tip = hand_landmarks.landmark[12]
                             middle_x, middle_y = int(middle_tip.x * frame.shape[1]), int(middle_tip.y * frame.shape[0])
                             
                             scroll_distance = middle_y - index_y
                             scroll_speed = int(scroll_distance / smooth_factor)
                             pyautogui.scroll(scroll_speed)
                             last_scroll_time = current_time
                             
                             
                             cv.circle(frame, (index_x, index_y), 10, (255, 0, 0), cv.FILLED)
                             cv.circle(frame, (middle_x, middle_y), 10, (255, 0, 0), cv.FILLED)
                             cv.line(frame, (index_x, index_y), (middle_x, middle_y), (255, 0, 0), 3)

                         # Limit scrolling frequency
                        
                    
                    

            current_mode = mode if detection_active else "Disabled"
            frame = draw_info(frame, fps, current_mode)
            if fps < 25:
               cv.putText(frame, "LOW FPS WARNING", (10, 110), 
               cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            cv.imshow("Hand Gesture Control", frame)

        if cv.waitKey(1) & 0xFF == 27:
            running = False
            break

    video_thread.join()
    processing_thread.join()
    cv.destroyAllWindows()

if __name__ == "__main__":
    # Start gesture control in a background thread
    gesture_thread = threading.Thread(target=main)
    gesture_thread.daemon = True  # Terminates when main thread exits
    gesture_thread.start()
    
    # Launch GUI in the main thread
    gui.run_ui()