import time
import numpy as np
import cv2
from pycaw.pycaw import AudioUtilities
from comtypes import CLSCTX_ALL

# Session state constants
STATE_ACTIVE = 1
STATE_INACTIVE = 0
STATE_EXPIRED = 2

def get_spotify_status():
    """
    Detects if Spotify is currently playing, paused, or not running.
    Returns "Playing", "Paused", or "Not Running".
    """
    try:
        # Get all active audio sessions
        sessions = AudioUtilities.GetAllSessions()

        for session in sessions:
            control = session._ctl
            process = session.Process

            if process and process.name().lower() == "spotify.exe":
                state = control.GetState()
                
                if state == STATE_ACTIVE:
                    return "Playing"
                elif state == STATE_INACTIVE:
                    return "Paused"
                elif state == STATE_EXPIRED:
                    return "Not Running"
        
        return "Not Running"  # If no session found

    except Exception as e:
        print(f"Error: {e}")
        return "Error"

def create_spotify_window(status):
    """
    Creates an OpenCV window displaying Spotify's playback status with drawn symbols.
    """
    # Window size
    width, height = 400, 200
    window = np.zeros((height, width, 3), dtype=np.uint8)

    # Define colors
    colors = {
        "Playing": (0, 255, 0),  # Green
        "Paused": (0, 255, 255),  # Yellow
        "Not Running": (0, 0, 255)  # Red
    }
    
    color = colors.get(status, (255, 255, 255))  # Default: White

    # Add title
    cv2.putText(window, "Spotify Status:", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Draw symbols based on status
    if status == "Playing":
        # Draw Play ▶ symbol (Triangle)
        pts = np.array([[150, 100], [180, 120], [150, 140]], np.int32)
        cv2.fillPoly(window, [pts], color)

    elif status == "Paused":
        # Draw Pause ⏸ symbol (Two vertical bars)
        cv2.rectangle(window, (140, 100), (150, 140), color, -1)
        cv2.rectangle(window, (160, 100), (170, 140), color, -1)

    elif status == "Not Running":
        # Show "❌ Not Running" text
        cv2.putText(window, "Not Running", (120, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    # Quit instructions
    cv2.putText(window, "Press Q to quit", (100, 180), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    return window

if __name__ == "__main__":
    while True:
        status = get_spotify_status()
        

        # Create OpenCV window
        window = create_spotify_window(status)
        cv2.imshow("Spotify Detector", window)

        # Exit if 'q' is pressed
        if cv2.waitKey(500) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
