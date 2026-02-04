import cv2
import mediapipe as mp

class HandGestureRecognition:
    def __init__(self):
        self.hands = mp.solutions.hands.Hands(max_num_hands=1)
        self.mp_draw = mp.solutions.drawing_utils

    def crop_hand_from_frame(self, image, hand_landmarks):
        image_height, image_width, _ = image.shape

        x_coords = [lm.x for lm in hand_landmarks.landmark]
        y_coords = [lm.y for lm in hand_landmarks.landmark]

        # Convert to pixel coords
        x_min = int(min(x_coords) * image_width)
        y_min = int(min(y_coords) * image_height)
        x_max = int(max(x_coords) * image_width)
        y_max = int(max(y_coords) * image_height)

        # Add margin (optional)
        margin = 20
        x_min = max(x_min - margin, 0)
        y_min = max(y_min - margin, 0)
        x_max = min(x_max + margin, image_width)
        y_max = min(y_max + margin, image_height)

        return image[y_min:y_max, x_min:x_max]

    def detect_gesture(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_frame)

        label = "No Hand Detected"
        cropped_hand = None

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

                # Crop hand for use elsewhere
                cropped_hand = self.crop_hand_from_frame(frame, hand_landmarks)

                landmarks = hand_landmarks.landmark
                fingers = []

                # Thumb
                if landmarks[4].x < landmarks[3].x:
                    fingers.append(1)
                else:
                    fingers.append(0)

                # 4 Fingers
                for tip_id in [8, 12, 16, 20]:
                    if landmarks[tip_id].y < landmarks[tip_id - 2].y:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                total_fingers = fingers.count(1)

                # Gesture mapping
                if total_fingers == 0:
                    label = "Fist"
                elif total_fingers == 5:
                    label = "Open Palm"
                elif total_fingers == 1:
                    label = "Thumb Up"
                elif total_fingers == 2:
                    label = "2 Fingers"
                elif total_fingers == 3:
                    label = "3 Fingers"
                elif total_fingers == 4:
                    label = "4 Fingers"

        return frame, label, cropped_hand

