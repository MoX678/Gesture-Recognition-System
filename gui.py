import json
import customtkinter as ctk
import keyboard
import threading
import time

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Modern style constants
MODERN_FONT = ("Segoe UI", 12)
TITLE_FONT = ("Segoe UI", 20, "bold")
BUTTON_STYLE = {
    "font": MODERN_FONT,
    "anchor": "w",
    "corner_radius": 12,
    "border_width": 0,
    "fg_color": "transparent",
    "hover_color": ("#3A3A3A", "#1F1F1F"),
    "height": 48
}
FRAME_STYLE = {
    "corner_radius": 16,
    "border_width": 0,
    "fg_color": ("#F5F5F5", "#2B2B2B")
    
}

SLIDER_STYLE = {
    "progress_color": "#646CFF",
    "button_color": "#646CFF",
    "button_hover_color": "#5359CC",
    "height": 8
}
MENU_STYLE = {
    "corner_radius": 6,
    "button_color": "#646CFF",
    "button_hover_color": "#5359CC",
    "fg_color": "#646CFF",   
}
BUTTON_STYLE = {
    "fg_color": "#646CFF",
    
    
}
json_filename = "mappings.json"

# Load or initialize configuration
try:
    with open(json_filename, "r") as file:
        data = json.load(file)
        action_options = data.get("actions", ["Open Menu", "Close Menu", "Next", "Previous"])
        selected_mappings = data.get("mappings", {})
        modes = data.get("modes", {})
        gesture_settings = data.get("gesture_settings", {

        })
        current_hotkey = data.get("hotkey", "ctrl+shift+g")
except FileNotFoundError:
    action_options = ["Open Menu", "Close Menu", "Next", "Previous"]
    selected_mappings = {}
    modes = {
        "Volume Control": True,
        "Scroll Page": True,
        "Cursor Mode": True
    }
    current_hotkey = "ctrl+shift+g"
    data = {"actions": action_options, "mappings": selected_mappings, 
            "modes": modes, "hotkey": current_hotkey}

gesture_options = ["Swipe Left", "Swipe Right", "Tap", "Double Tap"]

# Initialize missing mappings
for gesture in gesture_options:
    if gesture not in selected_mappings:
        selected_mappings[gesture] = action_options[0]

hotkey_id = None
recording = False  # New flag to track recording state

def run_ui():
    
    global root, action_menus, current_page, hotkey_label, record_button

    root = ctk.CTk()
    root.geometry("1000x600")
    root.title("Gesture Control Suite")
    root.withdraw()
    root.attributes("-topmost", True)

    # Configure grid layout
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # Modern sidebar with icons
    sidebar = ctk.CTkFrame(root, corner_radius=0, width=200)
    sidebar.grid(row=0, column=0, sticky="nsew")
    
    # Sidebar header
    ctk.CTkLabel(sidebar, text="👋 Gesture Suite", font=TITLE_FONT, 
                pady=20, anchor="center").pack(fill="x")

    # Navigation buttons
    nav_buttons = [
        ("General", "⚙️", general_page),
        ("Gestures", "👆", gestures_page),
        ("Modes", "🔄", modes_page)
    ]

    for text, emoji, command in nav_buttons:
        btn = ctk.CTkButton(sidebar, text=f" {emoji}  {text}", 
                          command=command, **BUTTON_STYLE)
        btn.pack(pady=4, padx=10, fill="x")

    # Main content frames
    global frame_general, frame_gestures, frame_modes
    frame_general = create_modern_frame(root)
    frame_gestures = create_modern_frame(root)
    frame_modes = create_modern_frame(root)

    # General Page Content
    build_general_page()
    
    # Gestures Page Content
    build_gestures_page()
    
    # Modes Page Content
    build_modes_page()

    general_page()
    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    root.mainloop()

def create_modern_frame(parent):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)
    return frame

def switch_page(new_frame):
    global current_page
    if 'current_page' in globals():
        current_page.grid_forget()
    new_frame.grid(row=0, column=1, sticky="nsew")
    current_page = new_frame

def build_general_page():
    # Title panel
    title_panel = ctk.CTkFrame(frame_general, **FRAME_STYLE)
    title_panel.grid(row=0, column=0, pady=10, padx=20, sticky="ew")
    ctk.CTkLabel(title_panel, text="General Settings", 
                font=TITLE_FONT).pack(padx=10, pady=10)

    # Content frame
    content_frame = ctk.CTkScrollableFrame(frame_general, **FRAME_STYLE)
    content_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    # Hotkey configuration
    global hotkey_label, record_button
    hotkey_row = ctk.CTkFrame(content_frame, fg_color="transparent")
    hotkey_row.pack(padx=10, pady=20, fill="x")
    
    ctk.CTkLabel(hotkey_row, text="Toggle UI Hotkey:", 
                font=MODERN_FONT).pack(side="left", padx=10)
    
    hotkey_label = ctk.CTkLabel(hotkey_row, text=current_hotkey, 
                               font=MODERN_FONT)
    hotkey_label.pack(side="left", padx=10)
    
    record_button = ctk.CTkButton(hotkey_row, text="Record New Hotkey", font=MODERN_FONT,
                                 command=start_recording,fg_color="#646CFF",hover_color="#5359CC")
    record_button.pack(side="right", padx=10)

    # Save button
    ctk.CTkButton(frame_general, text="Save Configuration", 
                 command=on_submit, height=52, font=TITLE_FONT, fg_color="#646CFF",hover_color="#5359CC"
                 ).grid(row=2, column=0, pady=20, padx=20, sticky="ew")

