import os
import sys
import threading
import time
import io
import logging
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, END
import platform
import subprocess
import darkdetect
import sv_ttk

try:
    from PyPDF2 import PdfMerger
except ImportError:
    print("PyPDF2 not found. Please install it using: pip install PyPDF2")
    sys.exit(1)

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
except ImportError:
    print("Google API libraries not found. Please install them using:")
    print("pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


# The scope defines the level of access. Read-only is safest.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'assets\\service_account.json'

# --- IMPORTANT: PASTE YOUR FOLDER ID HERE ---
DRIVE_FOLDER_ID = '1L94Vy-FQblxPG7XoqIjPWe-ebhRYIs3x'

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)



def get_app_data_path(filename):
    try:
        # Determine base path based on whether the app is frozen (packaged) or running from script
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as a PyInstaller bundle
            if os.name == 'win32': # Windows
                base_path = os.path.join(os.getenv('APPDATA'), APP_NAME)
            elif sys.platform == 'darwin': # macOS
                base_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', APP_NAME)
            else: # Linux and other Unix-like
                xdg_config_home = os.getenv('XDG_CONFIG_HOME')
                if xdg_config_home:
                    base_path = os.path.join(xdg_config_home)
                else:
                    base_path = os.path.join(os.path.expanduser('~'))
        else:
            # Running as a script, use the script's directory
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Create the base directory if it doesn't exist
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
        return os.path.join(base_path, filename)
    except Exception as e:
        # Fallback to current working directory if standard paths fail
        print(f"Warning: Could not determine standard app data path due to {e}. Using current working directory as fallback.")
        fallback_path = os.path.join(os.getcwd()) # Create a subfolder in CWD
        if not os.path.exists(fallback_path):
            os.makedirs(fallback_path, exist_ok=True)
        return os.path.join(fallback_path, filename)

