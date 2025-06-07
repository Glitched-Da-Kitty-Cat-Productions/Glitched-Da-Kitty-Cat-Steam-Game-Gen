import os
import json
import requests
import zipfile
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

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
            for app in data["applist"]["apps"]:
                if app["name"].lower() == game_name.lower():
                    return app["appid"]
        return None
    except Exception as e:
        print(f"Error fetching Steam API: {e}")
        return None

def download_game(steam_id):
    try:
        if not os.path.exists(DOWNLOAD_FOLDER):
            os.makedirs(DOWNLOAD_FOLDER)

        file_path = os.path.join(DOWNLOAD_FOLDER, f"{steam_id}.zip")
        extract_path = os.path.join(DOWNLOAD_FOLDER, steam_id)
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

if __name__ == "__main__":
    port = 5000
    url = f"http://127.0.0.1:{port}/"
    app.run(debug=True, port=port)