def build_gestures_page():
    # Title panel
    title_panel = ctk.CTkFrame(frame_gestures, **FRAME_STYLE)
    title_panel.grid(row=0, column=0, pady=20, padx=10, sticky="nsew")
    ctk.CTkLabel(title_panel, text="Gestures Configuration", 
                font=TITLE_FONT).pack(padx=10, pady=10)

    # Content frame
    content_frame = ctk.CTkFrame(frame_gestures, **FRAME_STYLE)
    content_frame.grid(row=1, column=0, padx=10, pady=20, sticky="nsew")
    frame_gestures.grid_columnconfigure(0, weight=4)
    frame_gestures.grid_rowconfigure(1, weight=5)

    # Gesture mappings
    global action_menus
    action_menus = {}
    for gesture in gesture_options:
        row = ctk.CTkFrame(content_frame, fg_color="transparent")
        row.pack(padx=10, pady=8, fill="x")
        
        ctk.CTkLabel(row, text=gesture, font=MODERN_FONT, 
                    width=180).pack(side="left", padx=10)
        
        action_menu = ctk.CTkOptionMenu(row, values=action_options, 
                                      **MENU_STYLE)
        action_menu.set(selected_mappings[gesture])
        action_menu.pack(side="right", expand=True, fill="x", padx=10)
        action_menus[gesture] = action_menu
        global swipe_sensitivity_slider, tap_duration_slider, gesture_timeout_slider, feedback_switch
        global swipe_sensitivity_label, tap_duration_label, gesture_timeout_label
        sensitivity_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    sensitivity_frame.pack(padx=10, pady=10, fill="x")
    ctk.CTkLabel(sensitivity_frame, text="Swipe Sensitivity:", font=MODERN_FONT).pack(side="left", padx=10)
    
    swipe_sensitivity_slider = ctk.CTkSlider(sensitivity_frame, from_=0.1, to=1.0, number_of_steps=9, **SLIDER_STYLE)
    swipe_sensitivity_slider.set(gesture_settings["swipe_sensitivity"])
    swipe_sensitivity_slider.pack(side="left", padx=10, expand=True, fill="x")
    
    swipe_sensitivity_label = ctk.CTkLabel(sensitivity_frame, text=f"{gesture_settings['swipe_sensitivity']:.2f}", font=MODERN_FONT)
    swipe_sensitivity_label.pack(side="right", padx=10)

    # Update label when slider changes
    swipe_sensitivity_slider.configure(command=lambda value: swipe_sensitivity_label.configure(text=f"{float(value):.2f}"))

    # Tap Duration Threshold
    tap_frame = ctk.CTkFrame(content_frame, fg_color="transparent" )
    tap_frame.pack(padx=10, pady=10, fill="x")
    ctk.CTkLabel(tap_frame, text="Tap Duration Threshold:", font=MODERN_FONT).pack(side="left", padx=10)
    
    tap_duration_slider = ctk.CTkSlider(tap_frame, from_=0.1, to=1.0, number_of_steps=9, **SLIDER_STYLE)
    tap_duration_slider.set(gesture_settings["pinch_threshold"])
    tap_duration_slider.pack(side="left", padx=10, expand=True, fill="x")
    
    tap_duration_label = ctk.CTkLabel(tap_frame, text=f"{gesture_settings['pinch_threshold']:.2f}", font=MODERN_FONT)
    tap_duration_label.pack(side="right", padx=10)

    # Update label when slider changes
    tap_duration_slider.configure(command=lambda value: tap_duration_label.configure(text=f"{float(value):.2f}"))

    # Gesture Timeout
    timeout_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    timeout_frame.pack(padx=10, pady=10, fill="x")
    ctk.CTkLabel(timeout_frame, text="Gesture Timeout (s):", font=MODERN_FONT).pack(side="left", padx=10)
    
    gesture_timeout_slider = ctk.CTkSlider(timeout_frame, from_=0.5, to=3.0, number_of_steps=5, **SLIDER_STYLE)
    gesture_timeout_slider.set(gesture_settings["gesture_timeout"])
    gesture_timeout_slider.pack(side="left", padx=10, expand=True, fill="x")
    
    gesture_timeout_label = ctk.CTkLabel(timeout_frame, text=f"{gesture_settings['gesture_timeout']:.2f}", font=MODERN_FONT)
    gesture_timeout_label.pack(side="right", padx=10)

    # Update label when slider changes
    gesture_timeout_slider.configure(command=lambda value: gesture_timeout_label.configure(text=f"{float(value):.2f}"))

    # Gesture Feedback
    feedback_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    feedback_frame.pack(padx=10, pady=10, fill="x")
    ctk.CTkLabel(feedback_frame, text="Enable Gesture Feedback:", font=MODERN_FONT).pack(side="left", padx=10)
    feedback_switch = ctk.CTkSwitch(feedback_frame, text="")
    feedback_switch.select() if gesture_settings["enable_feedback"] else feedback_switch.deselect()
    feedback_switch.pack(side="right", padx=10)

    # Save button
    ctk.CTkButton(frame_gestures, text="Save Configuration", 
                 command=save_gesture_settings, height=52, font=TITLE_FONT,fg_color="#646CFF",hover_color="#5359CC"
                 ).grid(row=2, column=0, pady=20, padx=20, sticky="ew")

