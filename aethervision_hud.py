import cv2
import mediapipe as mp
import numpy as np
import time
from collections import deque
import math
import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

NEON_CYAN = (255, 255, 0)
NEON_PINK = (255, 20, 147)
NEON_PURPLE = (255, 0, 255)
ELECTRIC_BLUE = (255, 191, 0)
LIME_GREEN = (0, 255, 127)
DARK_BG = (20, 20, 20)
HOLOGRAM_BLUE = (255, 200, 100)

class ModernCyberpunkHUD:
    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.hands = mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.fps_buffer = deque(maxlen=30)
        self.start_time = time.time()
        self.animation_time = 0
        self.particles = []
        self.scan_lines = []
        self.threat_level = 0
        self.bio_stats = {'heart_rate': 72, 'temp': 36.6, 'oxygen': 98}
        
    def create_particle(self, x, y):
        return {
            'x': x, 'y': y,
            'vx': np.random.randn() * 2,
            'vy': np.random.randn() * 2,
            'life': 30,
            'color': NEON_CYAN if np.random.random() > 0.5 else NEON_PINK
        }
    
    def update_particles(self, frame):
        new_particles = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            
            if p['life'] > 0 and 0 < p['x'] < frame.shape[1] and 0 < p['y'] < frame.shape[0]:
                alpha = p['life'] / 30.0
                size = int(3 * alpha)
                if size > 0:
                    cv2.circle(frame, (int(p['x']), int(p['y'])), size, p['color'], -1)
                new_particles.append(p)
        
        self.particles = new_particles
    
    def draw_holographic_line(self, frame, p1, p2, color, thickness=2):
        cv2.line(frame, p1, p2, color, thickness)
        cv2.line(frame, p1, p2, color, thickness + 2, lineType=cv2.LINE_AA)
    
    def draw_scan_line(self, frame, y_pos):
        h, w = frame.shape[:2]
        alpha = abs(math.sin(self.animation_time * 2))
        overlay = frame.copy()
        cv2.line(overlay, (0, y_pos), (w, y_pos), NEON_CYAN, 2)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    def detect_gesture(self, hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        ring_tip = hand_landmarks.landmark[16]
        pinky_tip = hand_landmarks.landmark[20]
        
        wrist = hand_landmarks.landmark[0]
        
        fingers_up = []
        finger_tips = [index_tip, middle_tip, ring_tip, pinky_tip]
        finger_bases = [hand_landmarks.landmark[i] for i in [5, 9, 13, 17]]
        
        for tip, base in zip(finger_tips, finger_bases):
            fingers_up.append(tip.y < base.y)
        
        thumb_up = thumb_tip.x < hand_landmarks.landmark[3].x
        
        if all(fingers_up):
            return "SCAN_MODE", LIME_GREEN
        elif not any(fingers_up):
            return "COMBAT_MODE", (0, 0, 255)
        elif fingers_up[0] and fingers_up[1] and not any(fingers_up[2:]):
            return "PEACE_PROTOCOL", NEON_PINK
        elif fingers_up[0] and not any(fingers_up[1:]):
            return "TARGET_LOCK", ELECTRIC_BLUE
        else:
            return "STANDBY", NEON_PURPLE
    
    def draw_futuristic_face_frame(self, frame, face_landmarks, h, w):
        x_coords = [landmark.x for landmark in face_landmarks.landmark]
        y_coords = [landmark.y for landmark in face_landmarks.landmark]
        
        x_min = int(min(x_coords) * w) - 50
        y_min = int(min(y_coords) * h) - 70
        x_max = int(max(x_coords) * w) + 50
        y_max = int(max(y_coords) * h) + 50
        
        bracket_len = 40
        offset = int(abs(math.sin(self.animation_time * 3)) * 5)
        
        self.draw_holographic_line(frame, (x_min - offset, y_min), (x_min + bracket_len, y_min), NEON_CYAN, 3)
        self.draw_holographic_line(frame, (x_min, y_min - offset), (x_min, y_min + bracket_len), NEON_CYAN, 3)
        
        self.draw_holographic_line(frame, (x_max + offset, y_min), (x_max - bracket_len, y_min), NEON_CYAN, 3)
        self.draw_holographic_line(frame, (x_max, y_min - offset), (x_max, y_min + bracket_len), NEON_CYAN, 3)
        
        self.draw_holographic_line(frame, (x_min - offset, y_max), (x_min + bracket_len, y_max), NEON_CYAN, 3)
        self.draw_holographic_line(frame, (x_min, y_max + offset), (x_min, y_max - bracket_len), NEON_CYAN, 3)
        
        self.draw_holographic_line(frame, (x_max + offset, y_max), (x_max - bracket_len, y_max), NEON_CYAN, 3)
        self.draw_holographic_line(frame, (x_max, y_max + offset), (x_max, y_max - bracket_len), NEON_CYAN, 3)
        
        pulse = abs(math.sin(self.animation_time * 2))
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), 
                     tuple(int(c * pulse) for c in NEON_CYAN), 1)
        
        glitch = np.random.randint(-2, 3) if np.random.random() > 0.9 else 0
        cv2.putText(frame, ">>> BIOMETRIC ID: CONFIRMED", 
                   (x_min + glitch, y_min - 15), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, NEON_PINK, 2)
        
        for i, landmark in enumerate(face_landmarks.landmark):
            if i % 8 == 0:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                color_mix = int((i / len(face_landmarks.landmark)) * 255)
                cv2.circle(frame, (x, y), 2, (255, color_mix, 255 - color_mix), -1)
        
        left_eye = [33, 133, 160, 159, 158, 157, 173]
        right_eye = [362, 263, 387, 386, 385, 384, 398]
        
        for eye_idx, eye_color in [(left_eye, ELECTRIC_BLUE), (right_eye, ELECTRIC_BLUE)]:
            eye_points = [(int(face_landmarks.landmark[i].x * w),
                          int(face_landmarks.landmark[i].y * h)) for i in eye_idx]
            eye_center = np.mean(eye_points, axis=0).astype(int)
            
            size = int(20 + math.sin(self.animation_time * 4) * 5)
            cv2.circle(frame, tuple(eye_center), size, eye_color, 2)
            cv2.circle(frame, tuple(eye_center), 3, NEON_PINK, -1)
            
            cv2.line(frame, (eye_center[0] - 15, eye_center[1]), 
                    (eye_center[0] + 15, eye_center[1]), eye_color, 2)
            cv2.line(frame, (eye_center[0], eye_center[1] - 15), 
                    (eye_center[0], eye_center[1] + 15), eye_color, 2)
            
            if np.random.random() > 0.8:
                self.particles.append(self.create_particle(eye_center[0], eye_center[1]))
    
    def draw_advanced_hand_overlay(self, frame, hand_landmarks, gesture, gesture_color, h, w):
        connections = mp_hands.HAND_CONNECTIONS
        for connection in connections:
            start = hand_landmarks.landmark[connection[0]]
            end = hand_landmarks.landmark[connection[1]]
            
            start_pos = (int(start.x * w), int(start.y * h))
            end_pos = (int(end.x * w), int(end.y * h))
            
            self.draw_holographic_line(frame, start_pos, end_pos, gesture_color, 3)
        
        pulse = abs(math.sin(self.animation_time * 3))
        for i, landmark in enumerate(hand_landmarks.landmark):
            x, y = int(landmark.x * w), int(landmark.y * h)
            
            if i in [4, 8, 12, 16, 20]:
                size = int(8 + pulse * 3)
                cv2.circle(frame, (x, y), size, gesture_color, -1)
                cv2.circle(frame, (x, y), size + 3, gesture_color, 2)
                
                if np.random.random() > 0.85:
                    self.particles.append(self.create_particle(x, y))
            else:
                cv2.circle(frame, (x, y), 5, gesture_color, -1)
        
        palm = hand_landmarks.landmark[9]
        cx, cy = int(palm.x * w), int(palm.y * h)
        
        hex_points = []
        for i in range(6):
            angle = math.pi / 3 * i + self.animation_time
            px = cx + int(25 * math.cos(angle))
            py = cy + int(25 * math.sin(angle))
            hex_points.append((px, py))
        
        hex_points = np.array(hex_points, np.int32)
        cv2.polylines(frame, [hex_points], True, gesture_color, 2)
        cv2.circle(frame, (cx, cy), 10, NEON_PINK, -1)
    
    def draw_modern_hud(self, frame, fps, gesture, gesture_color):
        h, w = frame.shape[:2]
        
        self.bio_stats['heart_rate'] = 72 + np.random.randint(-5, 6)
        self.bio_stats['temp'] = 36.6 + np.random.uniform(-0.2, 0.2)
        self.bio_stats['oxygen'] = 98 + np.random.randint(-1, 2)
        
        panel_w, panel_h = 320, 180
        overlay = frame.copy()
        cv2.rectangle(overlay, (15, 15), (15 + panel_w, 15 + panel_h), DARK_BG, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        self.draw_holographic_line(frame, (15, 15), (15 + panel_w, 15), NEON_CYAN, 2)
        self.draw_holographic_line(frame, (15, 15), (15, 15 + panel_h), NEON_CYAN, 2)
        self.draw_holographic_line(frame, (15 + panel_w, 15), (15 + panel_w, 15 + panel_h), NEON_CYAN, 2)
        self.draw_holographic_line(frame, (15, 15 + panel_h), (15 + panel_w, 15 + panel_h), NEON_CYAN, 2)
        
        y_offset = 45
        cv2.putText(frame, "// NEURAL INTERFACE //", (25, y_offset), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.6, NEON_PINK, 2)
        
        y_offset += 30
        cv2.putText(frame, f"FPS: {fps:.1f}", (25, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, LIME_GREEN, 1)
        cv2.rectangle(frame, (100, y_offset - 12), (100 + int(fps * 2), y_offset - 2), LIME_GREEN, -1)
        
        y_offset += 25
        cv2.putText(frame, f"HR: {self.bio_stats['heart_rate']} BPM", (25, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, ELECTRIC_BLUE, 1)
        
        y_offset += 25
        cv2.putText(frame, f"TEMP: {self.bio_stats['temp']:.1f}C", (25, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, ELECTRIC_BLUE, 1)
        
        y_offset += 25
        cv2.putText(frame, f"O2: {self.bio_stats['oxygen']}%", (25, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, ELECTRIC_BLUE, 1)
        
        y_offset += 25
        status_text = "OPTIMAL" if fps > 20 else "DEGRADED"
        status_color = LIME_GREEN if fps > 20 else (0, 165, 255)
        cv2.putText(frame, f"STATUS: {status_text}", (25, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        
        gesture_panel_w = 350
        cv2.rectangle(frame, (w - gesture_panel_w - 15, 15), 
                     (w - 15, 80), DARK_BG, -1)
        cv2.rectangle(frame, (w - gesture_panel_w - 15, 15), 
                     (w - 15, 80), gesture_color, 2)
        cv2.putText(frame, f"MODE: {gesture}", (w - gesture_panel_w, 45), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.7, gesture_color, 2)
        
        bar_w, bar_h = 600, 35
        bar_x, bar_y = (w - bar_w) // 2, h - 70
        
        elapsed = time.time() - self.start_time
        progress = min(100, (elapsed / 15) * 100)
        
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), DARK_BG, -1)
        
        fill_w = int((progress / 100) * bar_w)
        for i in range(fill_w):
            ratio = i / bar_w
            r = int(255 * (1 - ratio) + 147 * ratio)
            g = int(20 * (1 - ratio) + 0 * ratio)
            b = int(147 * (1 - ratio) + 255 * ratio)
            cv2.line(frame, (bar_x + i, bar_y), (bar_x + i, bar_y + bar_h), (b, g, r), 1)
        
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), NEON_CYAN, 2)
        
        cv2.putText(frame, f"AUGMENTATION PROGRESS: {progress:.1f}%", 
                   (bar_x, bar_y - 10), cv2.FONT_HERSHEY_DUPLEX, 
                   0.6, NEON_PINK, 2)
        
        scan_y = int(h * (0.3 + 0.4 * abs(math.sin(self.animation_time))))
        self.draw_scan_line(frame, scan_y)
        
        self.draw_neural_visualization(frame, 50, h // 2)
        
        timestamp = time.strftime("%H:%M:%S")
        cv2.putText(frame, f"[{timestamp}]", (w - 150, h - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, NEON_CYAN, 1)
    
    def draw_neural_visualization(self, frame, x, y):
        layers = [5, 7, 5]
        layer_spacing = 100
        node_spacing = 35
        
        for layer_idx, nodes in enumerate(layers):
            layer_x = x + layer_idx * layer_spacing
            
            for node_idx in range(nodes):
                node_y = y + (node_idx - nodes // 2) * node_spacing
                
                pulse = abs(math.sin(self.animation_time * 2 + node_idx * 0.5))
                size = int(6 + pulse * 3)
                cv2.circle(frame, (layer_x, node_y), size, NEON_CYAN, -1)
                cv2.circle(frame, (layer_x, node_y), size + 2, NEON_CYAN, 1)
                
                if layer_idx < len(layers) - 1:
                    next_layer_x = x + (layer_idx + 1) * layer_spacing
                    next_nodes = layers[layer_idx + 1]
                    
                    for next_node_idx in range(next_nodes):
                        next_node_y = y + (next_node_idx - next_nodes // 2) * node_spacing
                        
                        alpha = abs(math.sin(self.animation_time + node_idx + next_node_idx))
                        color = tuple(int(c * alpha) for c in NEON_PINK)
                        cv2.line(frame, (layer_x, node_y), 
                                (next_layer_x, next_node_y), color, 1, cv2.LINE_AA)
    
    def process_frame(self, frame):
        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        self.animation_time = time.time() - self.start_time
        
        face_results = self.face_mesh.process(rgb_frame)
        hand_results = self.hands.process(rgb_frame)
        
        gesture = "STANDBY"
        gesture_color = NEON_PURPLE
        
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                self.draw_futuristic_face_frame(frame, face_landmarks, h, w)
        
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                gesture, gesture_color = self.detect_gesture(hand_landmarks)
                self.draw_advanced_hand_overlay(frame, hand_landmarks, gesture, gesture_color, h, w)
        
        self.update_particles(frame)
        
        current_time = time.time()
        if len(self.fps_buffer) > 0:
            fps = 1.0 / (current_time - self.fps_buffer[-1]) if len(self.fps_buffer) > 0 else 0
        else:
            fps = 0
        self.fps_buffer.append(current_time)
        avg_fps = len(self.fps_buffer) / (self.fps_buffer[-1] - self.fps_buffer[0]) if len(self.fps_buffer) > 1 else fps
        
        self.draw_modern_hud(frame, avg_fps, gesture, gesture_color)
        
        return frame
    
    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 60)
        
        print("=" * 60)
        print("MODERN CYBERPUNK AR HUD - NEURAL INTERFACE ACTIVE")
        print("=" * 60)
        print("\nGesture Protocols:")
        print("  [HAND]  SCAN_MODE     -> All fingers extended")
        print("  [FIST]  COMBAT_MODE   -> Closed fist")
        print("  [PEACE] PEACE_PROTOCOL -> Index + Middle fingers")
        print("  [POINT] TARGET_LOCK   -> Index finger only")
        print("\nPress 'Q' to disconnect neural link\n")
        print("=" * 60)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Failed to capture frame")
                break
            
            frame = cv2.flip(frame, 1)
            frame = self.process_frame(frame)
            
            cv2.imshow('NEURAL INTERFACE :: CYBERPUNK HUD v2.0', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("\n[DISCONNECTING NEURAL LINK...]")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        self.face_mesh.close()
        self.hands.close()
        print("[NEURAL LINK TERMINATED]\n")

if __name__ == "__main__":
    hud = ModernCyberpunkHUD()
    hud.run()