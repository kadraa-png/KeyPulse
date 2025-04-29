import customtkinter as ctk
from threading import Thread, Event
import time
import subprocess
import json
from tkinter import filedialog, messagebox, Listbox, END, simpledialog, ttk
from pynput import keyboard

APP_SIGNATURE = "AutoKeyClickerProfile"

class AutoKeyClicker:
    def __init__(self):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.listener = keyboard.Listener(on_press=self.global_hotkey_handler)
        self.listener.start()

        self.app = ctk.CTk()
        self.app.title("KeyPulse")
        self.app.geometry("460x600")
        self.app.resizable(False, False)
        self.running = False
        self.stop_event = Event()

        self.repeat = 0
        self.max_duration = 0
        self.start_delay = 0

        self.build_ui()
        self.macros = []
        self.app.mainloop()

    def build_ui(self):
        top_row = ctk.CTkFrame(self.app, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(5, 0))

        self.macro_button = ctk.CTkButton(top_row, text="🧩", width=30, command=self.open_macro_popup)
        self.macro_button.pack(side="left", padx=(0, 5))

        self.mouse_button = ctk.CTkButton(top_row, text="🖱", width=30, command=self.open_mouse_popup)
        self.mouse_button.pack(side="left")

        ctk.CTkFrame(top_row, width=1, height=1).pack(side="left", expand=True, fill="x")


        ctk.CTkLabel(self.app, text="Key to Press:").pack(pady=(10, 0))
        self.key_entry = ctk.CTkEntry(self.app, width=200)
        self.key_entry.insert(0, "F10")
        self.key_entry.pack(pady=5)

        ctk.CTkButton(self.app, text="🗂 Key List", command=self.show_key_list).pack(pady=5)

        ctk.CTkLabel(self.app, text="Delay Before Press:").pack(pady=(10, 0))
        delay_frame = ctk.CTkFrame(self.app)
        delay_frame.pack(pady=5)
        self.hour_entry = self.create_labeled_entry(delay_frame, "Hrs", 0)
        self.minute_entry = self.create_labeled_entry(delay_frame, "Min", 0)
        self.second_entry = self.create_labeled_entry(delay_frame, "Sec", 1)
        self.ms_entry = self.create_labeled_entry(delay_frame, "ms", 0)

        btn_frame = ctk.CTkFrame(self.app)
        btn_frame.pack(pady=10)
        self.start_button = ctk.CTkButton(btn_frame, text="▶ Start", command=self.start_clicking, width=100)
        self.start_button.pack(side="left", padx=10)
        self.stop_button = ctk.CTkButton(btn_frame, text="⏹ Stop", command=self.stop_clicking, width=100, state="disabled")
        self.stop_button.pack(side="left", padx=10)

        advanced_frame = ctk.CTkFrame(self.app)
        advanced_frame.pack(pady=10)
        ctk.CTkLabel(advanced_frame, text="Advanced:").pack()
        ctk.CTkButton(advanced_frame, text="Repeat Count", command=self.set_repeat).pack(pady=2)
        ctk.CTkButton(advanced_frame, text="Max Duration (sec)", command=self.set_max_duration).pack(pady=2)
        ctk.CTkButton(advanced_frame, text="Start Delay (sec)", command=self.set_start_delay).pack(pady=2)

        action_frame = ctk.CTkFrame(self.app)
        action_frame.pack(pady=5)
        ctk.CTkButton(action_frame, text="💾 Save Profile", command=self.save_profile).pack(side="left", padx=10)
        ctk.CTkButton(action_frame, text="📂 Load Profile", command=self.load_profile).pack(side="left", padx=10)
        ctk.CTkButton(action_frame, text="🕵 Test Mode", command=self.test_mode).pack(side="left", padx=10)

        self.status_label = ctk.CTkLabel(self.app, text="Status: Idle", font=("Segoe UI", 12, "italic"))
        self.status_label.pack(pady=10)

    def create_labeled_entry(self, parent, label, default):
        frame = ctk.CTkFrame(parent)
        frame.pack(side="left", padx=5)
        ctk.CTkLabel(frame, text=label).pack()
        entry = ctk.CTkEntry(frame, width=50)
        entry.insert(0, str(default))
        entry.pack()
        return entry

    def open_mouse_popup(self):
        self.mouse_popup = ctk.CTkToplevel(self.app)
        self.mouse_popup.title("Mouse Automation")
        self.mouse_popup.geometry("320x350")
        self.mouse_popup.resizable(False, False)
        self.mouse_popup.protocol("WM_DELETE_WINDOW", self.close_mouse_popup)

        ctk.CTkLabel(self.mouse_popup, text="Mouse Clicker", font=("Segoe UI", 16)).pack(pady=10)

        delay_frame = ctk.CTkFrame(self.mouse_popup)
        delay_frame.pack(pady=5)
        self.m_hour = self.create_labeled_entry(delay_frame, "Hrs", 0)
        self.m_minute = self.create_labeled_entry(delay_frame, "Min", 0)
        self.m_second = self.create_labeled_entry(delay_frame, "Sec", 1)
        self.m_ms = self.create_labeled_entry(delay_frame, "ms", 0)

        self.mouse_button = ctk.StringVar(value="1")
        for text, val in [("Left Click", "1"), ("Middle Click", "2"), ("Right Click", "3")]:
            ctk.CTkRadioButton(self.mouse_popup, text=text, variable=self.mouse_button, value=val).pack(pady=2)

        control_frame = ctk.CTkFrame(self.mouse_popup)
        control_frame.pack(pady=10)
        self.mouse_start = ctk.CTkButton(control_frame, text="▶ Start", command=self.start_mouse_clicking, width=100)
        self.mouse_start.pack(side="left", padx=10)
        self.mouse_stop = ctk.CTkButton(control_frame, text="⏹ Stop", command=self.stop_mouse_clicking, width=100, state="disabled")
        self.mouse_stop.pack(side="left", padx=10)

        self.mouse_status = ctk.CTkLabel(self.mouse_popup, text="Status: Idle", font=("Segoe UI", 10, "italic"))
        self.mouse_click_count = 0
        self.mouse_counter_label = ctk.CTkLabel(self.mouse_popup, text="Clicks: 0", font=("Segoe UI", 10))
        self.mouse_counter_label.pack()
        self.mouse_status.pack(pady=10)

    def start_mouse_clicking(self):
        delay = self.get_mouse_delay()
        if delay is None:
            return
        self.mouse_stop_event = Event()
        self.mouse_start.configure(state="disabled")
        self.mouse_stop.configure(state="normal")
        self.mouse_status.configure(text="Running...")

        def loop():
            while not self.mouse_stop_event.is_set():
                subprocess.run(["xdotool", "click", self.mouse_button.get()])
                self.mouse_status.configure(text=f"Clicked button {self.mouse_button.get()}")
                self.mouse_click_count += 1
                if self.mouse_counter_label.winfo_exists():
                    self.mouse_counter_label.configure(text=f"Clicks: {self.mouse_click_count}")
                time.sleep(delay)
            if self.mouse_status.winfo_exists():
                self.mouse_status.configure(text="Stopped")


        Thread(target=loop, daemon=True).start()

    def stop_mouse_clicking(self):
        if hasattr(self, "mouse_stop_event"):
            self.mouse_stop_event.set()

        if hasattr(self, "mouse_start") and self.mouse_start.winfo_exists():
            self.mouse_start.configure(state="normal")

        if hasattr(self, "mouse_stop") and self.mouse_stop.winfo_exists():
            self.mouse_stop.configure(state="disabled")

        if hasattr(self, "mouse_status") and self.mouse_status.winfo_exists():
            self.mouse_status.configure(text="Stopped")
        self.mouse_click_count = 0
        if hasattr(self, "mouse_counter_label") and self.mouse_counter_label.winfo_exists():
            self.mouse_counter_label.configure(text="Clicks: 0")


    def close_mouse_popup(self):
        self.stop_mouse_clicking()
        if hasattr(self, "mouse_popup") and self.mouse_popup.winfo_exists():
            self.mouse_popup.destroy()


    def get_mouse_delay(self):
        try:
            h = int(self.m_hour.get())
            m = int(self.m_minute.get())
            s = int(self.m_second.get())
            ms = int(self.m_ms.get())
            total = h * 3600 + m * 60 + s + ms / 1000
            if total <= 0:
                raise ValueError
            return total
        except ValueError:
            self.mouse_status.configure(text="Error: Invalid delay")
            return None

    def set_repeat(self):
        try:
            value = simpledialog.askinteger("Repeat Count", "Enter how many times to repeat (0 for infinite):")
            if value is None:
                return
            self.repeat = max(0, value)
        except Exception:
            messagebox.showerror("Input Error", "Repeat count must be an integer.")

    def set_max_duration(self):
        try:
            value = simpledialog.askfloat("Max Duration", "Enter max duration in seconds:")
            if value is None:
                return
            self.max_duration = max(0, value)
        except Exception:
            messagebox.showerror("Input Error", "Max duration must be a number.")

    def set_start_delay(self):
        try:
            value = simpledialog.askfloat("Start Delay", "Enter delay before start in seconds:")
            if value is None:
                return
            self.start_delay = max(0, value)
        except Exception:
            messagebox.showerror("Input Error", "Start delay must be a number.")

    def get_total_delay(self):
        try:
            h = int(self.hour_entry.get())
            m = int(self.minute_entry.get())
            s = int(self.second_entry.get())
            ms = int(self.ms_entry.get())
            total = h * 3600 + m * 60 + s + ms / 1000
            if total <= 0:
                raise ValueError
            return total
        except ValueError:
            self.status_label.configure(text="Error: Invalid delay")
            return None

    def build_key_string(self):
        return self.key_entry.get().strip()

    def click_loop(self, key, delay):
        count = 0
        start_time = time.time()
        while not self.stop_event.is_set():
            subprocess.run(["xdotool", "key", key])
            count += 1
            self.status_label.configure(text=f"Pressed: {key} ({count})")
            time.sleep(delay)
            if self.repeat and count >= self.repeat:
                break
            if self.max_duration and (time.time() - start_time) >= self.max_duration:
                break
        self.status_label.configure(text="Stopped")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def start_clicking(self):
        key = self.build_key_string()
        delay = self.get_total_delay()
        if not key or delay is None:
            self.status_label.configure(text="Error: Invalid key")
            return

        def start_after_delay():
            time.sleep(self.start_delay)
            Thread(target=self.click_loop, args=(key, delay), daemon=True).start()

        self.running = True
        self.stop_event.clear()
        self.set_inputs_enabled(False)
        self.start_button.configure(state="disabled", text="Start")
        self.stop_button.configure(state="normal", text="Stop (F8)")
        self.status_label.configure(text="Running...")
        Thread(target=start_after_delay, daemon=True).start()


    def stop_clicking(self):
        self.stop_event.set()
        self.running = False
        self.set_inputs_enabled(True)
        self.start_button.configure(state="normal", text="Start (F8)")
        self.stop_button.configure(state="disabled", text="Stop")
        self.status_label.configure(text="Stopped")

    def save_profile(self):
        profile = {
            "signature": APP_SIGNATURE,
            "key": self.key_entry.get(),
            "hrs": self.hour_entry.get(),
            "min": self.minute_entry.get(),
            "sec": self.second_entry.get(),
            "ms": self.ms_entry.get()
        }
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if filepath:
            with open(filepath, "w") as f:
                json.dump(profile, f)
            self.status_label.configure(text="Profile saved")

    def load_profile(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not filepath:
            return
        try:
            with open(filepath, "r") as f:
                profile = json.load(f)
            if profile.get("signature") != APP_SIGNATURE:
                raise ValueError("Invalid signature")
            self.key_entry.delete(0, END)
            self.key_entry.insert(0, profile["key"])
            self.hour_entry.delete(0, END)
            self.hour_entry.insert(0, profile["hrs"])
            self.minute_entry.delete(0, END)
            self.minute_entry.insert(0, profile["min"])
            self.second_entry.delete(0, END)
            self.second_entry.insert(0, profile["sec"])
            self.ms_entry.delete(0, END)
            self.ms_entry.insert(0, profile["ms"])
            self.status_label.configure(text="Profile loaded")
        except Exception:
            messagebox.showerror("Error", "Invalid profile file")

    def test_mode(self):
        key = self.build_key_string()
        delay = self.get_total_delay()
        if not key or delay is None:
            return
        summary = f"🧪 Test Mode\nKey: {key}\nDelay: {delay:.2f}s\n"
        if self.repeat:
            summary += f"Repeat: {self.repeat}x\n"
        if self.max_duration:
            summary += f"Max Duration: {self.max_duration}s\n"
        if self.start_delay:
            summary += f"Start Delay: {self.start_delay}s"
        messagebox.showinfo("Test Mode", summary)

    def show_key_list(self):
        keys = [
            ("a", "A"), ("b", "B"), ("c", "C"), ("1", "1"), ("2", "2"),
            ("Return", "Enter"), ("Escape", "Esc"), ("Tab", "Tab"),
            ("BackSpace", "Backspace"), ("space", "Spacebar"), ("Delete", "Delete"),
            ("Shift", "Shift"), ("Control", "Ctrl"), ("Alt", "Alt"), ("Super", "Windows key"),
            ("Up", "↑ Arrow"), ("Down", "↓ Arrow"), ("Left", "← Arrow"), ("Right", "→ Arrow"),
            ("F1", "F1"), ("F2", "F2"), ("F3", "F3"), ("F4", "F4"),
            ("F5", "F5"), ("F6", "F6"), ("F7", "F7"), ("F8", "F8"),
            ("F9", "F9"), ("F10", "F10"), ("F11", "F11"), ("F12", "F12"),
        ]

        win = ctk.CTkToplevel(self.app)
        win.title("Key List")
        win.geometry("420x500")
        win.resizable(False, False)

        ctk.CTkLabel(win, text="Double-click a row to insert key:").pack(pady=10)

        tree = ttk.Treeview(win, columns=("code", "name"), show="headings", height=20)
        tree.heading("code", text="Key Code")
        tree.heading("name", text="Display Name")
        tree.column("code", anchor="center", width=120)
        tree.column("name", anchor="center", width=200)
        tree.pack(padx=10, pady=5, fill="both", expand=True)

        for code, name in keys:
            tree.insert("", "end", values=(code, name))

        def on_select(event):
            selected = tree.focus()
            if selected:
                values = tree.item(selected, "values")
                if values:
                    key = values[0]
                    self.key_entry.delete(0, 'end')
                    self.key_entry.insert(0, key)
                    win.destroy()

        tree.bind("<Double-1>", on_select)

        ctk.CTkButton(win, text="Close", command=win.destroy).pack(pady=10)

    def open_macro_popup(self):
        self.macro_popup = ctk.CTkToplevel(self.app)
        self.macro_popup.title("Macro Automation")
        self.macro_popup.geometry("500x600")
        self.macro_popup.resizable(False, False)

        ctk.CTkLabel(self.macro_popup, text="Macro Sequence", font=("Segoe UI", 16)).pack(pady=10)

        self.macro_listbox = Listbox(self.macro_popup, height=15, width=60)
        self.macro_listbox.pack(padx=10, pady=10)

        save_load_frame = ctk.CTkFrame(self.macro_popup)
        save_load_frame.pack(pady=5)

        ctk.CTkButton(save_load_frame, text="💾 Save Macro", command=self.save_macro).pack(side="left", padx=10)
        ctk.CTkButton(save_load_frame, text="📂 Load Macro", command=self.load_macro).pack(side="left", padx=10)


        controls = ctk.CTkFrame(self.macro_popup)
        controls.pack(pady=5)

        ctk.CTkButton(controls, text="➕ Add Key", command=self.add_macro_key).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="➕ Add Mouse", command=self.add_macro_mouse).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="🗑 Remove", command=self.remove_macro_step).pack(side="left", padx=5)

        repeat_frame = ctk.CTkFrame(self.macro_popup)
        repeat_frame.pack(pady=10)

        self.repeat_var = ctk.IntVar(value=1)
        self.infinite_repeat = ctk.BooleanVar(value=False)

        ctk.CTkLabel(repeat_frame, text="Repeat Count:").pack(side="left", padx=5)
        self.repeat_entry = ctk.CTkEntry(repeat_frame, width=50)
        self.repeat_entry.insert(0, "1")
        self.repeat_entry.pack(side="left", padx=5)

        self.infinite_checkbox = ctk.CTkCheckBox(
            repeat_frame, text="∞ Infinite", variable=self.infinite_repeat,
            command=lambda: self.repeat_entry.configure(state="disabled" if self.infinite_repeat.get() else "normal")
        )
        self.infinite_checkbox.pack(side="left", padx=10)

        ctk.CTkButton(self.macro_popup, text="▶ Run Macro", command=self.run_macro).pack(pady=10)
        ctk.CTkButton(self.macro_popup, text="Close", command=self.macro_popup.destroy).pack()

    def add_macro_key(self):
        key = simpledialog.askstring("Add Key", "Enter key name:")
        if key:
            delay = simpledialog.askfloat("Delay", "Delay after this step (seconds):", minvalue=0)
            hold = simpledialog.askfloat("Hold Duration", "How long to hold the key (sec):", minvalue=0)
            if delay is not None and hold is not None:
                self.macros.append(("key", key, delay, hold))
                self.macro_listbox.insert(END, f"[Key] {key} ⏱ Hold: {hold:.2f}s → Delay: {delay:.2f}s")

    def add_macro_mouse(self):
        button = simpledialog.askinteger("Mouse Button", "Enter button (1=Left, 2=Middle, 3=Right):", minvalue=1, maxvalue=3)
        if button:
            delay = simpledialog.askfloat("Delay", "Delay after this step (seconds):", minvalue=0)
            hold = simpledialog.askfloat("Hold Duration", "How long to hold the button (sec):", minvalue=0)
            if delay is not None and hold is not None:
                self.macros.append(("mouse", str(button), delay, hold))
                self.macro_listbox.insert(END, f"[Mouse] Button {button} ⏱ Hold: {hold:.2f}s → Delay: {delay:.2f}s")


    def remove_macro_step(self):
        selection = self.macro_listbox.curselection()
        if selection:
            index = selection[0]
            del self.macros[index]
            self.macro_listbox.delete(index)


    def run_macro(self):
        def macro_thread():
            try:
                repeat_times = float("inf") if self.infinite_repeat.get() else int(self.repeat_entry.get())
            except:
                messagebox.showerror("Invalid Repeat", "Please enter a valid repeat count.")
                return

            for _ in range(int(repeat_times) if repeat_times != float("inf") else 99999999):
                for action, target, delay, hold in self.macros:
                    if action == "key":
                        subprocess.run(["xdotool", "keydown", target])
                        time.sleep(hold)
                        subprocess.run(["xdotool", "keyup", target])
                    elif action == "mouse":
                        subprocess.run(["xdotool", "mousedown", target])
                        time.sleep(hold)
                        subprocess.run(["xdotool", "mouseup", target])
                    time.sleep(delay)
                if repeat_times == float("inf"):
                    continue
            messagebox.showinfo("Macro", "Macro execution complete!")

        Thread(target=macro_thread, daemon=True).start()
    def set_inputs_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        print(f"[DEBUG] Setting input state to: {state}")

        widgets = [
            self.key_entry,
            self.hour_entry,
            self.minute_entry,
            self.second_entry,
            self.ms_entry,
        ]
        for w in widgets:
            try:
                w.configure(state=state)
            except Exception as e:
                print(f"Failed to set state for {w}: {e}")

    def save_macro(self):
        if not self.macros:
            messagebox.showinfo("Save Macro", "No macro steps to save.")
            return

        profile = {
            "signature": "AutoKeyClickerMacro",
            "macros": self.macros,
            "repeat": self.repeat_entry.get(),
            "infinite": self.infinite_repeat.get()
        }

        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filepath:
            with open(filepath, "w") as f:
                json.dump(profile, f)
            messagebox.showinfo("Macro", "Macro saved successfully.")

    def load_macro(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return

        try:
            with open(filepath, "r") as f:
                profile = json.load(f)

            if profile.get("signature") != "AutoKeyClickerMacro":
                raise ValueError("Invalid macro file format")

            self.macros = profile["macros"]
            self.macro_listbox.delete(0, END)

            for step in self.macros:
                action, target, delay, hold = step
                label = f"[{action.capitalize()}] {target} ⏱ Hold: {hold:.2f}s → Delay: {delay:.2f}s"
                self.macro_listbox.insert(END, label)

            self.repeat_entry.delete(0, END)
            self.repeat_entry.insert(0, str(profile.get("repeat", "1")))
            self.infinite_repeat.set(profile.get("infinite", False))
            self.repeat_entry.configure(state="disabled" if self.infinite_repeat.get() else "normal")

            messagebox.showinfo("Macro", "Macro loaded successfully.")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load macro: {e}")

    def global_hotkey_handler(self, key):
        try:
            if key == keyboard.Key.f8:
                if self.running:
                    self.app.after(0, self.stop_clicking)
                else:
                    self.app.after(0, self.start_clicking)

            elif key == keyboard.Key.f6:
                if hasattr(self, "mouse_popup") and self.mouse_popup.winfo_exists():
                    if not hasattr(self, "mouse_stop_event") or self.mouse_stop_event.is_set():
                        self.app.after(0, self.start_mouse_clicking)
                    else:
                        self.app.after(0, self.stop_mouse_clicking)

            elif key == keyboard.Key.f7:
                if hasattr(self, "macro_popup") and self.macro_popup.winfo_exists():
                    if not hasattr(self, "macro_running") or not self.macro_running:
                        self.app.after(0, self.run_macro)
                    else:
                        self.macro_running = False
        except Exception as e:
            print(f"[Hotkey Error] {e}")

if __name__ == "__main__":
    AutoKeyClicker()
