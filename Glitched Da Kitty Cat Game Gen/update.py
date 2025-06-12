import os
import shutil
import subprocess
import customtkinter as ctk
import threading
import ctypes
REPO_URL = "https://github.com/Glitched-Da-Kitty-Cat-Productions/Glitched-Da-Kitty-Cat-Steam-Game-Gen"
CLONE_DIR = "temp_repo"
TARGET_FILES = ["app.py", "requirements.txt", "src", "Game Gen.exe"]

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(e)
        exit(1)

def backup_files():
    backup_dir = "backup"
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    os.makedirs(backup_dir)
    for item in TARGET_FILES:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.copytree(item, os.path.join(backup_dir, item))
            else:
                shutil.copy(item, backup_dir)
    print(f"Backup created at: {backup_dir}")

def clone_repo():
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR)
    run_command(f"git clone {REPO_URL} {CLONE_DIR}")
    print(f"Cloned repository to: {CLONE_DIR}")

def update_files():
    for item in TARGET_FILES:
        source_path = os.path.join(CLONE_DIR, item)
        if os.path.exists(source_path):
            if os.path.isdir(source_path):
                if os.path.exists(item):
                    shutil.rmtree(item)
                shutil.copytree(source_path, item)
            else:
                shutil.copy(source_path, item)
            print(f"Updated: {item}")
        else:
            print(f"Skipped: {item} (not found in repository)")

def cleanup():
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR)
    print(f"Cleaned up temporary files.")

class UpdateGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Glitched Da Kitty Cat Auto-Updater")
        self.geometry("600x400")

        self.header_label = ctk.CTkLabel(self, text="Auto-Updater", font=("Arial", 24, "bold"))
        self.header_label.pack(pady=20)

        self.log_text = ctk.CTkTextbox(self, height=15, width=50)
        self.log_text.pack(pady=10, padx=10, fill="both", expand=True)

        self.update_button = ctk.CTkButton(self, text="Start Update", command=self.start_update)
        self.update_button.pack(pady=10)

        self.exit_button = ctk.CTkButton(self, text="Exit", command=self.exit_app)
        self.exit_button.pack(pady=10)

    def log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def start_update(self):
        self.update_button.configure(state="disabled")
        threading.Thread(target=self.run_update, daemon=True).start()

    def run_update(self):
        try:
            self.log("Starting auto-update...")
            backup_files()
            self.log("Backup completed.")
            clone_repo()
            self.log("Repository cloned.")
            update_files()
            self.log("Files updated.")
            cleanup()
            self.log("Temporary files cleaned up.")
            self.log("Auto-update completed successfully.")
        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            self.update_button.configure(state="normal")

    def exit_app(self):
        self.destroy()
        os._exit(0)

if __name__ == "__main__":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    app = UpdateGUI()
    app.mainloop()