class MasechetDownloader:

    # --- Static Class Data and Methods ---
    masechtos_info_static = {
        "Brachos": [36083, 125], "Shabbos": [36104, 312], "Eiruvin": [36087, 207],
        "Psachim": [36101, 240], "Shkalim": [36105, 42], "Yuma": [36112, 173],
        "Sukkah": [36108, 110], "Beitza": [36082, 78], "Rosh Hashana": [36102, 67],
        "Tainis": [36109, 59], "Megilah": [36094, 61], "Moed Katan": [36097, 55],
        "Chagigah": [36084, 51], "Yevamos": [36111, 242], "Kesubos": [36091, 222],
        "Nedarim": [36098, 180], "Nazir": [36100, 130], "Sotah": [36107, 96],
        "Gittin": [36088, 178], "Kedushin": [36092, 162], "Bava Kamma": [36079, 236],
        "Bava Metzia": [36080, 235], "Bava Basra": [36078, 350], "Sanhedrin": [36103, 224],
        "Makkos": [36093, 46], "Shvuos": [36106, 96], "Avodah Zarah": [36077, 150],
        "Horyos": [36089, 25], "Zevachim": [36113, 238], "Menuchos": [36096, 217],
        "Chulin": [36085, 281], "Bechoros": [36081, 119], "Arachin": [36086, 65],
        "Temurah": [36110, 65], "Krisos": [36090, 54], "Meilah": [36095, 41],
        "Nidah": [36099, 143]
    }

    @staticmethod
    def daf_amud_calculator(page_number):
        """
        Calculates the daf and amud from a given page number.
        - Page 1 corresponds to Daf 2a.
        - Page 2 corresponds to Daf 2b.
        - Page 3 corresponds to Daf 3a, and so on.
        """
        if page_number < 1:
            return None, None

        # Calculate the daf number. Since page 1 is daf 2, we add 1 to the page number
        # before the calculation, effectively shifting the start.
        daf = 2 + (page_number - 1) // 2

        # Determine Amud. Odd pages are 'a', even pages are 'b'.
        amud = "a" if page_number % 2 != 0 else "b"

        return daf, amud

    def __init__(self, root):
        self.root = root
        self.root.title("Masechet Downloader (Google Drive Edition)")
        self.root.geometry("550x600")

        self.drive_service = self.authenticate_google_drive()
        if not self.drive_service:
            self.root.destroy()
            return

        self.masechta_folder_ids = {}
        self.theme_auto()
        self.create_widgets()

    def authenticate_google_drive(self):
        """Authenticates with the Google Drive API using a Service Account."""

        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        service_path = os.path.join(base_dir, SERVICE_ACCOUNT_FILE)
        
        if not os.path.exists(service_path): #os.path.join(base_dir, SERVICE_ACCOUNT_FILE)): #os.path.abspath(SERVICE_ACCOUNT_FILE)):
            messagebox.showerror("Authentication Error", f"Service account key file not found: '{SERVICE_ACCOUNT_FILE}'\nPlease follow the setup instructions.")
            return None
        try:
            creds = service_account.Credentials.from_service_account_file(
                service_path, scopes=SCOPES)
            service = build('drive', 'v3', credentials=creds)
            print("[INFO] Successfully authenticated with Google Drive via Service Account.")
            return service
        except HttpError as error:
            messagebox.showerror("API Error", f'An error occurred building the Drive service: {error}')
            return None
        except Exception as e:
            messagebox.showerror("Authentication Error", f'An unexpected error occurred during authentication: {e}')
            return None

    def create_widgets(self):
        """Creates and lays out the tkinter widgets."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- Masechet Selection ---
        masechet_frame = ttk.LabelFrame(main_frame, text="Masechet")
        masechet_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        masechet_frame.columnconfigure(1, weight=1)

        masechtos = list(self.masechtos_info_static.keys())
        self.masechet_var = tk.StringVar()
        masechet_label = ttk.Label(masechet_frame, text="Select Masechet:")
        masechet_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.masechet_combo = ttk.Combobox(masechet_frame, textvariable=self.masechet_var, values=masechtos, state="readonly")
        self.masechet_combo.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.masechet_combo.bind("<<ComboboxSelected>>", self.update_ui_for_masechet)

        # --- Selection Options ---
        options_frame = ttk.LabelFrame(main_frame, text="Download Options")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        options_frame.columnconfigure(0, weight=1)

        # --- Selection Type ---
        self.select_type_var = tk.StringVar(value="Dapim")
        type_frame = ttk.Frame(options_frame)
        type_frame.grid(row=0, column=0, pady=5, sticky=tk.W)
        ttk.Label(type_frame, text="By:").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(type_frame, text="Dapim", variable=self.select_type_var, value="Dapim", command=self.toggle_selection_widgets).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(type_frame, text="Amudim", variable=self.select_type_var, value="Amudim", command=self.toggle_selection_widgets).grid(row=0, column=2, padx=5)

        # --- Selection Mode ---
        self.selection_mode_var = tk.StringVar(value="Range")
        mode_frame = ttk.Frame(options_frame)
        mode_frame.grid(row=1, column=0, pady=5, sticky=tk.W)
        ttk.Label(mode_frame, text="Mode:").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(mode_frame, text="All", variable=self.selection_mode_var, value="All", command=self.toggle_selection_widgets).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(mode_frame, text="Range", variable=self.selection_mode_var, value="Range", command=self.toggle_selection_widgets).grid(row=0, column=2, padx=5)
        ttk.Radiobutton(mode_frame, text="Individual", variable=self.selection_mode_var, value="Individual", command=self.toggle_selection_widgets).grid(row=0, column=3, padx=5)

        # --- Range Frame ---
        self.range_frame = ttk.Frame(options_frame)
        self.range_frame.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))
        self.range_start_var = tk.StringVar()
        self.range_end_var = tk.StringVar()
        ttk.Label(self.range_frame, text="From:").grid(row=0, column=0, padx=5)
        self.range_start_combo = ttk.Combobox(self.range_frame, textvariable=self.range_start_var, width=10)
        self.range_start_combo.grid(row=0, column=1, padx=5)
        ttk.Label(self.range_frame, text="To:").grid(row=0, column=2, padx=5)
        self.range_end_combo = ttk.Combobox(self.range_frame, textvariable=self.range_end_var, width=10)
        self.range_end_combo.grid(row=0, column=3, padx=5)

        # --- Individual Selection Frame ---
        self.individual_frame = ttk.Frame(options_frame)
        self.individual_frame.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.individual_listbox = tk.Listbox(self.individual_frame, selectmode="multiple", height=8)
        self.individual_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.individual_frame.columnconfigure(0, weight=1)
        self.individual_frame.rowconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(self.individual_frame, orient="vertical", command=self.individual_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.individual_listbox.config(yscrollcommand=scrollbar.set)

        # --- Merge Options ---
        merge_frame = ttk.LabelFrame(main_frame, text="Output Options")
        merge_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.merge_all_var = tk.BooleanVar(value=True)
        self.merge_amudim_var = tk.BooleanVar(value=False)
        self.keep_individuals_var = tk.BooleanVar(value=False)
        self.merge_all_check = ttk.Checkbutton(merge_frame, text="Merge entire selection into one PDF", variable=self.merge_all_var)
        self.merge_all_check.grid(row=0, column=0, sticky=tk.W, padx=5)
        self.merge_amudim_check = ttk.Checkbutton(merge_frame, text="Merge Amudim into Dapim", variable=self.merge_amudim_var, command=self.toggle_keep_option)
        self.merge_amudim_check.grid(row=1, column=0, sticky=tk.W, padx=5)
        self.keep_individuals_check = ttk.Checkbutton(merge_frame, text="Keep individual Amud PDFs after merging", variable=self.keep_individuals_var)
        self.keep_individuals_check.grid(row=2, column=0, sticky=tk.W, padx=5)

        # --- Action Buttons ---
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.E), pady=10)
        self.download_button = ttk.Button(action_frame, text="Start Download", command=self.start_download, state=tk.DISABLED)
        self.download_button.grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="Open Downloads Folder", command=self.open_output_folder).grid(row=0, column=0, padx=5)

        # --- Progress Bar & Status ---
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        status_frame.columnconfigure(0, weight=1)
        self.progress_bar = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.status_label = ttk.Label(status_frame, text="Ready.")
        self.status_label.grid(row=1, column=0, sticky=tk.W)

        self.toggle_selection_widgets()
        self.toggle_keep_option()

    def update_ui_for_masechet(self, event=None):
        """Update range and individual lists when a masechet is selected."""
        masechta_name = self.masechet_var.get()
        if not masechta_name:
            self.download_button.config(state=tk.DISABLED)
            return

        _, total_pages = self.masechtos_info_static[masechta_name]
        max_daf = (total_pages + 1) // 2

        # Populate Dapim options
        daf_options = list(range(2, max_daf + 1))
        # Populate Amudim options
        amud_options = []
        for p in range(1, total_pages + 1):
            daf, amud = self.daf_amud_calculator(p)
            amud_options.append(f"{daf}{amud}")

        select_type = self.select_type_var.get()
        if select_type == "Dapim":
            self.range_start_combo['values'] = daf_options
            self.range_end_combo['values'] = daf_options
            self.individual_listbox.delete(0, tk.END)
            for daf in daf_options:
                self.individual_listbox.insert(tk.END, daf)
        else: # Amudim
            self.range_start_combo['values'] = amud_options
            self.range_end_combo['values'] = amud_options
            self.individual_listbox.delete(0, tk.END)
            for amud in amud_options:
                self.individual_listbox.insert(tk.END, amud)

        self.download_button.config(state=tk.NORMAL)

    def toggle_selection_widgets(self, event=None):
        """Show/hide widgets based on selection mode."""
        mode = self.selection_mode_var.get()
        self.range_frame.grid_remove()
        self.individual_frame.grid_remove()

        if mode == "Range":
            self.range_frame.grid()
            if self.range_end_var:
                self.range_end_var.set("")
            if self.range_start_var:
                self.range_start_var.set("")
        elif mode == "Individual":
            self.individual_frame.grid()

        self.update_ui_for_masechet() # Refresh lists

    def toggle_keep_option(self):
        """Enable/disable the 'keep individuals' checkbox."""
        if self.merge_amudim_var.get():
            self.keep_individuals_check.config(state=tk.NORMAL)
        else:
            self.keep_individuals_check.config(state=tk.DISABLED)
            self.keep_individuals_var.set(False)

    def _calculate_pages_to_download(self):
        """
        Determines the set of page numbers to download based on user selection.
        """
        pages = set()
        masechta_name = self.masechet_var.get()
        masechta_info = self.masechtos_info_static.get(masechta_name)
        if not masechta_info:
            return set()

        _, total_pages = masechta_info
        selection_mode = self.selection_mode_var.get()
        select_type = self.select_type_var.get()

        if selection_mode == "All":
            pages.update(range(1, total_pages + 1))

        elif selection_mode == "Range":
            start_val = self.range_start_var.get()
            end_val = self.range_end_var.get()
            if not start_val or not end_val:
                messagebox.showerror("Input Error", "Please select a start and end for the range.")
                return set()

            if select_type == "Dapim":
                start_daf, end_daf = int(start_val), int(end_val)
                for daf in range(start_daf, end_daf + 1):
                    pages.add(2 * (daf - 2) + 1)
                    pages.add(2 * (daf - 2) + 2)
            else:  # Amudim
                start_page = [f"{d}{a}" for p in range(1, total_pages+1) for d,a in [self.daf_amud_calculator(p)]].index(start_val) + 1
                end_page = [f"{d}{a}" for p in range(1, total_pages+1) for d,a in [self.daf_amud_calculator(p)]].index(end_val) + 1
                for p in range(start_page, end_page + 1):
                    pages.add(p)

        elif selection_mode == "Individual":
            selected_indices = self.individual_listbox.curselection()
            if not selected_indices:
                messagebox.showerror("Input Error", "Please select individual items from the list.")
                return set()

            if select_type == "Dapim":
                for i in selected_indices:
                    daf = int(self.individual_listbox.get(i))
                    pages.add(2 * (daf - 2) + 1)
                    pages.add(2 * (daf - 2) + 2)
            else:  # Amudim
                for i in selected_indices:
                    amud_str = self.individual_listbox.get(i)
                    page = [f"{d}{a}" for p in range(1, total_pages+1) for d,a in [self.daf_amud_calculator(p)]].index(amud_str) + 1
                    pages.add(page)

        # Final validation to ensure no pages are out of bounds
        return {p for p in pages if 1 <= p <= total_pages}

    def start_download(self):
        """Main logic to orchestrate the download and merge process."""
        masechta_name = self.masechet_var.get()
        if not masechta_name:
            messagebox.showerror("Error", "Please select a Masechet.")
            return

        if not DRIVE_FOLDER_ID or DRIVE_FOLDER_ID == 'PASTE_YOUR_FOLDER_ID_HERE':
            messagebox.showerror("Setup Error", "Please set the 'DRIVE_FOLDER_ID' variable in the script.")
            return

        download_dir = os.path.join(DOWNLOADS_DIR, masechta_name)
        os.makedirs(download_dir, exist_ok=True)

        self.status_label.config(text=f"Calculating pages for {masechta_name}...")
        self.root.update_idletasks()

        valid_pages = self._calculate_pages_to_download()

        if not valid_pages:
            self.status_label.config(text="No valid pages selected.")
            return

        self.status_label.config(text=f"Found {len(valid_pages)} pages to download.")
        self.progress_bar['maximum'] = len(valid_pages)
        self.progress_bar['value'] = 0
        self.root.update_idletasks()

        downloaded_files_map = {}
        files_to_delete_later = set()

        # --- Main Download Loop ---
        for i, page_num in enumerate(sorted(list(valid_pages))):
            daf, amud = self.daf_amud_calculator(page_num)
            if daf is None: continue

            filename = f"{masechta_name}_Daf{daf}_Amud{amud}.pdf"
            local_path = os.path.join(download_dir, filename)

            self.status_label.config(text=f"Downloading {filename}...")
            self.root.update_idletasks()

            if not os.path.exists(local_path):
                success = self.download_from_drive(masechta_name, filename, local_path)
                if success:
                    downloaded_files_map[page_num] = local_path
                else:
                    self.status_label.config(text=f"Failed to download {filename}. Skipping.")
                    time.sleep(2)
            else:
                downloaded_files_map[page_num] = local_path
                self.status_label.config(text=f"File already exists: {filename}")
                time.sleep(0.5)

            self.progress_bar['value'] = i + 1
            self.root.update_idletasks()

        # --- Merging Logic ---
        self._perform_merging(download_dir, downloaded_files_map, files_to_delete_later)

        # --- Cleanup ---
        if not self.keep_individuals_var.get() and self.merge_amudim_var.get():
            self.clean_up(self, list(files_to_delete_later))

        self.status_label.config(text=f"Download finished for {masechta_name}. Files are in: {download_dir}")
        messagebox.showinfo("Complete", f"Download and merge process for {masechta_name} is complete.")

    def _perform_merging(self, download_dir, downloaded_files_map, files_to_delete_later):
        """Handles all PDF merging operations based on user preferences."""
        files_for_final_merge = []

        if self.merge_amudim_var.get():
            self.status_label.config(text="Merging Amudim into Dapim...")
            self.root.update_idletasks()
            daf_to_files = {}
            for page_num, filepath in downloaded_files_map.items():
                daf, _ = self.daf_amud_calculator(page_num)
                if daf not in daf_to_files: daf_to_files[daf] = []
                daf_to_files[daf].append(filepath)

            for daf, paths in sorted(daf_to_files.items()):
                daf_filename = os.path.join(download_dir, f"{self.masechet_var.get()}_Daf{daf}.pdf")
                self.merge_pdfs(self, sorted(paths), daf_filename)
                files_for_final_merge.append(daf_filename)
                if not self.keep_individuals_var.get():
                    files_to_delete_later.update(paths)
        else:
            # Sort by page number (dict key) to ensure correct order
            sorted_items = sorted(downloaded_files_map.items())
            files_for_final_merge.extend([item[1] for item in sorted_items])

        if self.merge_all_var.get():
            self.status_label.config(text="Merging selection into a single PDF...")
            self.root.update_idletasks()
            if self.selection_mode_var.get() == "All":
                suffix = "All"
            elif self.selection_mode_var.get() == "Range":
                suffix = f"Range_{self.range_start_var.get()}-{self.range_end_var.get()}"
            else:
                suffix = "Individual_Selection"

            merged_filename = os.path.join(DOWNLOADS_DIR, f"{self.masechet_var.get()}_{suffix}_Full.pdf")
            self.merge_pdfs(self, files_for_final_merge, merged_filename)


    def download_from_drive(self, masechta_name, filename, save_path):
        """Searches for a file on Google Drive and downloads it.
        It first looks in a subfolder named after the masechta, then falls back to the main folder.
        """
        try:
            # Check cache for masechta folder ID
            parent_folder_id = self.masechta_folder_ids.get(masechta_name)

            if parent_folder_id is None:
                # If not cached, search for the masechta subfolder
                folder_query = f"name = '{masechta_name}' and '{DRIVE_FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                folder_results = self.drive_service.files().list(q=folder_query, corpora='allDrives', includeItemsFromAllDrives=True, supportsAllDrives=True, fields='files(id)').execute()
                folder_items = folder_results.get('files', [])

                if folder_items:
                    parent_folder_id = folder_items[0]['id']
                    self.masechta_folder_ids[masechta_name] = parent_folder_id
                else:
                    # Cache the fact that we should use the root folder
                    self.masechta_folder_ids[masechta_name] = DRIVE_FOLDER_ID
                    parent_folder_id = DRIVE_FOLDER_ID
            
            # Search for the file in the determined folder (masechta subfolder or root)
            query = f"name = '{filename}' and '{parent_folder_id}' in parents and trashed = false"
            results = self.drive_service.files().list(q=query, corpora='allDrives', includeItemsFromAllDrives=True, supportsAllDrives=True, fields='files(id)').execute()
            items = results.get('files', [])

            # If not found in subfolder, and we were searching a subfolder, try the root folder as a fallback
            if not items and parent_folder_id != DRIVE_FOLDER_ID:
                query = f"name = '{filename}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
                results = self.drive_service.files().list(q=query, corpora='allDrives', includeItemsFromAllDrives=True, supportsAllDrives=True, fields='files(id)').execute()
                items = results.get('files', [])

            if not items:
                print(f"[WARN] File not found in Drive: {filename}")
                self.status_label.configure(text=f"File not found in Drive: {filename}")
                return False

            file_id = items[0]['id']
            request = self.drive_service.files().get_media(fileId=file_id)

            with io.FileIO(save_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            return True
        except HttpError as error:
            print(f"[ERROR] An HTTP error occurred: {error}")
            self.status_label.configure(text = f"[ERROR] An HTTP error occurred: {error}")
            return False
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")
            self.status_label.configure(text = f"[ERROR] An unexpected error occurred: {e}")
            return False

    @staticmethod
    def merge_pdfs(self, pdf_files, output_filename):
        """Merges a list of PDF files into a single output file."""
        if not pdf_files: return
        merger = PdfMerger()
        for pdf_path in pdf_files:
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                try:
                    merger.append(pdf_path)
                except Exception as e:
                    print(f"[ERROR] Could not append {os.path.basename(pdf_path)}: {e}")
                    self.status_label.configure(text = f"[ERROR] Could not append {os.path.basename(pdf_path)}: {e}")
        try:
            merger.write(output_filename)
        except Exception as e:
            print(f"[ERROR] Could not write merged PDF {os.path.basename(output_filename)}: {e}")
            self.status_label.configure(text = f"[ERROR] Could not write merged PDF {os.path.basename(output_filename)}: {e}")
        finally:
            merger.close()

    @staticmethod
    def clean_up(self, files_to_delete):
        """Deletes specified temporary files."""
        for file in files_to_delete:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except OSError as e:
                print(f"[ERROR] Could not delete file {os.path.basename(file)}: {e}")
                self.status_label.configure(text = f"[ERROR] Could not delete file {os.path.basename(file)}: {e}")

    def open_output_folder(self):
        """Opens the main downloads directory."""
        folder_path = DOWNLOADS_DIR
        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def theme_auto(self, theme=None):
        sv_ttk.set_theme(darkdetect.theme()) # type: ignore

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    root = tk.Tk()
    app = MasechetDownloader(root)
    sv_ttk.set_theme("light")
    
    try:
        t = threading.Thread(target=darkdetect.listener, args=(app.theme_auto, ))
        t.daemon = True
        t.start()
        sv_ttk.set_theme(darkdetect.theme()) # type: ignore
    except: pass
    
    # Close the splash screen once the main app is initialized and ready
    try: pyi_splash.close() # type: ignore
    except: pass
    
    root.mainloop()

if __name__ == "__main__":
    
    try:
        import pyi_splash # type: ignore
        # You can optionally update the splash screen text as things load
        pyi_splash.update_text("Loading UI...")
    except ImportError:
        pyi_splash = None # Will be None when not running from a PyInstaller bundle
    except RuntimeError: pass
    
    main()
