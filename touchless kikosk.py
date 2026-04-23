import cv2
import numpy as np
import mediapipe as mp
import time
import os
import urllib.request
import qrcode   # ✅ ADDED

from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# -----------------------------
# Download Model
# -----------------------------
MODEL_PATH = "hand_landmarker.task"

if not os.path.exists(MODEL_PATH):
    print("Downloading model...")
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    urllib.request.urlretrieve(url, MODEL_PATH)
    print("Download complete!")

# -----------------------------
# Load Images
# -----------------------------
def load_img(path):
    img = cv2.imread(path)
    if img is None:
        print("Error loading:", path)
        exit()
    return cv2.resize(img, (1280, 720))

bg_image = load_img(r"C:\Users\adith\OneDrive\Desktop\touchless kikiosk\thiruvananthapuram-bg.jpg")
menu_bg = load_img(r"C:\Users\adith\OneDrive\Desktop\touchless kikiosk\Travel-Bucket-List-Wallpaper-Mural-for-Wall-M.jpg")
 
place_bgs = {
    "Sree Padmanabhaswamy Temple": load_img(r"C:\Users\adith\OneDrive\Desktop\touchless kikiosk\sree padmanabha swamy temple.jpg"),
    "Kovalam Beach": load_img(r"C:\Users\adith\OneDrive\Desktop\touchless kikiosk\kovalam-beach.webp"),
    "Napier Museum": load_img(r"C:\Users\adith\OneDrive\Desktop\touchless kikiosk\napier-museum.jpg"),
    "Kanakakunnu Palace": load_img(r"C:\Users\adith\OneDrive\Desktop\touchless kikiosk\kanakakunnu palace.jpg"),
    "Poovar Island": load_img(r"C:\Users\adith\OneDrive\Desktop\touchless kikiosk\poovar island.jpg"),
    "Veli Tourist Village": load_img(r"C:\Users\adith\OneDrive\Desktop\touchless kikiosk\veli tourist.jpg")
}

# -----------------------------
# Detailed Info (✅ ADDED map)
# -----------------------------
attractions = {
    "Sree Padmanabhaswamy Temple": {
        "desc": "One of the richest temples in the world dedicated to Lord Vishnu.",
        "location": "Thiruvananthapuram, Kerala",
        "timing": "3:30 AM – 12:00 PM, 5:00 PM – 8:00 PM",
        "entry": "Free (Dress code required)",
        "map": "https://maps.google.com/?q=8.4828,76.9436"
    },
    "Kovalam Beach": {
        "desc": "Famous beach with lighthouse and golden sand.",
        "location": "Kovalam, Kerala",
        "timing": "Open 24 hours",
        "entry": "Free",
        "map": "https://maps.google.com/?q=8.4000,76.9780"
    },
    "Napier Museum": {
        "desc": "Historic museum with art and culture.",
        "location": "Thiruvananthapuram, Kerala",
        "timing": "10:00 AM – 5:00 PM (Closed Monday)",
        "entry": "₹20",
        "map": "https://maps.google.com/?q=8.5153,76.9533"
    },
    "Kanakakunnu Palace": {
        "desc": "Cultural palace hosting events and festivals.",
        "location": "Near Napier Museum",
        "timing": "10:00 AM – 6:00 PM",
        "entry": "Free",
        "map": "https://maps.google.com/?q=8.5165,76.9550"
    },
    "Poovar Island": {
        "desc": "Scenic island with backwaters and boating.",
        "location": "Poovar, Kerala",
        "timing": "9:00 AM – 6:00 PM",
        "entry": "Boat ride charges apply",
        "map": "https://maps.google.com/?q=8.3129,77.0730"
    },
    "Veli Tourist Village": {
        "desc": "Tourist park with boating and gardens.",
        "location": "Veli, Kerala",
        "timing": "8:00 AM – 6:00 PM",
        "entry": "Free (Boating extra)",
        "map": "https://maps.google.com/?q=8.5316,76.8855"
    }
}

# -----------------------------
# QR FUNCTION (✅ ADDED)
# -----------------------------
def generate_qr(link):
    qr = qrcode.make(link)
    qr = np.array(qr.convert('RGB'))
    qr = cv2.resize(qr, (200, 200))
    return qr

def overlay_png(bg, overlay, x, y):
    h, w, _ = overlay.shape

    for i in range(h):
        for j in range(w):
            if overlay[i][j][3] != 0:  # alpha channel
                if y+i < bg.shape[0] and x+j < bg.shape[1]:
                    bg[y+i, x+j] = overlay[i][j][:3]
# -----------------------------
# MediaPipe Setup
# -----------------------------
base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    running_mode=vision.RunningMode.VIDEO
)

landmarker = vision.HandLandmarker.create_from_options(options)

# -----------------------------
# Finger Count
# -----------------------------
def count_fingers(lm):
    fingers = 0

    if lm[4][0] > lm[3][0]:
        fingers += 1

    if lm[8][1] < lm[6][1]: fingers += 1
    if lm[12][1] < lm[10][1]: fingers += 1
    if lm[16][1] < lm[14][1]: fingers += 1
    if lm[20][1] < lm[18][1]: fingers += 1

    return fingers

