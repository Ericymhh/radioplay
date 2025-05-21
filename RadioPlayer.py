import tkinter as tk
from tkinter import ttk, messagebox
import vlc
import json
import os
import random
from datetime import datetime

STATIONS_FILE = "stations.json"
PLAY_HISTORY_FILE = "play_history.log"
ICON_PATH = "Radio.ico"

default_stations = {
    "九八新聞台 News98": "https://stream.rcs.revma.com/pntx1639ntzuv.m4a",
    "環宇廣播電台 FM96.7": "https://stream.rcs.revma.com/srn5f9kmwxhvv",
    "IC之音竹科 FM97.5": "https://stream.rcs.revma.com/7mnq8rt7k5zuv"
}

def load_stations():
    if os.path.exists(STATIONS_FILE):
        with open(STATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(STATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_stations, f, indent=2, ensure_ascii=False)
        return default_stations

def save_stations(stations):
    with open(STATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(stations, f, indent=2, ensure_ascii=False)

def log_play_history(station_name, url):
    with open(PLAY_HISTORY_FILE, "a", encoding="utf-8") as f:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{time_str} | {station_name} | {url}\n")

class RadioPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("廣播電台播放器V1.10")
        self.root.resizable(False, False)
        if os.path.exists(ICON_PATH):
            self.root.iconbitmap(ICON_PATH)

        self.stations = load_stations()
        self.player = vlc.MediaPlayer()
        self.is_playing = False
        self.animation_flag = False

        self.station_var = tk.StringVar()
        self.station_combobox = ttk.Combobox(root, textvariable=self.station_var, width=50, state="readonly")
        self.station_combobox["values"] = list(self.stations.keys())
        if self.stations:
            self.station_combobox.current(0)
        self.station_combobox.pack(pady=5)

        control_frame = tk.Frame(root)
        control_frame.pack(pady=5)

        self.play_button = tk.Button(control_frame, text="▶ 撥放", width=10, command=self.toggle_play)
        self.play_button.grid(row=0, column=0, padx=5)

        volume_icon = tk.Label(control_frame, text="🔊", font=("Arial", 14))
        volume_icon.grid(row=0, column=1, padx=(10, 0))

        self.volume_var = tk.DoubleVar(value=100)
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure("TScale", troughcolor="#ddd", background="#4a90e2", thickness=15, sliderthickness=20)

        self.volume_slider = ttk.Scale(control_frame, from_=0, to=200, orient="horizontal",
                                       variable=self.volume_var, style="TScale",
                                       command=self.set_volume, length=180)
        self.volume_slider.grid(row=0, column=2, padx=5)

        self.volume_label = tk.Label(control_frame, text="100%", font=("Arial", 12))
        self.volume_label.grid(row=0, column=3, padx=(5, 10))

        self.animation_label = tk.Label(root, text="", font=("Consolas", 24))
        self.animation_label.pack(pady=5)

        self.marquee_label = tk.Label(root, text="請連接電台", font=("Microsoft JhengHei UI", 14), fg="#333")
        self.marquee_label.pack(pady=(0, 10))
        self.marquee_text = ""
        self.marquee_pos = 0
        self.marquee_running = False

        setting_frame = tk.Frame(root)
        setting_frame.pack(pady=5)

        tk.Button(setting_frame, text="➕ 新增電台", command=lambda: self.open_station_editor()).grid(row=0, column=0, padx=5)
        tk.Button(setting_frame, text="✏️ 編輯電台", command=lambda: self.open_station_editor(edit=True)).grid(row=0, column=1, padx=5)
        tk.Button(setting_frame, text="❌ 刪除電台", command=self.delete_station).grid(row=0, column=2, padx=5)
        tk.Button(setting_frame, text="📜 檢視播放紀錄", command=self.view_play_history).grid(row=0, column=3, padx=5)

        self.set_volume(None)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def toggle_play(self):
        if self.is_playing:
            self.player.stop()
            self.play_button.config(text="▶ 撥放")
            self.is_playing = False
            self.animation_flag = False
            self.update_marquee_text("請連接電台")
            self.animation_label.config(text="")
        else:
            station_name = self.station_var.get()
            url = self.stations.get(station_name)
            if url:
                self.player.set_mrl(url)
                self.player.play()
                log_play_history(station_name, url)
                self.play_button.config(text="⏸ 暫停")
                self.is_playing = True
                self.animation_flag = True
                self.update_marquee_text(f"正在連接 {station_name} 電台")
                self.start_animation()
                self.root.after(3000, lambda: self.update_playing_status(station_name))

    def update_playing_status(self, station_name):
        if not self.is_playing:
            return
        if self.player.is_playing():
            self.update_marquee_text(f"正在撥放 {station_name} 電台")
        else:
            self.root.after(1000, lambda: self.update_playing_status(station_name))

    def set_volume(self, _):
        volume = int(self.volume_var.get())
        self.player.audio_set_volume(volume)
        display_vol = f"{volume}% (Boost)" if volume > 100 else f"{volume}%"
        self.volume_label.config(text=display_vol)

    def start_animation(self):
        self.animate_label()

    def animate_label(self):
        if not self.animation_flag:
            self.animation_label.config(text="")
            return
        bars = "".join("▁▂▃▄▅▆▇█"[random.randint(0, 7)] for _ in range(10))
        self.animation_label.config(text=bars)
        self.root.after(200, self.animate_label)

    def update_marquee_text(self, text):
        self.marquee_text = text + "    "
        self.marquee_pos = 0
        if not self.marquee_running:
            self.marquee_running = True
            self.run_marquee()

    def run_marquee(self):
        if not self.marquee_running:
            return
        display_text = self.marquee_text[self.marquee_pos:] + self.marquee_text[:self.marquee_pos]
        self.marquee_label.config(text=display_text)
        self.marquee_pos = (self.marquee_pos + 1) % len(self.marquee_text)
        self.root.after(200, self.run_marquee)

    def open_station_editor(self, edit=False):
        editor = tk.Toplevel(self.root)
        editor.title("電台設定")
        editor.geometry("400x180")
        editor.resizable(False, False)
        if os.path.exists(ICON_PATH):
            editor.iconbitmap(ICON_PATH)

        if edit:
            current_name = self.station_var.get()
            if not current_name:
                messagebox.showwarning("未選擇電台", "請先選擇要編輯的電台。", parent=self.root)
                editor.destroy()
                return
            current_url = self.stations.get(current_name)
        else:
            current_name = ""
            current_url = ""

        tk.Label(editor, text="電台名稱：").pack(pady=5)
        name_entry = tk.Entry(editor, width=50)
        name_entry.pack()
        name_entry.insert(0, current_name)

        tk.Label(editor, text="串流網址：").pack(pady=5)
        url_entry = tk.Entry(editor, width=50)
        url_entry.pack()
        url_entry.insert(0, current_url)

        def save_station():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            if not name or not url:
                messagebox.showerror("錯誤", "請填寫完整資訊。", parent=editor)
                return
            self.stations[name] = url
            save_stations(self.stations)
            self.station_combobox["values"] = list(self.stations.keys())
            self.station_combobox.set(name)
            editor.destroy()

        tk.Button(editor, text="儲存", command=save_station, width=10).pack(pady=10)

    def delete_station(self):
        name = self.station_var.get()
        if name:
            confirm = messagebox.askyesno("刪除確認", f"確定刪除 {name} 嗎？", parent=self.root)
            if confirm:
                del self.stations[name]
                save_stations(self.stations)
                self.station_combobox["values"] = list(self.stations.keys())
                if self.stations:
                    self.station_combobox.current(0)
                else:
                    self.update_marquee_text("請連接電台")

    def view_play_history(self):
        if not os.path.exists(PLAY_HISTORY_FILE):
            messagebox.showinfo("播放紀錄", "尚無播放紀錄。", parent=self.root)
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("播放紀錄")
        history_window.geometry("600x400")
        history_window.resizable(False, False)
        if os.path.exists(ICON_PATH):
            history_window.iconbitmap(ICON_PATH)

        columns = ("time", "station", "url")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")
        tree.heading("time", text="時間")
        tree.heading("station", text="電台名稱")
        tree.heading("url", text="串流網址")
        tree.column("time", width=150, anchor="center")
        tree.column("station", width=150, anchor="center")
        tree.column("url", width=280, anchor="w")
        tree.pack(fill="both", expand=True)

        with open(PLAY_HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" | ")
                if len(parts) == 3:
                    tree.insert("", "end", values=parts)

    def on_close(self):
        self.player.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RadioPlayerApp(root)
    root.mainloop()