def build_modes_page():
    # Title panel
    title_panel = ctk.CTkFrame(frame_modes, **FRAME_STYLE)
    title_panel.grid(row=0, column=0, pady=10, padx=20, sticky="ew")
    ctk.CTkLabel(title_panel, text="Operation Modes", 
                font=TITLE_FONT).pack(padx=10, pady=10)

    # Content frame
    content_frame = ctk.CTkScrollableFrame(frame_modes, **FRAME_STYLE)
    content_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    # Mode switches
    global mode_switches
    mode_switches = {}
    for mode, state in modes.items():
        frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(frame, text=mode, font=MODERN_FONT, 
                    width=180).pack(side="left", padx=10)
        
        switch = ctk.CTkSwitch(frame, text="", command=lambda m=mode: update_mode(m),fg_color="gray36",progress_color= "#646CFF")
        switch.pack(side="right", padx=10)
        switch.select() if state else switch.deselect()
        mode_switches[mode] = switch

    # Save button
    ctk.CTkButton(frame_modes, text="Save Configuration", 
                 command=on_submit, height=52, font=TITLE_FONT, fg_color="#646CFF",hover_color="#5359CC"
                 ).grid(row=2, column=0, pady=20, padx=20, sticky="ew")

def general_page(): switch_page(frame_general)
def gestures_page(): switch_page(frame_gestures)
def modes_page(): switch_page(frame_modes)

def update_mode(mode_name):
    modes[mode_name] = mode_switches[mode_name].get()
def save_gesture_settings():
    gesture_settings["swipe_sensitivity"] = swipe_sensitivity_slider.get()
    gesture_settings["pinch_threshold"] = tap_duration_slider.get()
    gesture_settings["gesture_timeout"] = gesture_timeout_slider.get()
    gesture_settings["enable_feedback"] = feedback_switch.get()
    data["gesture_settings"] = gesture_settings
    with open(json_filename, "w") as outfile:
        json.dump(data, outfile, indent=4)
    show_popup("Gesture settings saved successfully!", "Success")
def start_recording():
    global recording, hotkey_id
    if hotkey_id is not None:
        keyboard.remove_hotkey(hotkey_id)
    recording = True
    record_button.configure(state="disabled", text="Press new hotkey...")
    threading.Thread(target=record_hotkey_thread, daemon=True).start()

def record_hotkey_thread():
    try:
        new_hotkey = keyboard.read_hotkey()
        if new_hotkey:
            update_hotkey_config(new_hotkey)
    finally:
        root.after(0, lambda: record_button.configure(
            state="normal", text="Record New Hotkey"))
        global recording
        recording = False

def update_hotkey_config(new_hotkey):
    global current_hotkey, hotkey_id
    current_hotkey = new_hotkey
    data["hotkey"] = new_hotkey
    hotkey_id = keyboard.add_hotkey(new_hotkey, toggle_ui)
    root.after(0, lambda: hotkey_label.configure(text=new_hotkey))

def on_submit():
    data["mappings"] = {gesture: menu.get() for gesture, menu in action_menus.items()}
    data["modes"] = {mode: switch.get() for mode, switch in mode_switches.items()}
    data["hotkey"] = current_hotkey
    data["gesture_settings"] = gesture_settings
    with open(json_filename, "w") as outfile:
        json.dump(data, outfile, indent=4)
    show_popup("Settings saved successfully!", "Success")

def toggle_ui():
    if not recording and root.winfo_viewable():
        root.withdraw()
    elif not recording:
        fade_in()

def fade_in():
    root.deiconify()
    root.attributes("-alpha", 0)
    for i in range(1, 11):
        root.attributes("-alpha", i * 0.1)
        time.sleep(0.03)

def start_hotkey_listener():
    global hotkey_id
    hotkey_id = keyboard.add_hotkey(current_hotkey, toggle_ui)

def show_popup(message, title):
    popup = ctk.CTkToplevel(root)
    popup.attributes("-topmost", True)
    popup.geometry("300x200")
    frame = ctk.CTkFrame(popup)
    frame.pack(fill="both", expand=True, padx=5, pady=5)
    ctk.CTkLabel(frame, text=title, font=TITLE_FONT).pack(pady=10)
    ctk.CTkLabel(frame, text=message, font=MODERN_FONT).pack(pady=5)
    ctk.CTkButton(frame, text="Close", command=popup.destroy).pack(pady=15)

if __name__ == "__main__":
    run_ui()