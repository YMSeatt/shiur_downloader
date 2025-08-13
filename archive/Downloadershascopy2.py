import requests
import random
import os
import time
import sys
import platform
try:
    from PyPDF2 import PdfMerger
except ImportError:
    print("PyPDF2 not found. Please install it using: pip install PyPDF2")
    sys.exit(1) # Exit if dependency is missing
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, END # Added simpledialog for range input (alternative)
import uuid
import logging
import subprocess
import math # For ceiling function if needed

dir_folder = f"downloads"
os.makedirs(dir_folder, exist_ok=True)
#Make individual selections scrollable


class MasechetDownloader:

    # --- Static Class Data and Methods ---
    def detect_environment():
        # ... (detect_environment code remains the same) ... [source: 1-2]
        if 'google.colab' in sys.modules:
            return 'colab'
        elif os.name == 'nt':
            return 'powershell'
        else:
            return 'standard'

    env = detect_environment()

    def daf_amud_calculator(page_number):
        # ... (daf_amud_calculator code remains the same) ... [source: 2]
        daf = 2 + (page_number - 2) // 2
        amud = "ב" if page_number % 2 != 0 else "א"
        return daf, amud

    masechtos_info_static = {
        # ... (masechtos_info_static dictionary remains the same) ... [source: 2-6]
         "Brachos": [36083, 125], "Shabbos": [36104, 312], "Eiruvin": [36087, 207],
         "Psachim": [36101, 240], "Shkalim": [36105, 42], "Yuma": [36112, 173],
         "Sukkah": [36108, 110], "Beitza": [36082, 78], "Rosh Hashana": [36102, 67],
         "Tainis": [36109, 59], "Megilah": [36094, 61], "Moed Katan": [36097, 55],
         "Chagigah": [36084, 51], "Yevamos": [36111, 242], "Kesubos": [36091, 222],
         "Nedarim": [36098, 180], "Nazir": [36100, 130], "Sotah": [36107, 96],
         "Gittin": [36088, 178], "Kedushin": [3692, 162], "Bava Kamma": [36079, 236],
         "Bava Metzia": [36080, 235], "Bava Basra": [36078, 350], "Sanhedrin": [36103, 224],
         "Makkos": [36093, 46], "Shvuos": [36106, 96], "Avodah Zarah": [36077, 150],
         "Horyos": [36089, 25], "Zevachim": [36113, 238], "Menuchos": [36096, 217],
         "Chulin": [36085, 281], "Bechoros": [36081, 119], "Arachin": [36086, 65],
         "Temurah": [36110, 65], "Krisos": [36090, 54], "Meilah": [36095, 41],
         "Nidah": [36099, 143]
    }

    def check_internet_connection():
        # ... (check_internet_connection code remains the same) ... [source: 6-7]
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.exceptions.RequestException:
            return False

    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    # --- Instance Initialization (`__init__`) ---
    def __init__(self,root):
        
        self.root = tk.Tk()
        self.root.title("Masechet Downloader")
        self.root.geometry("500x800") # Increased size for new widgets
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(2, weight=1)
        #self.root.rowconfigure(0, weight=1)
        # --- Main Container and Scrollable Area Setup ---
        container = ttk.Frame(self.root,height=700)
        container.grid(sticky="NSEW",column=1)
        
        
        #centerer.grid
        

        # Using a PanedWindow might be better for resizing later, but Frame is simpler for now
        top_controls_frame = ttk.Frame(container, height=45,width=100) # Frame for non-scrolling controls if needed
        top_controls_frame.grid(sticky="NEW", padx=0,column=0,row=0, pady=5)
        top_controls_frame.grid_anchor("center")
        top_controls_frame.grid_propagate(True) # Prevent resizing based on content initially

        # Canvas for main scrolling content
        self.content_canvas = tk.Frame(container,height=400)
        self.content_canvas.grid(column=0,sticky="NSEW",row=1,rowspan=3,columnspan=4)
        self.content_canvas.grid_anchor("center")
        self.content_canvas.grid_propagate(True)
        
        #scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.content_canvas.yview)
        #scrollbar.grid(sticky=('N','S',"E"),column=5,row=1,rowspan=3)

        #self.content_canvas.configure(yscrollcommand=scrollbar.set,height=400)

        # Frame inside the canvas that holds the widgets
        #self.content_canvas = ttk.Frame(self.content_canvas)
        
        #self.content_canvas.create_window((1, 1), window=self.content_canvas, anchor="nw")

        # --- Scrolling Fix ---
        # Bind mousewheel ONLY to the canvas and the scroll_frame inside it
        def _on_mousewheel(event):
            # On Windows, delta is +/- 120. Linux uses +/- 1 (buttons 4/5). Adjust divisor/logic.
            if sys.platform == 'win32':
                scroll_delta = int(-1 * (event.delta / 120))
            elif sys.platform == 'darwin': # macOS might need different handling
                scroll_delta = int(-1 * event.delta)
            else: # Linux/other (button 4 up, 5 down) - event.num might be needed
                if event.num == 4:
                    scroll_delta = -1
                elif event.num == 5:
                    scroll_delta = 1
                else:
                    scroll_delta = 0
            print()
            print(self.content_canvas.winfo_screen())
        def _on_mousewheelindi(event):
            # On Windows, delta is +/- 120. Linux uses +/- 1 (buttons 4/5). Adjust divisor/logic.
            if sys.platform == 'win32':
                scroll_delta = int(-1 * (event.delta / 120))
            elif sys.platform == 'darwin': # macOS might need different handling
                scroll_delta = int(-1 * event.delta)
            else: # Linux/other (button 4 up, 5 down) - event.num might be needed
                if event.num == 4:
                    scroll_delta = -1
                elif event.num == 5:
                    scroll_delta = 1
                else:
                    scroll_delta = 0
            self.individual_canvas.yview_scroll(scroll_delta, "units")

        # Bind to the canvas and the frame within it
        self.content_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.content_canvas.bind("<Button-4>", _on_mousewheel) # For Linux scroll up
        self.content_canvas.bind("<Button-5>", _on_mousewheel) # For Linux scroll down
        self.content_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.content_canvas.bind("<Button-4>", _on_mousewheel)
        self.content_canvas.bind("<Button-5>", _on_mousewheel)
        # IMPORTANT: Need to also bind recursively to children widgets if they fill the frame
        # Or tell Tkinter the scroll region properly updates
        self.content_canvas.bind("<Configure>", lambda e: self.content_canvas.grid_configure(rowspan=1,sticky="nsew"))
        # --- End Scrolling Fix ---


        # --- Widgets ---
        masechtos_keys = list(MasechetDownloader.masechtos_info_static.keys())

        # Masechet Selection (moved to top_controls_frame for non-scrolling)
        masechet_label = ttk.Label(top_controls_frame, text="Masechet: ")
        masechet_label.grid(column=0,row=0, sticky="W",padx=0,pady=1)
        self.masechet_select_var = tk.StringVar()
        self.masechet_selection = ttk.Combobox(
            top_controls_frame,
            textvariable=self.masechet_select_var,
            values=masechtos_keys,
            width=20,
            state="readonly",takefocus=True
        )
        self.masechet_selection.grid(column=1,row=0,pady=1, padx=5,sticky=("W"))

        self.masechet_selection.bind("<<ComboboxSelected>>", self.update_options_for_masechet) # Combined update function

        # --- Selection Type (Daf/Amud) --- (In Scroll Frame)
        self.select_type_var = tk.StringVar(value="Dapim") # Default to Dapim
        ttk.Label(self.content_canvas, text="Select By:").grid(column=1,row=1,pady=(10, 0))#
        select_type_frame = ttk.Frame(self.content_canvas)
        select_type_frame.grid(column=1)#
        ttk.Radiobutton(select_type_frame, text="Dapim", variable=self.select_type_var, value="Dapim", command= lambda:self.update_text(caller="Selecter")).grid(column=2, padx=5,row=2,sticky="W")#left
        ttk.Radiobutton(select_type_frame, text="Amudim", variable=self.select_type_var, value="Amudim", command=lambda:self.update_text(caller="Selecter")).grid(column=1, padx=5,row=2,sticky="W")#left


        # --- Selection Mode (All/Range/Individual) --- (In Scroll Frame)
        self.selection_mode_var = tk.StringVar(value="All") # Default to All
        ttk.Label(self.content_canvas, text="Selection Mode:").grid(column=1,padx=20,pady=(10, 0),row=3)#
        mode_frame = ttk.Frame(self.content_canvas)
        mode_frame.grid(column=1)#
        ttk.Radiobutton(mode_frame, text="All", variable=self.selection_mode_var, value="All", command= lambda: self.update_text(caller="selmoder")).grid(column=1,row=4, padx=5)#left
        ttk.Radiobutton(mode_frame, text="Range", variable=self.selection_mode_var, value="Range", command= lambda: self.update_text(caller="selmoder")).grid(column=2,row=4, padx=5)#left
        ttk.Radiobutton(mode_frame, text="Individual", variable=self.selection_mode_var, value="Individual", command= lambda: self.update_text(caller="selmoder")).grid(column=3,row=4, padx=5)#left

        # --- Range Selection Widgets (Hidden initially) ---
        self.range_frame = ttk.Frame(container)
        
        # self.range_frame.pack() # Packed later when mode is "Range"
        self.range_start_var = tk.StringVar(value=2)
        self.range_end_var = tk.StringVar(value=3)
        
        ttk.Label(master=self.range_frame, text="From:").grid(column=2,row=3, padx=10,sticky="W")#left
        self.range_start_spin = ttk.Combobox(self.range_frame, textvariable=self.range_start_var, width=5)
        self.range_start_spin.grid(column=2,row=4,sticky=("N"),padx=10)#left
        self.range_start_spin.bind(self.validate_range)
        
        
        ttk.Label(self.range_frame, text="To:").grid(column=5,row=3, padx=10,sticky="W")#left
        self.range_end_spin = ttk.Combobox(self.range_frame, textvariable=self.range_end_var, width=5)
        self.range_end_spin.grid(column=5,row=4,sticky=("N"),padx=10)#left

        self.range_end_spin.bind(self.validate_range) # type: ignore


        # --- Individual Selection Widgets (Using Checkbox List Frame) ---
        self.individual_list_frame_container = ttk.Frame(container,height=230,padding=5) # Container to pack/unpack
        # self.individual_list_frame_container.pack() # Packed later
        ttk.Label(self.individual_list_frame_container, text="Select Items:").grid(column=2,row=3,sticky="e")
        ttk.Button(self.individual_list_frame_container, text="Clear Selection", command=self.clear_indi_list_sel).grid(column=3,sticky="e",row=3)

        # Inner frame for the actual list, inside a canvas for scrolling
        self.individual_canvas = tk.Listbox(self.individual_list_frame_container, height=10, width=75, borderwidth=1, relief="sunken", selectmode="multiple")
        self.individual_scrollbar = ttk.Scrollbar(self.individual_list_frame_container, orient="vertical", command=self.individual_canvas.yview)
        #self.individual_list_frame = ttk.Frame(self.individual_canvas) # Frame holding checkboxes
        
        
        self.individual_scrollbar.grid(sticky="NSW",rowspan=3,column=5)
        self.individual_canvas.grid(sticky="NW",column=1,columnspan=3,row=4 )#left
        self.individual_canvas.grid_anchor("nw")
        #self.individual_canvas.create_window((1, 2), window=self.individual_list_frame, anchor="n")

        self.individual_canvas.configure(yscrollcommand=self.individual_scrollbar.set)
        
        self.individual_canvas.bind("<MouseWheel>", _on_mousewheelindi)
        self.individual_canvas.bind("<Button-4>", _on_mousewheelindi) # For Linux scroll up
        self.individual_canvas.bind("<Button-5>", _on_mousewheelindi) # For Linux scroll down
        self.individual_scrollbar.bind("<MouseWheel>", _on_mousewheelindi)
        self.individual_scrollbar.bind("<Button-4>", _on_mousewheelindi)
        self.individual_scrollbar.bind("<Button-5>", _on_mousewheelindi)
        # IMPORTANT: Need to also bind recursively to children widgets if they fill the frame
        # Or tell Tkinter the scroll region properly updates
        #self.individual_scrollbar.bind("<Configure>", lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))

        #self.individual_list_frame.bind("<Configure>", lambda e: self.individual_canvas.configure(scrollregion=self.individual_canvas.bbox("all")))
        """# Bind mousewheel to the inner list canvas too
        #self.individual_canvas.bind("<MouseWheel>", _on_mousewheel)
        #self.individual_canvas.bind("<Button-4>", _on_mousewheel)
        #self.individual_canvas.bind("<Button-5>", _on_mousewheel)
        #self.individual_list_frame.bind("<MouseWheel>", _on_mousewheel) # Bind to frame as well
        #self.individual_list_frame.bind("<Button-4>", _on_mousewheel)
        #self.individual_list_frame.bind("<Button-5>", _on_mousewheel)
        """
        

        # Dictionary to hold the BooleanVar for each checkbox item
        self.individual_vars = {}

        # --- Merge Options --- (In Scroll Frame)
        ttk.Label(self.content_canvas, text="Merge Options:").grid(pady=(2, 0),column=1,row=5)
        self.merge_options_frame = ttk.Frame(self.content_canvas)
        self.merge_options_frame.grid(column=1,row=6, padx=20) # Align left slightly for clarity

        self.merge_into_one_pdf_var = tk.BooleanVar(value=False)
        self.merge_into_masechet = ttk.Checkbutton(
            self.merge_options_frame, text="Merge entire selection into one PDF", variable=self.merge_into_one_pdf_var, command = lambda:self.update_text(caller="merger"))
        self.merge_into_masechet.grid(column=1)
        #self.merge_into_masechet.bind("<ButtonSelected>", lambda e: self.update_merge_options)
        
        select_type = self.select_type_var.get()
        self.merge_into_dapim_var = tk.BooleanVar(value=False)
        self.merge_into_dapim_check = ttk.Checkbutton(self.merge_options_frame, text=str, variable=self.merge_into_dapim_var, command=lambda:self.update_text(caller="merger"))
        
         
        #self.merge_into_dapim_check.grid(column=1)

        mode = self.selection_mode_var.get()
        self.merge_into_dapim_check.configure(text= ("Keep Dapim PDFs") if mode == "All" and select_type == "Dapim" else print(""))
        # Disable initially if selecting Dapim
        self.keep_amudim_var = tk.BooleanVar(value=False)
        self.keep_amudim_check = ttk.Checkbutton(
            self.merge_options_frame, text="Keep individual Amud PDFs", variable=self.keep_amudim_var
        )
        #self.keep_amudim_check.grid(column=1)
        # Disable initially if selecting Dapim? Or always allow keeping if downloaded?
        # Let's enable always, logic will handle it.


        # --- Download Button --- (In Scroll Frame)
        self.download_button = ttk.Button(self.root,text="Download", command=self.start_download, state=tk.DISABLED)
        self.download_button.grid(pady=20, column=1,row=7,sticky="S")
        
        # Open output folder button
        self.open_output_folder = ttk.Button(self.root,text="Open Download Folder", command=self.open_output_folder_)
        self.open_output_folder.grid(pady=20,column=1,columnspan=3,padx=(0,5),row=7,sticky="se")
        self.open_output_folder.grid_anchor("e")


        self.range_start_amud = str(self.range_start_var)
        self.range_end_amud = str(self.range_start_var)
        print(self.root.grid_size())
        # Initial state setup
        self.toggle_selection_widgets() # Hide/show appropriate widgets


    # --- GUI Update and Validation Methods ---

    def update_options_for_masechet(self, event=None):
        """Updates range limits and individual list when masechet changes."""
        selected_masechet = self.masechet_select_var.get()
        if not selected_masechet:
            self.download_button.configure(state=tk.DISABLED)
            return

        _, total_pages = MasechetDownloader.masechtos_info_static[selected_masechet]
        self.max_daf = total_pages / 2
        self.total_pages = total_pages
        self.max_daflist = []
        self.max_daflist.clear
        if ".5" not in str(total_pages/2):
            extra_page = False
            print("Not extra")
        else:
            print("Extra")
            extra_page = True
        
        
        if self.select_type_var.get() != "Dapim":
            #self.range_start_spin.grid(sticky=("W","S","E","N"),column=1,row=5)#left
            for i in range(2,(self.total_pages)+1):
                g=f"{i}a"
                self.max_daflist.append(g)
                i+=1
                g=f"{i}b"
                self.max_daflist.append(g)
                i+=1
            # Update Range Spinboxes
            self.range_start_spin.config(values=self.max_daflist)
            self.range_end_spin.config(values=self.max_daflist)
            # Clamp current values if they exceed new max
            if float(self.range_start_var.get()) > self.max_daf: self.range_start_var.set(self.max_daf)
            if float(self.range_end_var.get()) > self.max_daf: self.range_end_var.set(self.max_daf)
            if float(self.range_start_var.get()) < 2: self.range_start_var.set("2a")
            if float(self.range_end_var.get()) < 2: self.range_end_var.set("2b")
            if float(self.range_start_var.get()) == 2: self.range_start_var.set("2a")
            if float(self.range_end_var.get()) == 2: self.range_end_var.set("2b")
        else:
            print("RangeEditing")
            if extra_page:
                print("Extra Range2")
                for i in range(2,int(self.max_daf+2)+1):
                    print(i)
                    self.max_daflist.append(i)
            else:
                print("ExtraRange1")
                for i in range(2,int(self.max_daf+2)):
                    self.max_daflist.append(i)
                
                
            # Update Range Spinboxes
            self.range_start_spin.config(values=self.max_daflist)
            self.range_end_spin.config(values=self.max_daflist)
            # Clamp current values if they exceed new max
            if float(self.range_start_var.get()) > self.max_daf: self.range_start_var.set(self.max_daf)
            if float(self.range_end_var.get()) > self.max_daf: self.range_end_var.set(self.max_daf)
            if float(self.range_start_var.get()) < 2: self.range_start_var.set(2)
            if float(self.range_end_var.get()) < 2: self.range_end_var.set(2)
            self.validate_range()

        # Update Individual List (calls populate)
        self.update_individual_list()

        # Enable download button
        self.download_button.configure(state=tk.NORMAL)

    
    
        
    def update_text (self,caller=None, event=None):
        select_type = self.select_type_var.get()
        mode = self.selection_mode_var.get()
        #print(mode)
        # Pack (show) the relevant widget
        if self.merge_into_one_pdf_var.get() == True:
            print("HH")
            self.merge_into_dapim_check.grid(column=1,row=2)
            if self.merge_into_dapim_var.get() == True:
                self.keep_amudim_check.grid(column=1,row=3)
            else:
                self.keep_amudim_check.grid_remove()
        else:
            self.keep_amudim_check.grid_remove()
            self.merge_into_dapim_check.grid_remove()

        if mode == "Range":
            if select_type == "Dapim": self.merge_into_dapim_check.configure(text="Keep the Dapim PDF's")
            elif select_type == "Amudim":self.merge_into_dapim_check.configure(text="Merge Amudim into Dapim PDF's")
        elif mode == "Individual":
            if select_type == "Dapim": self.merge_into_dapim_check.configure(text="Keep the Dapim PDF's")
            elif select_type == "Amudim": self.merge_into_dapim_check.configure(text="      Merge into Dapim PDFs\n   (Under Construction, so it may\n        not work as expected)")
        elif mode == "All":
            if select_type == "Dapim": self.merge_into_dapim_check.configure(text="Keep the Dapim PDFs")
            elif select_type == "Amudim": self.merge_into_dapim_check.configure(text="Merge Amudim into Dapim PDFs")
        if caller == "Selecter":
            self.update_individual_list()
        elif caller == "selmoder":
            self.toggle_selection_widgets()

    def update_individual_list(self):
        """Clears and populates the individual checkbox list."""
        selected_masechet = self.masechet_select_var.get()
        select_type = self.select_type_var.get()

        # Clear existing checkboxes and vars
        #for widget in self.individual_list_frame.winfo_children():
        #    widget.destroy()
        self.individual_vars.clear()

        if not selected_masechet:
            return # Nothing to populate

        # Update Merge Amudim into Dapim checkbox state
        
        if select_type == "Dapim":
            print("Dapim") # Cannot merge amudim if selecting dapim

        selected_masechet = self.masechet_select_var.get()
        if not selected_masechet:
            self.download_button.configure(state=tk.DISABLED)
            return

        _, total_pages = MasechetDownloader.masechtos_info_static[selected_masechet]
        self.max_daf = (total_pages / 2)
        """if ".5" in self.max_daf:
            self.max_daf.replace(".5","a")"""
        self.total_pages = total_pages
        self.max_daflist = []
        self.max_daflist.clear
        self.max_daflistam = []
        self.max_daflistam.clear
        mode = self.selection_mode_var.get()
        
        #See if there is an extra Amud or not
        if ".5" not in str(total_pages/2):
            extra_page = False
            print("Not extra")
        else:
            print("Extra")
            extra_page = True
            
        if self.select_type_var.get() != "Dapim" and mode == "Range":
            
            print("in range amudim")
            if extra_page:
                for i in range(2, (self.total_pages//2) + 2):
                    g = f"{i}a"
                    g2 = f"{i}b"
                    self.max_daflistam.append(g)
                    self.max_daflistam.append(g2)
                g3 = f"{self.total_pages//2+2}a"
                self.max_daflistam.append(g3)
            else:
                for i in range(2, (self.total_pages//2) + 2):
                    g = f"{i}a"
                    g2 = f"{i}b"
                    self.max_daflistam.append(g)
                    self.max_daflistam.append(g2)
                                    
            # Update Range Spinboxes
            self.range_start_spin.config(values=self.max_daflistam)
            self.range_end_spin.config(values=self.max_daflistam)
            """if "a" or "b" in self.range_end_var.get() and self.range_start_var.get():
                self.range_end_var.replace("a",".3")
                self.range_end_var.replace("b","7.5")
                self.range_end_var.replace("a","3")
                self.range_end_var.replace("b","7.5")"""

            # Clamp current values if they exceed new max
            #self.range_start_amud = str(self.range_start_var)
            #self.range_end_amud = str(self.range_start_var)
            
            if "a" or "b" in self.range_start_amud and self.range_end_var:
                self.range_start_amud.replace("a", ".35")
                self.range_end_amud.replace("b",".75")
            else:
                self.range_start_amud.__add__(".35")
                self.range_end_amud.__add__(".75")
                self.range_end_var.__add__("a", "b")
                self.range_start_var.__add__("a", "b")
            
            print(self.range_end_amud)
            print(self.range_start_amud)
            if self.range_start_amud and self.range_end_amud == "PY_VAR3": 
                self.range_start_amud = "2.35"
                self.range_end_amud = "2.75"
            if float(self.range_start_amud) >= self.max_daf: self.range_start_var.set(f"{self.max_daf}b")
            if float(self.range_end_amud) >= self.max_daf: self.range_end_var.set(f"{self.max_daf}b")
            if float(self.range_start_amud) <= 2.35: self.range_start_var.set("2a")
            if float(self.range_end_amud) <= 2.35: self.range_end_var.set("2b")
            if float(self.range_start_amud) == 2.35: self.range_start_var.set("2a")
            if float(self.range_end_amud) == 2.75: self.range_end_var.set("2b")
            
        else:
            if extra_page:
                print("Extra2")
                for i in range(2, int(self.max_daf + 2)+1):
                    self.max_daflist.append(i)
            else:
                print("Extra4")
                for i in range(2, int(self.max_daf + 2)):
                    self.max_daflist.append(i)
            
            # Update Range Spinboxes
            self.range_start_spin.config(values=self.max_daflist)
            self.range_end_spin.config(values=self.max_daflist)
        
            print(self.range_start_amud)
            print(self.range_end_amud)
            
            self.range_start_amud.removesuffix("a")
            self.range_start_amud.removesuffix("b")
            self.range_end_amud.removesuffix("a")
            self.range_end_amud.removesuffix("b")
            
            print(self.range_start_amud,"after removal(i hope)")
            print(self.range_end_amud)
            
            if self.range_start_amud and self.range_end_amud == "PY_VAR3":
                self.range_start_amud = "2"
                self.range_end_amud = "3"
            self.range_start_var.set(self.range_start_amud)
            self.range_end_var.set(self.range_end_amud)
            
            # Clamp current values if they exceed new max
            if float(self.range_start_var.get()) > self.max_daf: self.range_start_var.set(self.max_daf)
            if float(self.range_end_var.get()) > self.max_daf: self.range_end_var.set(self.max_daf)
            if float(self.range_start_var.get()) < 2: self.range_start_var.set(2)
            if float(self.range_end_var.get()) < 2: self.range_end_var.set(3)
            self.validate_range()

        # Update Individual List (calls populate)
        if ".5" not in str(total_pages/2):
            extra_page = False
            print("Not extra")
        else:
            print("Extra")
            extra_page = True
        # Populate based on Dapim or Amudim
        if select_type == "Dapim":
            if extra_page:
                items = range(2, int(self.max_daf + 3))
            else:
                items = range(2, int(self.max_daf + 2))
            #items = range(2, int(self.max_daf + 3))
            item_prefix = "Daf "
        else: # Amudim
            items = []
            for page in range(2, self.total_pages + 2): # Hebrewbooks pages seem to start from 2 usually
                daf, amud = MasechetDownloader.daf_amud_calculator(page)
                items.append(f"Daf {daf} Amud {amud}")

        item_label_func = lambda item: f"{item_prefix}{item}" if select_type == "Dapim" else str(item)
        
        self.individual_canvas.delete(0,END)
        
        for item in items:
            var = tk.BooleanVar(value=False)
            #label = item_label_func(item)
            #cb = ttk.Checkbutton(self.individual_list_frame, text=label, variable=var)
            #cb.grid(sticky="w", padx=5)
            
            self.individual_canvas.insert(END, item_label_func(item))
            
            self.individual_vars[item] = var # Store var, key is the item (e.g., 3 for Daf 3, or "Daf 3 Amud א" for amud)
        
        # Update scroll region after adding widgets
        #self.individual_list_frame.update_idletasks()
        #self.individual_canvas.configure(scrollregion=self.individual_canvas)
        self.individual_canvas.yview_moveto(0) # Scroll back to top

    def clear_indi_list_sel (self, event=None):
        self.individual_canvas.selection_clear(0,END)

    def toggle_selection_widgets(self):
        """Shows/hides Range or Individual selection widgets based on mode."""
        mode = self.selection_mode_var.get()
        select_type = self.select_type_var.get()
        # Forget (hide) all conditional widgets first
        self.range_frame.grid_forget()
        self.individual_list_frame_container.grid_forget()

        # Pack (show) the relevant widget
        if mode == "Range":
            self.range_frame.grid(pady=5, column=0,row=2,columnspan=3,sticky=("N","E","W"))
            self.range_frame.grid_anchor("center")
            self.range_frame.grid_propagate(True)
            #self.range_frame.grid_anchor("nw")
            print(self.range_frame.grid_slaves)
            print("Got to Range")
            if select_type == "Dapim":
                self.merge_into_dapim_check.configure(text="Keep the Dapim PDF's")
            elif select_type == "Amudim":
                self.merge_into_dapim_check.configure(text="Merge Amudim into Dapim PDF's")
        elif mode == "Individual":
            self.individual_list_frame_container.grid(column=0,row=3,pady=5, sticky="NEW", padx=10)
            self.individual_list_frame_container.grid_anchor("nw")
            self.update_individual_list() # Ensure list is populated correctly
        elif mode == "All":
            pass
            
        self.update_options_for_masechet

    def open_output_folder_ (self, event=None):
        folder_path = dir_folder
        try:
            if not os.path.exists(folder_path):
                if messagebox.askyesno("Create Folder?", f"The output folder '{folder_path}' does not exist. Create it?"):
                    os.makedirs(folder_path)
            if platform.system() == "Windows": os.startfile(folder_path)
            elif platform.system() == "Darwin": subprocess.Popen(["open", folder_path])
            else: subprocess.Popen(["xdg-open", folder_path])
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open output folder:\n{e}")

    def validate_range(self):
        """Ensures start range is not greater than end range."""
        start = self.range_start_var.get()
        end = self.range_end_var.get()
        if start > end:
            self.range_end_var.set(start) # Or set start to end, depending on desired behavior
            # Optionally provide user feedback


    # --- Download Logic --- (Modified `start_download`)
    def start_download(self):
        masechta_name = self.masechet_select_var.get()
        if not masechta_name:
            messagebox.showwarning("Selection Missing", "Please select a Masechet.")
            return

        selection_mode = self.selection_mode_var.get()
        select_type = self.select_type_var.get() # "Dapim" or "Amudim"

        # --- Determine Pages to Download ---
        pages_to_download = set()# Use a set to avoid duplicates

        masechta_id, total_pages = MasechetDownloader.masechtos_info_static[masechta_name]
        
        max_daf = total_pages // 2
        
        if ".5" not in str(total_pages/2):
            extra_page = False
            print("Not extra")
        else:
            print("Extra")
            extra_page = True
            
            
        base_url = f"https://beta.hebrewbooks.org/pagefeed/hebrewbooks_org_{masechta_id}_{{page_number}}.pdf"
        download_dir = f"downloads/{masechta_name}"
        os.makedirs(download_dir, exist_ok=True)

        print(f"\n--- Starting Download for {masechta_name} ---")
        print(f"Selection Mode: {selection_mode}, Select By: {select_type}")


        if selection_mode == "All":
            if select_type == "Dapim":
                # All pages for all dapim (2 to max_daf)
                for daf in range(1, max_daf + 2):
                    pages_to_download.add(2 * (daf - 2) + 1) # Amud Aleph page
                    pages_to_download.add(2 * (daf - 2) + 2) # Amud Bet page
                if extra_page:
                    pages_to_download.add(total_pages)
                    print(total_pages)
                print("Selected: All Dapim")
            else: # All Amudim
                pages_to_download.update(range(1, total_pages + 1))
                print("Selected: All Amudim")

        elif selection_mode == "Range":
            
            if select_type == "Dapim":
                start_daf = int(self.range_start_var.get())
                end_daf = int(self.range_end_var.get())
                if start_daf > end_daf:
                    print(start_daf,end_daf)
                    messagebox.showerror("Invalid Range", "Start daf cannot be greater than end daf.")
                    return
            else:
                start_daf = self.range_start_var.get()
                end_daf = self.range_end_var.get()
                
            
            print(start_daf,end_daf)
            

            if select_type == "Dapim":
                # Pages for all dapim in the range
                for daf in range(start_daf - 1, end_daf):
                    pages_to_download.add(2 * (daf - 1) + 1) # Amud Aleph page
                    pages_to_download.add(2 * (daf - 1) + 2) # Amud Bet page
                print(f"Selected: Dapim Range {start_daf}-{end_daf}")
            else: # Amudim within the daf range
                
                if "a" in start_daf: 
                    start_daf = start_daf.replace("a",".5") 
                    start_daf = (float(start_daf))
                elif "b" in start_daf: 
                    start_daf = int(start_daf.replace("b",""))
                
                if "a" in end_daf: 
                    end_daf = end_daf.replace("a",".5") 
                    end_daf=(float(end_daf))
                elif "b" in end_daf: 
                    end_daf = int(end_daf.replace("b",""))

                if ".5" in str(start_daf) and ".5" in str(end_daf):
                    
                    start_daf_p = int(start_daf + .5)
                    end_daf_p = int(end_daf - .5)
                    print(start_daf_p,end_daf_p,"Ps")
                    for daf in range(start_daf_p,end_daf_p):
                        print("daf",daf)
                        pages_to_download.add(2 * (daf - 2) + 1) # Amud Aleph page
                        print({(2 * (daf - 2) + 1)},"a",daf)
                        print("daf2",daf)
                        pages_to_download.add(2 * (daf - 2) + 2) # Amud Bet page
                        print((2 * (daf - 2) + 2),"b",daf)
                        
                    pages_to_download.add(float(start_daf-2)*2)
                    print("start daf",start_daf)
                    print(float(start_daf-2)*2)
                    
                    pages_to_download.add((float(start_daf-2)*2)+1)
                    print("one after start daf:",(float(start_daf-2)*2)+1)
                    
                    print("end daf",end_daf)
                    pages_to_download.add(2 * float(end_daf-2))
                    print(2 * float(end_daf-2))
                    print(f"Amudim in {start_daf}, {start_daf_p} {end_daf}, {end_daf_p}")
                    print("this is the pages to download: ",pages_to_download)
                else:
            
                    for daf in range(start_daf, end_daf + 1):
                        pages_to_download.add(2 * (daf - 1) + 1) # Amud Aleph page
                        pages_to_download.add(2 * (daf - 1) + 2) # Amud Bet page
                    print(f"Selected: Amudim in Dapim Range {start_daf}-{end_daf}")
                    print("this is the pages to download: ",pages_to_download)
                # Note: Selecting amudim by range is the same as selecting dapim by range in terms of pages

        elif selection_mode == "Individual":
            values = self.individual_canvas.selection_get()
            values = values.replace("Daf ", "", -1) if select_type == "Dapim" else values
            values = list(values.split("\n"))
            try:
                values.remove("\n")
            except ValueError: pass
            
            print(values)
            selected_items = list(values) #[item for item, var in self.individual_vars.items() if var.get()]
            if not selected_items:
                messagebox.showwarning("Selection Missing", "Please select at least one.")
                return

            if select_type == "Dapim":
                # Get pages for selected dapim
                if extra_page:
                    
                    for daf in selected_items: # item is the daf number
                        print("Not Removing")
                        #print(daf)
                        pages_to_download.add(2 * (int(daf) - 2) + 1)
                        pages_to_download.add(2 * (int(daf) - 2) + 2)
                        
                    print(selected_items)
                    if selected_items.__contains__(total_pages//2 + 2):
                        print("Removing Extra")
                        pages_to_download.remove(total_pages+1)
                        
                else:
                    for daf in selected_items: # item is the daf number
                        pages_to_download.add(2 * (int(daf) - 2) + 1)
                        pages_to_download.add(2 * (int(daf) - 2) + 2)
                print(f"Selected Individual Dapim: {selected_items}")
            else: # Amudim
                    # Get pages for selected amudim
                    # item is "Daf X Amud Y" string
                    for item_str in selected_items:
                        parts = item_str.split() # ["Daf", "X", "Amud", "Y"]
                        daf = int(parts[1])
                        amud_char = parts[3]
                        if amud_char == "א":
                            pages_to_download.add(2 * (daf - 2) + 1)
                        else: # "ב"
                            pages_to_download.add(2 * (daf - 2) + 2)
                    print(f"Selected Individual Amudim: {selected_items}")
        print("this is the pages to download: ",pages_to_download)
        # --- Filter out pages beyond total_pages ---
        valid_pages = {p for p in pages_to_download if 1 <= p <= total_pages+1}
        if not valid_pages:
            messagebox.showinfo("No Pages", "No valid pages selected or found for this Masechet.")
            return

        print(f"Will download {len(valid_pages)} pages.")

        # --- Get Merge Options ---
        merge_all_selection = self.merge_into_one_pdf_var.get()
        merge_amudim_into_dapim = self.merge_into_dapim_var.get() # Only possible if selecting amudim
        keep_individual_amudim = self.keep_amudim_var.get()

        print(f"Merge All: {merge_all_selection}, Merge Dapim: {merge_amudim_into_dapim}, Keep Amudim: {keep_individual_amudim}")

        # --- Progress Bar ---
        progress_bar = ttk.Progressbar(self.content_canvas, orient='horizontal', length=300, mode='determinate')
        progress_bar.grid(pady=10, column=1,row=4)
        progress_bar['maximum'] = len(valid_pages)
        progress_counter = 0


        # --- Download Loop ---
        downloaded_amud_files = {} # Store {page_num: filepath}
        files_to_delete_later = set()
        download_failed = False

        for page_num in (sorted(list(valid_pages))): # Download in order
            daf, amud = MasechetDownloader.daf_amud_calculator(page_num+1)
            
            filename = os.path.join(download_dir, f"{masechta_name}_Daf{daf}_Amud{amud}.pdf")
            downloaded_amud_files[page_num] = filename

            if not os.path.exists(filename):
                print(f"[INFO] Downloading Page {page_num} (Daf {daf} Amud {amud})...")
                url = base_url.format(page_number=int(page_num))
                print(url)
                if not MasechetDownloader.download_page(url, filename):
                    download_failed = True
                    break # Stop download process on failure
            else:
                print(f"[INFO] File already exists: {os.path.basename(filename)}")

            progress_counter += 1
            progress_bar['value'] = progress_counter
            self.root.update_idletasks()

        progress_bar.destroy() # Remove progress bar

        if download_failed:
             messagebox.showerror("Download Failed", "Download stopped due to an error. Check logs.")
             return

        # --- Merging Logic ---
        files_for_final_merge = [] # List of PDFs to merge for the single file output

        # 1. Merge Amudim into Dapim if requested
        if merge_amudim_into_dapim:
            print("[INFO] Merging Amudim into Dapim...")
            # Group downloaded files by daf
            daf_files = {} # {daf_num: [amud_aleph_path, amud_bet_path]}
            for page_num, filepath in downloaded_amud_files.items():
                daf, amud = MasechetDownloader.daf_amud_calculator(page_num)
                if daf not in daf_files: daf_files[daf] = []
                print(daf,filepath)
                daf_files[daf].append(filepath)

            for daf, amud_filepaths in daf_files.items():
                if len(amud_filepaths) > 0: # Should always be 1 or 2 if downloaded
                    daf_filename = os.path.join(download_dir, f"{masechta_name}_Daf{daf+1}.pdf")
                    MasechetDownloader.merge_pdfs(amud_filepaths, daf_filename)
                    files_for_final_merge.append(daf_filename) # Use the merged daf PDF for the final merge
                    if not keep_individual_amudim:
                        files_to_delete_later.update(amud_filepaths) # Mark original amudim for deletion
        else:
            # If not merging into dapim, use the individual amud files for the final merge
            files_for_final_merge.extend(downloaded_amud_files.values())


        # 2. Merge all selected items into one PDF if requested
        if merge_all_selection:
             print("[INFO] Merging selection into single PDF...")
             # Use the list determined above (either daf PDFs or amud PDFs)
             if files_for_final_merge:
                 # Determine a suitable name based on selection
                 if selection_mode == "All": name_suffix = "All"
                 elif selection_mode == "Range": name_suffix = f"Range{self.range_start_var.get()}-{self.range_end_var.get()}"
                 else: name_suffix = "Selection"
                 merged_filename = os.path.join(download_dir, f"{masechta_name}_{name_suffix}_Full.pdf")
                 MasechetDownloader.merge_pdfs(files_for_final_merge, merged_filename)

                 # Decide if intermediate daf files should be deleted
                 if merge_amudim_into_dapim and not keep_individual_amudim:
                      # If we merged amudim->dapim->full, and we don't keep amudim,
                      # should we keep the intermediate daf pdfs? Let's assume yes unless explicitly told otherwise.
                      # If the user ALSO doesn't want the daf pdfs, logic needs extension.
                      pass
             else:
                 print("[WARN] No files available for final merge.")

        # --- Cleanup ---
        if not keep_individual_amudim:
             # Delete files marked earlier (usually original amudim if they were merged)
             MasechetDownloader.clean_up(list(files_to_delete_later))
        else:
             print("[INFO] Keeping individual Amud PDFs as requested.")


        messagebox.showinfo("Download Complete", f"Process finished for {masechta_name}.\nFiles are in: {download_dir}")
        print(f"--- Download Finished for {masechta_name} ---")



    # --- Static Download/Merge/Cleanup Helpers --- (Remain mostly the same)
    @staticmethod
    def download_page(url, filename):
        # ... (download_page code remains largely the same) ... [source: 21-24]
        max_retries = 5
        retry_delay = 1
        if not MasechetDownloader.check_internet_connection():
        #    print("[ERROR] No internet connection detected.")
        #    messagebox.showerror("Network Error", "No internet connection detected.")
            return True

        for attempt in range(max_retries):
            try:
                response = MasechetDownloader.session.get(url, stream=True, timeout=15)
                response.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"[INFO] Successfully downloaded {os.path.basename(filename)}")
                return True
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Failed to download {url} (Attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay * (attempt + 1))

        print(f"[ERROR] Failed to download {url} after {max_retries} attempts.")
        messagebox.showerror("Download Error", f"Failed to download a page:\n{os.path.basename(url)}\nPlease check logs and connection.")
        return False


    @staticmethod
    def merge_pdfs(pdf_files, output_filename):
        # ... (merge_pdfs code remains largely the same) ... [source: 24-25]
        if not pdf_files:
            print(f"[WARN] No PDF files provided to merge into {output_filename}.")
            return
        merger = PdfMerger()
        print(f"[INFO] Merging {len(pdf_files)} files into {os.path.basename(output_filename)}...")
        valid_files_count = 0
        processed_files = [] # Handle potential duplicates in input list
        for pdf in pdf_files:
             if pdf in processed_files: continue # Skip duplicates
             processed_files.append(pdf)
             if os.path.exists(pdf) and os.path.getsize(pdf) > 0:
                try:
                    merger.append(pdf)
                    valid_files_count += 1
                except Exception as e:
                    print(f"[ERROR] Failed to append {os.path.basename(pdf)} to merge list: {e}")
             else:
                 print(f"[WARN] Skipping missing or empty file: {os.path.basename(pdf)}")
        print(processed_files)
        if valid_files_count > 0:
            try:
                merger.write(output_filename)
                print(f"[INFO] Successfully merged into {os.path.basename(output_filename)}")
            except Exception as e:
                 print(f"[ERROR] Failed to write merged PDF {os.path.basename(output_filename)}: {e}")
                 messagebox.showerror("Merge Error", f"Failed to create merged PDF:\n{os.path.basename(output_filename)}")
            finally:
                 merger.close()
        else:
             print(f"[ERROR] No valid PDF files were available to merge into {os.path.basename(output_filename)}.")
             messagebox.showwarning("Merge Error", f"Could not create:\n{os.path.basename(output_filename)}\nNo valid source files found.")


    @staticmethod
    def clean_up(files_to_delete):
        # ... (clean_up code remains the same) ... [source: 25]
        print(f"[INFO] Cleaning up {len(files_to_delete)} temporary files...")
        deleted_count = 0
        for file in files_to_delete:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    deleted_count += 1
            except OSError as e:
                print(f"[ERROR] Failed to delete file {os.path.basename(file)}: {e}")
        if deleted_count > 0: print(f"[INFO] Deleted {deleted_count} files.")


    def run(self):
        
        self.root.mainloop()


# --- Main Execution ---
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if not MasechetDownloader.check_internet_connection():
        # ... (internet check remains the same) ...
        print("[ERROR] No internet connection detected.")
        #root_check = tk.Tk()
        #root_check.withdraw()
        #messagebox.showerror("Network Error", "No internet connection detected. Cannot download until there is internet.")
        #root_check.destroy()
        #return

    print(f"Detected environment: {MasechetDownloader.env}")
    app = MasechetDownloader(root=tk)
    app.run()

if __name__ == "__main__":
    main()