# Glitched Da Kitty Cat's Steam Game Gen

[![Discord Presence](https://lanyard-profile-readme.vercel.app/api/1361130884140634322?theme=dark)](https://discord.com/users/1361130884140634322)

A tool to search for Steam games, fetch their details, and download them with ease. Includes features like game information popups, trailers, screenshots, and more.

## Prerequisites

- [Python](https://www.python.org/) (v3.10 or higher recommended)
- pip (comes with Python)

## Installation

1. Clone this repository.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Configuration

No additional configuration is required. The app uses a `lookup.txt` file for game data and fetches game details from the Steam API.

## Running the App

To start the app, run:

```bash
python app.py
```

## Features

- Search for Steam games by name.
- Fetch detailed game information, including trailers, screenshots, and descriptions.
- Download games as zip files, automatically extract them, and delete the zip after extraction.
- Open games directly in the Steam browser.

## New Feature: Auto Add Game to Steam

With the new Auto Add feature, you no longer need SteamTools to add games to Steam. This feature automatically places the necessary `.lua` and `.manifest` files into the appropriate Steam directories and restarts Steam for you but it will require admin.


## Using SteamTools to Add Games to Your Steam Library

### Do this - 

1. Download and install [SteamTools](https://www.steamtools.net/download.html#)
2. Run the setup you downloaded
3. Run the Steamtools.exe
4. Go to the game you want to download's folder with the lua, manifests, sts
5. Select everything in that folder execept the `README.txt` if thats in it
6. Drag it onto the floating steam 
7. Then Restart your steam client
8. Download the game and have fun :)

### Or Watch This Video - 

[Link To Youtube Video](https://youtu.be/3T47Uwx9QlM?si=qFwmUPDvsvFuFLpy&t=12)

## Credits

Thanks to [fares.top](https://fares.top/) for the game downloads/database

## Project Structure

- `app.py`: Main Flask app entry point.
- `static/`: Contains static files like `lookup.txt` and `styles.css`.
- `templates/`: Contains HTML templates for the app.
- `README.md`: This file.
- `requirements.txt`: Required Modules From Python

## Notes

- This project is intended for educational and personal use only.
- Make sure to keep your environment secure when running the app.
- This readme was AI-generated because I am lazy and didn't sleep.
