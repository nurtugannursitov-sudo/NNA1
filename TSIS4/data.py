"""
SNAKE GAME - Data Layer
Contains: SettingsManager, Database
"""

import json
import os
from datetime import datetime


# ========== SETTINGS MANAGER ==========
class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "snake_color": {
                "head": [50, 255, 100],
                "body": [0, 255, 0],
                "dark_body": [0, 150, 0]
            },
            "grid_overlay": True,
            "sound": True
        }
        self.settings = self.default_settings.copy()
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    for key in loaded:
                        if key in self.settings:
                            if isinstance(self.settings[key], dict) and isinstance(loaded[key], dict):
                                self.settings[key].update(loaded[key])
                            else:
                                self.settings[key] = loaded[key]
                print("Settings loaded")
            except:
                print("Error loading settings, using defaults")
        else:
            self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get_snake_colors(self):
        c = self.settings["snake_color"]
        return (tuple(c["head"]), tuple(c["body"]), tuple(c["dark_body"]))

    def get_grid_overlay(self):
        return self.settings["grid_overlay"]

    def set_grid_overlay(self, value):
        self.settings["grid_overlay"] = value
        self.save_settings()

    def get_sound(self):
        return self.settings["sound"]

    def set_sound(self, value):
        self.settings["sound"] = value
        self.save_settings()

    def set_snake_color(self, part, r, g, b):
        self.settings["snake_color"][part] = [r, g, b]
        self.save_settings()

    def reset_to_defaults(self):
        self.settings = self.default_settings.copy()
        self.save_settings()


# ========== DATABASE ==========
class Database:
    def __init__(self):
        self.scores_file = "scores.json"
        self.scores = self.load_scores()

    def load_scores(self):
        if os.path.exists(self.scores_file):
            try:
                with open(self.scores_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_scores(self):
        with open(self.scores_file, 'w') as f:
            json.dump(self.scores, f, indent=4)

    def save_game_result(self, username, score, level):
        self.scores.append({
            "username": username,
            "score": score,
            "level": level,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:50]
        self.save_scores()

    def get_top_scores(self, limit=10):
        return self.scores[:limit]

    def get_personal_best(self, username):
        best = 0
        for s in self.scores:
            if s["username"] == username and s["score"] > best:
                best = s["score"]
        return best

    def close(self):
        pass
