import os
import json
import requests
import zipfile
from flask import Flask, render_template, request, jsonify
import difflib
import shutil
import subprocess
import psutil 
import ctypes
import pyuac
import threading
import customtkinter as ctk
import tkinter.scrolledtext as st
import logging
import re
from tkinter import Text
from tkinter import END
import ansi2html
from colorama import init, AnsiToWin32
from io import StringIO

app = Flask(__name__, static_folder="src/static", template_folder="src/templates")

GAME_DATA_URL = "https://fares.top/game_data.json"
GAME_DOWNLOAD_URL = "https://steamdatabase.s3.eu-north-1.amazonaws.com/{steam_id}.zip"
STEAM_API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v0002/"
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "downloads")

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def load_game_data():
    try:
        response = requests.get(GAME_DATA_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch game data. HTTP {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error loading game data: {e}")
        return {}

def find_steam_id_by_name(game_name):
    try:
        response = requests.get(STEAM_API_URL)
        if response.status_code == 200:
            data = response.json()
            game_names = [app["name"] for app in data["applist"]["apps"]]
            closest_matches = difflib.get_close_matches(game_name, game_names, n=1, cutoff=0.6)
            if closest_matches:
                matched_name = closest_matches[0]
                for app in data["applist"]["apps"]:
                    if app["name"].lower() == matched_name.lower():
                        return app["appid"]
        return None
    except Exception as e:
        print(f"Error fetching Steam API: {e}")
        return None

def download_game(steam_id):
    try:
        if not os.path.exists(DOWNLOAD_FOLDER):
            os.makedirs(DOWNLOAD_FOLDER)

        game_details = fetch_game_details(steam_id)
        if not game_details:
            return f"Failed to fetch game details for Steam ID: {steam_id}"

        game_name = game_details.get("name", f"Game {steam_id}").replace(":", "").replace("/", "_").replace("\\", "_")
        file_path = os.path.join(DOWNLOAD_FOLDER, f"{steam_id}.zip")
        extract_path = os.path.join(DOWNLOAD_FOLDER, game_name)
        download_url = GAME_DOWNLOAD_URL.format(steam_id=steam_id)

        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            os.remove(file_path)

            return f"Game downloaded and extracted successfully: {extract_path}"
        else:
            return f"Failed to download game. HTTP {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

def fetch_game_details(steam_id):
    try:
        api_url = f"https://store.steampowered.com/api/appdetails?appids={steam_id}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            if data.get(str(steam_id), {}).get("success"):
                return data[str(steam_id)]["data"]
        return None
    except Exception as e:
        print(f"Error fetching game details: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        game_name = request.form.get("game_name", "").strip()
        if not game_name:
            return render_template("index.html", error="Please enter a game name.")

        steam_id = find_steam_id_by_name(game_name)
        if steam_id:
            game_details = fetch_game_details(steam_id)
            if game_details:
                return render_template(
                    "index.html",
                    success=f"Game found: {game_name} (Steam ID: {steam_id})",
                    steam_id=steam_id,
                    game_details=game_details,
                )
            else:
                return render_template("index.html", error="Failed to fetch game details.")
        else:
            return render_template("index.html", error="Game not found.")
    return render_template("index.html")

@app.route("/games-list", methods=["GET", "POST"])
def games_list():
    try:
        search_query = request.form.get("search_query", "").strip().lower() if request.method == "POST" else ""
        game_data = load_game_data()
        games = []

        if search_query:
            steam_id = find_steam_id_by_name(search_query)
            if steam_id:
                game_details = fetch_game_details(steam_id)
                if game_details:
                    games.append({
                        "name": game_details.get("name", f"Game {steam_id}"),
                        "steam_id": steam_id,
                        "header_image": game_details.get("header_image", ""),
                        "short_description": game_details.get("short_description", "No description available."),
                        "price": game_details.get("price_overview", {}).get("final_formatted", "Free"),
                        "release_date": game_details.get("release_date", {}).get("date", "Unknown"),
                    })
            else:
                return render_template("games_list.html", error="No close matches found for your search.")
        else:
            count = 0
            for game_id, game_info in game_data.items():
                if count >= 30:
                    break
                game_details = fetch_game_details(game_id)
                if game_details:
                    games.append({
                        "name": game_details.get("name", f"Game {game_id}"),
                        "steam_id": game_id,
                        "header_image": game_details.get("header_image", ""),
                        "short_description": game_details.get("short_description", "No description available."),
                        "price": game_details.get("price_overview", {}).get("final_formatted", "Free"),
                        "release_date": game_details.get("release_date", {}).get("date", "Unknown"),
                    })
                    count += 1

        return render_template("games_list.html", games=games, search_query=search_query)
    except Exception as e:
        return render_template("games_list.html", error=f"Error: {e}")

@app.route("/game/<steam_id>", methods=["GET"])
def game_details(steam_id):
    try:
        game_details = fetch_game_details(steam_id)
        if game_details:
            return render_template("game_details.html", game_details=game_details)
        else:
            return render_template("game_details.html", error="Game details not found.")
    except Exception as e:
        return render_template("game_details.html", error=f"Error: {e}")

@app.route("/download/<steam_id>", methods=["POST"])
def download(steam_id):
    result = download_game(steam_id)
    return jsonify({"success": True, "message": result})

@app.route('/run-admin', methods=['POST'])
def run_admin():
    try:
        if not pyuac.isUserAdmin():
            pyuac.runAsAdmin()
            os._exit(0)
            return jsonify({"message": "Re-launching as admin! Please refresh the page."})
        else:
            return jsonify({"message": "App is already running with admin privileges."})
    except Exception as e:
        return jsonify({"message": f"Failed to restart app with admin privileges: {e}"}), 500

@app.route('/auto-add-game', methods=['POST'])
def auto_add_game():
        if not request.is_json or request.json is None:
            return jsonify({"message": "Invalid or missing JSON in request."}), 400
        steam_id = request.json.get('steam_id')
        if not steam_id:
            return jsonify({"message": "Steam ID is required."}), 400
        downloaded_game = download_game(steam_id)
        if "Error" in downloaded_game:
            return jsonify({"message": downloaded_game}), 500
        game_details = fetch_game_details(steam_id)
        if not game_details:
            return jsonify({"message": "Failed to fetch game details."}), 500

        game_name = game_details.get("name", f"Game {steam_id}").replace(":", "").replace("/", "_").replace("\\", "_")
        lua_source_folder = os.path.join(DOWNLOAD_FOLDER, game_name)

        lua_target_folder = r"C:\Program Files (x86)\Steam\config\stplug-in"
        manifest_target_folder = r"C:\Program Files (x86)\Steam\config\depotcache"

        try:
            for root, _, files in os.walk(lua_source_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    os.chmod(file_path, 0o777) 

            os.chmod(lua_source_folder, 0o777)

            for root, _, files in os.walk(lua_source_folder):
                for file in files:
                    if file.endswith('.lua'):
                        shutil.copy(os.path.join(root, file), lua_target_folder)

            for root, _, files in os.walk(lua_source_folder):
                for file in files:
                    if file.endswith('.manifest'):
                        shutil.copy(os.path.join(root, file), manifest_target_folder)

            shutil.rmtree(lua_source_folder)

            for process in psutil.process_iter(['name']):
                if process.info['name'] and ('steam' in process.info['name'].lower() or 'steamservice' in process.info['name'].lower()):
                    process.terminate()
            subprocess.run([r"C:\Program Files (x86)\Steam\Steam.exe"])

            return jsonify({"message": "Game files added to Steam and Steam restarted successfully."})
        except PermissionError as e:
            return jsonify({"message": f"Permission error: {e}"}), 500
        except Exception as e:
            return jsonify({"message": f"Failed to auto-add game to Steam: {e}"}), 500


@app.route('/remove-from-library', methods=['POST'])
def remove_from_library():
    try:
        if not request.is_json or request.json is None:
            return jsonify({"message": "Invalid request."}), 400

        steam_id = request.json.get('steam_id')
        if not steam_id:
            return jsonify({"message": "Steam ID is required."}), 400

        game_details = fetch_game_details(steam_id)
        if not game_details:
            return jsonify({"message": "Failed to fetch game details."}), 404

        game_name = game_details.get("name", f"Game {steam_id}").replace(":", "").replace("/", "_").replace("\\", "_")
        lua_target_folder = r"C:\Program Files (x86)\Steam\config\stplug-in"
        manifest_target_folder = r"C:\Program Files (x86)\Steam\config\depotcache"

        for root, _, files in os.walk(lua_target_folder):
            for file in files:
                if file.startswith(str(steam_id)) and file.endswith(".lua"):
                    os.remove(os.path.join(root, file))

        for root, _, files in os.walk(manifest_target_folder):
            for file in files:
                if file.startswith(str(steam_id)) and file.endswith(".manifest"):
                    os.remove(os.path.join(root, file))
                    
        for process in psutil.process_iter(['name']):
            if process.info['name'] and ('steam' in process.info['name'].lower() or 'steamservice' in process.info['name'].lower()):
                process.terminate()
        subprocess.run([r"C:\Program Files (x86)\Steam\Steam.exe"])

        return jsonify({"message": "Game removed from library and Steam restarted successfully."})
    except Exception as e:
        return jsonify({"message": f"Error: {e}"}), 500


@app.route('/check-admin', methods=['GET'])
def check_admin():
    if is_admin():
        return jsonify({"message": "The app is running with admin privileges."})
    else:
        return jsonify({"message": "The app is NOT running with admin privileges."})

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False
init()

class TextWidgetHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.ansi_stream = StringIO()
        self.ansi_converter = AnsiToWin32(self.ansi_stream)

    def emit(self, record):
        msg = self.format(record)
        self.ansi_stream.seek(0)
        self.ansi_stream.truncate(0)
        self.ansi_converter.write(msg)
        converted_msg = self.ansi_stream.getvalue()
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", converted_msg + "\n")
        self.text_widget.configure(state="disabled")
        self.text_widget.see("end")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SteamGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Glitched Da Kitty Cat Steam Game Gen")
        self.iconbitmap("src/static/Steam Game Logo.ico")
        self.geometry("1000x700")
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, height=50)
        self.header_frame.pack(fill="x")
        self.header_label = ctk.CTkLabel(
            self.header_frame, text="Glitched Da Kitty Cat Steam Game Gen", font=("Arial", 24, "bold"), anchor="w"
        )
        self.header_label.pack(side="left", padx=20)
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0, width=200)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_label = ctk.CTkLabel(
            self.sidebar_frame, text="Menu", font=("Arial", 18, "bold"), anchor="w"
        )
        self.sidebar_label.pack(pady=10, padx=10)
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True)
        self.console_output = st.ScrolledText(
            self.content_frame, wrap="word", height=20, width=80, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 12)
        )
        self.console_output.pack(pady=10, padx=10, fill="both", expand=True)
        self.exit_button = ctk.CTkButton(self.content_frame, text="Exit", command=self.exit_app)
        self.exit_button.pack(pady=10)
        self.open_website_btn = ctk.CTkButton(self.content_frame, text="Open Website", command=self.open_website)
        self.open_website_btn.pack(pady=10)
    def open_website(self):
        import webbrowser
        webbrowser.open("http://127.0.0.1:5000")

    def exit_app(self):
        self.destroy()
        os._exit(0)

def run_flask_app():
    app.run(debug=True, port=5000, use_reloader=False)

def main():
    gui = SteamGUI()
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    text_handler = TextWidgetHandler(gui.console_output)
    text_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logging.getLogger().addHandler(text_handler)
    logging.getLogger().setLevel(logging.INFO)
    gui.mainloop()

if __name__ == "__main__":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    main()