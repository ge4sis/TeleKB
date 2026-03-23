import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import datetime
import os
import concurrent.futures
from ..config import Config
from ..db import Database
from ..telegram_service import TelegramService
from ..translator import Translator
from ..file_manager import FileManager
from ..text_utils import TextUtils
from .channel_window import ChannelWindow
from ..settings import Settings

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("TeleKB")
        self.root.geometry("600x500")
        
        self.db = Database(Config.DB_PATH)
        self.telegram_service = TelegramService()
        self.translator = Translator()
        
        self.settings = Settings()
        
        saved_output = self.settings.get("output_dir")
        default_output = os.path.join(os.getcwd(), "output")
        self.output_dir = tk.StringVar(value=saved_output if saved_output else default_output)
        self.is_running = False
        self.log_queue = queue.Queue()
        self.channel_window = None
        
        self.create_widgets()
        self.check_queue()
        
        if not os.path.exists(self.output_dir.get()):
            os.makedirs(self.output_dir.get())
            
        self.sync_from_file()

    def create_widgets(self):
        frame_top = ttk.LabelFrame(self.root, text="Output Directory", padding=10)
        frame_top.pack(fill=tk.X, padx=10, pady=5)
        
        entry_dir = ttk.Entry(frame_top, textvariable=self.output_dir)
        entry_dir.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_browse = ttk.Button(frame_top, text="Browse", command=self.browse_dir)
        btn_browse.pack(side=tk.RIGHT)
        
        frame_controls = ttk.Frame(self.root, padding=10)
        frame_controls.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_run = ttk.Button(frame_controls, text="Run Collection", command=self.start_collection)
        self.btn_run.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_channels = ttk.Button(frame_controls, text="Channel Management", command=self.open_channel_window)
        self.btn_channels.pack(side=tk.LEFT)
        
        self.lbl_status = ttk.Label(frame_controls, text="Ready")
        self.lbl_status.pack(side=tk.RIGHT)
        
        frame_log = ttk.LabelFrame(self.root, text="Logs", padding=10)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.txt_log = tk.Text(frame_log, state=tk.DISABLED, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(frame_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scrollbar.set)
        
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir.set(d)
            self.settings.set("output_dir", d)
            self.sync_from_file()

    def log(self, message):
        self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")

    def check_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.txt_log.configure(state=tk.NORMAL)
            self.txt_log.insert(tk.END, msg + "\n")
            self.txt_log.see(tk.END)
            self.txt_log.configure(state=tk.DISABLED)
        self.root.after(100, self.check_queue)

    def open_channel_window(self):
        if self.channel_window is not None:
            try:
                if self.channel_window.top.winfo_exists():
                    self.channel_window.top.lift()
                    self.channel_window.top.attributes('-topmost', True)
                    self.channel_window.top.after(100, lambda: self.channel_window.top.attributes('-topmost', False))
                    return
            except tk.TclError:
                self.channel_window = None
                
        self.channel_window = ChannelWindow(self.root, self.db, self.telegram_service)

    def start_collection(self):
        if self.is_running:
            return
            
        self.is_running = True
        self.btn_run.configure(state=tk.DISABLED)
        self.btn_channels.configure(state=tk.DISABLED)
        self.lbl_status.config(text="Running...")
        self.log("Starting collection...")
        
        threading.Thread(target=self.run_collection_thread, daemon=True).start()

    def run_collection_thread(self):
        try:
            self.log("Connecting to Telegram...")
            
            def _request_ui_input(prompt_type):
                f = concurrent.futures.Future()
                self.root.after(0, lambda: self._show_login_dialog(prompt_type, f))
                return f.result()

            phone_cb = lambda: _request_ui_input("phone")
            code_cb = lambda: _request_ui_input("code")
            pw_cb = lambda: _request_ui_input("password")
            
            connected = self.telegram_service.connect(
                phone_callback=phone_cb,
                code_callback=code_cb,
                password_callback=pw_cb
            )
            
            if not connected:
                self.log("Login failed or cancelled.")
                self.finish_collection()
                return

            channels = self.db.get_channels(only_enabled=True)
            if not channels:
                self.log("No enabled channels found.")
                self.finish_collection()
                return

            total_channels = len(channels)
            processed_count = 0
            
            for ch in channels:
                ch_id = ch['channel_id']
                ch_title = ch['title']
                last_id = ch['last_message_id']
                
                self.log(f"Processing channel: {ch_title} (Last ID: {last_id})")
                
                messages = self.telegram_service.fetch_messages(ch_id, min_id=last_id)
                self.log(f"  Found {len(messages)} new messages.")
                
                if not messages:
                    processed_count += 1
                    continue
                    
                max_id = last_id
                success_count = 0
                
                for msg in messages:
                    text = msg.message
                    msg_id = msg.id
                    
                    if not text: 
                        continue
                        
                    # Convert to Markdown for preserving links
                    # We pass msg.entities to helper
                    original_markdown = TextUtils.convert_entities_to_markdown(text, msg.entities)
                        
                    is_kr = TextUtils.is_korean(text)
                    translated = ""
                    
                    if not is_kr:
                        self.log(f"    Translating msg {msg_id}...")
                        translated = self.translator.translate_to_korean(text)
                        if not translated:
                            self.log(f"    Translation failed for {msg_id}. Saving original.")
                    else:
                        self.log(f"    Skipping translation for {msg_id} (Korean detected).")
                    
                    image_paths = []
                    if msg.photo:
                        # Use same date logic as FileManager
                        sub_folder = FileManager.get_target_directory_name(msg.date)
                        images_dir = os.path.join(self.output_dir.get(), sub_folder, "images")
                        
                        if not os.path.exists(images_dir):
                            os.makedirs(images_dir)
                            
                        # Use msg_id for unique filename
                        img_filename = f"{ch_id}_{msg_id}.jpg"
                        img_path = os.path.join(images_dir, img_filename)
                        
                        self.log(f"    Downloading image for {msg_id}...")
                        downloaded_path = self.telegram_service.download_media(msg, img_path)
                        
                        if downloaded_path:
                            image_paths.append(downloaded_path)
                        else:
                             self.log(f"    Image download failed for {msg_id}")
                    
                    try:
                        fpath = FileManager.save_markdown(
                            channel_name=ch_title,
                            message_text=original_markdown, # Pass markdown here
                            translated_text=translated,
                            message_id=msg_id,
                            message_date=msg.date,
                            output_dir=self.output_dir.get(),
                            is_korean_skipped=is_kr,
                            image_paths=image_paths
                        )

                        self.db.save_message_log(ch_id, msg_id, fpath)
                        success_count += 1
                        if msg_id > max_id:
                            max_id = msg_id
                    except Exception as e:
                        self.log(f"    Error saving file for {msg_id}: {e}")
                
                if max_id > last_id:
                    self.db.update_last_message_id(ch_id, max_id)
                    self.log(f"  Updated last_message_id to {max_id}")
                
                processed_count += 1
                
        except Exception as e:
            self.log(f"Critical Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.finish_collection()

    def finish_collection(self):
        self.is_running = False
        def _update():
            self.btn_run.configure(state=tk.NORMAL)
            self.btn_channels.configure(state=tk.NORMAL)
            self.lbl_status.config(text="Ready")
            self.log("Collection finished.")
            self.sync_to_file()
        self.root.after(0, _update)

    def sync_from_file(self):
        output_path = self.output_dir.get()
        if not output_path or not os.path.exists(output_path):
            return
        
        self.log("Checking for sync state file...")
        sync_data = FileManager.load_sync_state(output_path)
        if sync_data:
            try:
                self.db.update_from_sync_data(sync_data)
                self.log(f"Synced {len(sync_data)} channels from sync_state.json.")
            except Exception as e:
                self.log(f"Error updating from sync file: {e}")
        else:
             self.log("No sync file found or file is empty.")

    def sync_to_file(self):
        output_path = self.output_dir.get()
        if not output_path or not os.path.exists(output_path):
            return
        
        try:
            sync_data = self.db.get_sync_data()
            FileManager.save_sync_state(sync_data, output_path)
            self.log("State saved to sync_state.json.")
        except Exception as e:
            self.log(f"Error saving sync state: {e}")

    def _show_login_dialog(self, prompt_type, future):
        dialog = tk.Toplevel(self.root)
        dialog.title("Telegram Login")
        dialog.geometry("400x150")
        
        lbl = ttk.Label(dialog, text="")
        lbl.pack(pady=10)
        
        entry = ttk.Entry(dialog)
        entry.pack(pady=5, padx=20, fill=tk.X)
        
        if prompt_type == "phone":
            lbl.config(text="Enter Phone (e.g. +82...):")
        elif prompt_type == "code":
            lbl.config(text="Enter Code:")
        elif prompt_type == "password":
            lbl.config(text="Enter Password:")
            entry.config(show="*")
            
        def submit():
            val = entry.get().strip()
            if val:
                future.set_result(val)
                dialog.destroy()
                
        entry.bind('<Return>', lambda e: submit())
        entry.focus_set()
        
        btn = ttk.Button(dialog, text="Submit", command=submit)
        btn.pack(pady=10)
        
        dialog.lift()
        dialog.attributes('-topmost', True)
        
        def on_close():
             if not future.done():
                 future.set_result("")
             dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", on_close)