# -----------------------------
# Draw Menu
# -----------------------------
def draw_menu(frame, pointer):
    y = 150
    for name in attractions.keys():
        color = (0,0,0)
        if pointer and 200 < pointer[0] < 800 and y-40 < pointer[1] < y+20:
            color = (0,255,0)

        cv2.putText(frame, name, (200, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        y += 80

def draw_multiline_text(frame, text, x, y, line_width=40):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        if len(line + word) < line_width:
            line += word + " "
        else:
            lines.append(line)
            line = word + " "

    lines.append(line)

    for i, l in enumerate(lines):
        cv2.putText(frame, l.strip(), (x, y + i*30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

# -----------------------------
# Camera
# -----------------------------
cap = cv2.VideoCapture(0)
cap.set(3,1280)
cap.set(4,720)

if not cap.isOpened():
    print("❌ Camera not detected")
    exit()
    # -----------------------------
# Variables
# -----------------------------
app_state = "home"
selected_place = None

smooth_x, smooth_y = 0, 0
alpha = 0.2
trail_points = []

last_gesture_time = 0
gesture_delay = 1

prev_fingers = 0
stable_count = 0
stable_threshold = 5


# -----------------------------
# MAIN LOOP
# -----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame,1)
    display_frame = bg_image.copy()

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect_for_video(mp_image, int(time.time()*1000))

    lmList = []
    if result.hand_landmarks:
        for hand in result.hand_landmarks:
            for lm in hand:
                lmList.append((int(lm.x*1280), int(lm.y*720)))

    if len(lmList) != 21:
        lmList = []

    fingers = 0
    pointer = None

    if lmList:
        current_fingers = count_fingers(lmList)

        if abs(current_fingers - prev_fingers) <= 2:
            if current_fingers == prev_fingers:
                stable_count += 1
            else:
                stable_count = 0

        prev_fingers = current_fingers

        if stable_count > stable_threshold:
            fingers = current_fingers

        cx, cy = lmList[8]
        smooth_x = int(alpha*cx + (1-alpha)*smooth_x)
        smooth_y = int(alpha*cy + (1-alpha)*smooth_y)
        pointer = (smooth_x, smooth_y)

        trail_points.append(pointer)

        if len(trail_points) > 15:
            trail_points.pop(0)

    current_time = time.time()

    # GESTURES
    if fingers == 3 and current_time - last_gesture_time > 1:
        app_state = "menu"
        last_gesture_time = current_time

    elif fingers >= 4 and current_time - last_gesture_time > 1:
        app_state = "home"
        selected_place = None
        last_gesture_time = current_time

    # UI
    if app_state == "home":
        cv2.putText(display_frame, "Welcome to",
                    (150,200), cv2.FONT_HERSHEY_SIMPLEX,1.5,(0,0,0),3)

    elif app_state == "menu":
        display_frame = menu_bg.copy()
        draw_menu(display_frame, pointer)

        if pointer and fingers == 2 and current_time - last_gesture_time > gesture_delay:
            y = 150
            for name in attractions.keys():
                if 200 < pointer[0] < 800 and y-40 < pointer[1] < y+20:
                    selected_place = name
                    app_state = "info"
                    last_gesture_time = current_time
                y += 80

    elif app_state == "info":

        if selected_place is None or selected_place not in attractions:
            app_state = "menu"
            continue

        if selected_place in place_bgs:
            display_frame = place_bgs[selected_place].copy()

        info = attractions[selected_place]

        cv2.putText(display_frame, selected_place,
                    (50,100), cv2.FONT_HERSHEY_SIMPLEX,1.2,(255,255,255),3)

        draw_multiline_text(display_frame, "Description: " + info["desc"], 50, 170)

        cv2.putText(display_frame, "Location: " + info["location"],
                    (50,300), cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)

        cv2.putText(display_frame, "Timing: " + info["timing"],
                    (50,350), cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)

        cv2.putText(display_frame, "Entry: " + info["entry"],
                    (50,400), cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,0,0),2)

        # QR
        qr_img = generate_qr(info["map"])
        display_frame[450:650, 1000:1200] = qr_img

        cv2.putText(display_frame, "Scan for Location",
                    (950, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        cv2.putText(display_frame, "Show 4/5 fingers to go back",
                    (50,650), cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,255,0),2)

        # ⭐ FIXED STAR EFFECT
        if pointer:
            x, y = pointer

            for angle in range(0, 360, 45):
                x2 = int(x + 20 * np.cos(np.radians(angle)))
                y2 = int(y + 20 * np.sin(np.radians(angle)))
                cv2.line(display_frame, (x, y), (x2, y2), (255,255,0), 2)

            cv2.circle(display_frame, (x, y), 5, (0,0,255), -1)

    cv2.putText(display_frame, f"Fingers: {fingers}",
                (20,50), cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,255),2)

    cv2.imshow("Touchless Tourism Kiosk", display_frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
landmarker.close()
