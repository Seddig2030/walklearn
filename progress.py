# -*- coding: utf-8 -*-
import json, os
from datetime import date, timedelta

KEY = "walklearn_progress.json"

DEFAULT = {"level": None, "completedLessons": [], "streakDays": 0, "lastActiveDate": None}

def path():
    try:
        from kivy.app import App
        return os.path.join(App.get_running_app().user_data_dir, KEY)
    except Exception:
        return os.path.join(os.path.dirname(__file__), KEY)

def load():
    try:
        with open(path(), "r", encoding="utf-8") as f:
            x = DEFAULT.copy(); x.update(json.load(f)); return x
    except Exception:
        return DEFAULT.copy()

def save(state):
    os.makedirs(os.path.dirname(path()), exist_ok=True)
    with open(path(), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def set_level(level):
    s=load(); s["level"]=level; save(s); return s

def complete(lesson_id):
    s=load()
    if lesson_id not in s["completedLessons"]:
        s["completedLessons"].append(lesson_id)
    today=date.today()
    today_s=today.isoformat()
    if s["lastActiveDate"] != today_s:
        yesterday=(today-timedelta(days=1)).isoformat()
        s["streakDays"] = s["streakDays"] + 1 if s["lastActiveDate"] == yesterday else 1
        s["lastActiveDate"]=today_s
    save(s); return s

def reset():
    save(DEFAULT.copy()); return DEFAULT.copy()
