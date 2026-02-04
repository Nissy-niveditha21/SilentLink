import os
import platform

class CommandExecutor:
    def __init__(self):
        self.system = platform.system()

    def run_command(self, label):
        if self.system != "Windows":
            print("System commands only supported on Windows.")
            return

        if label == "Thumb Up":
            os.system("nircmd.exe changesysvolume 2000")  # Volume Up
        elif label == "Thumb Down":
            os.system("nircmd.exe changesysvolume -2000")  # Volume Down
        elif label == "Open Palm":
            os.system("nircmd.exe mutesysvolume 2")  # Mute/Unmute
        elif label == "2 Fingers":
            os.system("start notepad.exe")  # Open Notepad
        #elif label == "Fist":
            #os.system("rundll32.exe user32.dll,LockWorkStation")  # Lock Screen
