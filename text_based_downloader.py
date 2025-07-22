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
import uuid
import logging
import subprocess
import math # For ceiling function if needed

dir_folder = f"downloads"
os.makedirs(dir_folder, exist_ok=True)

class MasechetDownloader:

    # --- Static Class Data and Methods ---
    def detect_environment():
        if 'google.colab' in sys.modules:
            return 'colab'
        elif os.name == 'nt':
            return 'powershell'
        else:
            return 'standard'

    env = detect_environment()

    def daf_amud_calculator(page_number):
        daf = 2 + (page_number - 2) // 2
        amud = "b" if page_number % 2 != 0 else "a"
        return daf, amud

    masechtos_info_static = {
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
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.exceptions.RequestException:
            return False

    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    def __init__(self):
        self.masechta_name = None
        self.selection_mode = None
        self.select_type = None
        self.range_start = None
        self.range_end = None
        self.individual_selections = []
        self.merge_all_selection = False
        self.merge_amudim_into_dapim = False
        self.keep_individual_amudim = False

    def get_user_input(self):
        """Gets all the required information from the user."""
        # 1. Select Masechet
        masechtos = list(self.masechtos_info_static.keys())
        print("Please select a Masechet:")
        for i, m in enumerate(masechtos):
            print(f"  {i+1}. {m}")
        while True:
            try:
                choice = int(input(f"Enter a number (1-{len(masechtos)}): "))
                if 1 <= choice <= len(masechtos):
                    self.masechta_name = masechtos[choice-1]
                    break
                else:
                    print("Invalid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # 2. Select by Dapim or Amudim
        print("\nSelect by:")
        print("  1. Dapim")
        print("  2. Amudim")
        while True:
            try:
                choice = int(input("Enter a number (1-2): "))
                if choice == 1:
                    self.select_type = "Dapim"
                    break
                elif choice == 2:
                    self.select_type = "Amudim"
                    break
                else:
                    print("Invalid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # 3. Selection Mode
        print("\nSelection Mode:")
        print("  1. All")
        print("  2. Range")
        print("  3. Individual")
        while True:
            try:
                choice = int(input("Enter a number (1-3): "))
                if choice == 1:
                    self.selection_mode = "All"
                    break
                elif choice == 2:
                    self.selection_mode = "Range"
                    break
                elif choice == 3:
                    self.selection_mode = "Individual"
                    break
                else:
                    print("Invalid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # 4. Range or Individual specifics
        _, total_pages = self.masechtos_info_static[self.masechta_name]
        max_daf = total_pages // 2

        if self.selection_mode == "Range":
            if self.select_type == "Dapim":
                while True:
                    try:
                        self.range_start = int(input(f"Enter start daf (2-{max_daf}): "))
                        self.range_end = int(input(f"Enter end daf (2-{max_daf}): "))
                        if 2 <= self.range_start <= max_daf and 2 <= self.range_end <= max_daf and self.range_start <= self.range_end:
                            break
                        else:
                            print("Invalid range.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
            else: # Amudim
                while True:
                    try:
                        start_str = input(f"Enter start amud (e.g., 2a, 2b, 3a...): ")
                        end_str = input(f"Enter end amud (e.g., 2a, 2b, 3a...): ")
                        # Basic validation, more can be added
                        self.range_start = start_str
                        self.range_end = end_str
                        break
                    except ValueError:
                        print("Invalid input.")

        elif self.selection_mode == "Individual":
            if self.select_type == "Dapim":
                print(f"Enter dafim numbers (2-{max_daf}), separated by commas:")
                while True:
                    try:
                        selections = input("> ")
                        self.individual_selections = [int(s.strip()) for s in selections.split(',')]
                        break
                    except ValueError:
                        print("Invalid input. Please enter numbers separated by commas.")
            else: # Amudim
                print(f"Enter amudim (e.g., 2a, 2b, 3a), separated by commas:")
                while True:
                    try:
                        selections = input("> ")
                        self.individual_selections = [s.strip() for s in selections.split(',')]
                        break
                    except ValueError:
                        print("Invalid input.")

        # 5. Merge options
        self.merge_all_selection = input("\nMerge entire selection into one PDF? (y/n): ").lower() == 'y'
        if self.select_type == "Amudim":
            self.merge_amudim_into_dapim = input("Merge amudim into dapim PDFs? (y/n): ").lower() == 'y'
            if not self.merge_amudim_into_dapim:
                self.keep_individual_amudim = input("Keep individual amud PDFs? (y/n): ").lower() == 'y'


    # --- Download Logic ---
    def start_download(self):
        masechta_name = self.masechta_name
        selection_mode = self.selection_mode
        select_type = self.select_type

        pages_to_download = set()

        masechta_id, total_pages = self.masechtos_info_static[masechta_name]

        max_daf = total_pages // 2

        if ".5" not in str(total_pages/2):
            extra_page = False
        else:
            extra_page = True

        base_url = f"https://beta.hebrewbooks.org/pagefeed/hebrewbooks_org_{masechta_id}_{{page_number}}.pdf"
        download_dir = f"downloads/{masechta_name}"
        os.makedirs(download_dir, exist_ok=True)

        print(f"\n--- Starting Download for {masechta_name} ---")
        print(f"Selection Mode: {selection_mode}, Select By: {select_type}")


        if selection_mode == "All":
            if select_type == "Dapim":
                for daf in range(1, max_daf + 2):
                    pages_to_download.add(2 * (daf - 2) + 1)
                    pages_to_download.add(2 * (daf - 2) + 2)
                if extra_page:
                    pages_to_download.add(total_pages)
            else:
                pages_to_download.update(range(1, total_pages + 1))

        elif selection_mode == "Range":
            if select_type == "Dapim":
                start_daf = self.range_start
                end_daf = self.range_end
                for daf in range(start_daf - 1, end_daf):
                    pages_to_download.add(2 * (daf - 1) + 1)
                    pages_to_download.add(2 * (daf - 1) + 2)
            else:
                start_str = self.range_start
                end_str = self.range_end

                start_daf = int(start_str[:-1])
                start_amud = start_str[-1]
                end_daf = int(end_str[:-1])
                end_amud = end_str[-1]

                for daf in range(start_daf, end_daf + 1):
                    if daf == start_daf and start_amud == 'b':
                        pages_to_download.add(2 * (daf - 2) + 2)
                    elif daf == end_daf and end_amud == 'a':
                        pages_to_download.add(2 * (daf - 2) + 1)
                    else:
                        pages_to_download.add(2 * (daf - 2) + 1)
                        pages_to_download.add(2 * (daf - 2) + 2)

        elif selection_mode == "Individual":
            if select_type == "Dapim":
                for daf in self.individual_selections:
                    pages_to_download.add(2 * (int(daf) - 2) + 1)
                    pages_to_download.add(2 * (int(daf) - 2) + 2)
            else:
                for item_str in self.individual_selections:
                    daf = int(item_str[:-1])
                    amud_char = item_str[-1]
                    if amud_char == "a":
                        pages_to_download.add(2 * (daf - 2) + 1)
                    else:
                        pages_to_download.add(2 * (daf - 2) + 2)

        valid_pages = {p for p in pages_to_download if 1 <= p <= total_pages+1}
        if not valid_pages:
            print("No valid pages selected or found for this Masechet.")
            return

        print(f"Will download {len(valid_pages)} pages.")

        merge_all_selection = self.merge_all_selection
        merge_amudim_into_dapim = self.merge_amudim_into_dapim
        keep_individual_amudim = self.keep_individual_amudim

        downloaded_amud_files = {}
        files_to_delete_later = set()
        download_failed = False

        for i, page_num in enumerate(sorted(list(valid_pages))):
            daf, amud = MasechetDownloader.daf_amud_calculator(page_num+1)

            filename = os.path.join(download_dir, f"{masechta_name}_Daf{daf}_Amud{amud}.pdf")
            downloaded_amud_files[page_num] = filename

            if not os.path.exists(filename):
                print(f"[INFO] Downloading Page {page_num} (Daf {daf} Amud {amud})...")
                url = base_url.format(page_number=int(page_num))
                if not MasechetDownloader.download_page(url, filename):
                    download_failed = True
                    break
            else:
                print(f"[INFO] File already exists: {os.path.basename(filename)}")

            # Progress bar
            progress = (i + 1) / len(valid_pages)
            bar_length = 40
            block = int(round(bar_length * progress))
            text = f"\rProgress: [{'#' * block + '-' * (bar_length - block)}] {int(progress * 100)}%"
            sys.stdout.write(text)
            sys.stdout.flush()

        if download_failed:
             print("\nDownload Failed. Check logs.")
             return

        files_for_final_merge = []

        if merge_amudim_into_dapim:
            print("\n[INFO] Merging Amudim into Dapim...")
            daf_files = {}
            for page_num, filepath in downloaded_amud_files.items():
                daf, amud = self.daf_amud_calculator(page_num)
                if daf not in daf_files: daf_files[daf] = []
                daf_files[daf].append(filepath)

            for daf, amud_filepaths in daf_files.items():
                if len(amud_filepaths) > 0:
                    daf_filename = os.path.join(download_dir, f"{masechta_name}_Daf{daf+1}.pdf")
                    self.merge_pdfs(amud_filepaths, daf_filename)
                    files_for_final_merge.append(daf_filename)
                    if not keep_individual_amudim:
                        files_to_delete_later.update(amud_filepaths)
        else:
            files_for_final_merge.extend(downloaded_amud_files.values())

        if merge_all_selection:
             print("\n[INFO] Merging selection into single PDF...")
             if files_for_final_merge:
                 if selection_mode == "All": name_suffix = "All"
                 elif selection_mode == "Range": name_suffix = f"Range{self.range_start}-{self.range_end}"
                 else: name_suffix = "Selection"
                 merged_filename = os.path.join(download_dir, f"{masechta_name}_{name_suffix}_Full.pdf")

                 existing_files = [f for f in files_for_final_merge if os.path.exists(f)]

                 self.merge_pdfs(existing_files, merged_filename)

        if not keep_individual_amudim:
             self.clean_up(list(files_to_delete_later))
        else:
             print("[INFO] Keeping individual Amud PDFs as requested.")


        print(f"\n--- Download Finished for {masechta_name} ---")

    # --- Static Download/Merge/Cleanup Helpers ---
    @staticmethod
    def download_page(url, filename):
        max_retries = 5
        retry_delay = 1
        if not MasechetDownloader.check_internet_connection():
            print("[ERROR] No internet connection detected.")
            return False

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
        return False


    @staticmethod
    def merge_pdfs(pdf_files, output_filename):
        if not pdf_files:
            print(f"[WARN] No PDF files provided to merge into {output_filename}.")
            return
        merger = PdfMerger()
        print(f"[INFO] Merging {len(pdf_files)} files into {os.path.basename(output_filename)}...")
        valid_files_count = 0

        for pdf_path in pdf_files:
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                try:
                    merger.append(pdf_path)
                    valid_files_count += 1
                except Exception as e:
                    print(f"[ERROR] Failed to append {os.path.basename(pdf_path)} to merge list: {e}")

        if valid_files_count > 0:
            try:
                merger.write(output_filename)
                print(f"[INFO] Successfully merged into {os.path.basename(output_filename)}")
            except Exception as e:
                 print(f"[ERROR] Failed to write merged PDF {os.path.basename(output_filename)}: {e}")
            finally:
                 merger.close()
        else:
             print(f"[ERROR] No valid PDF files were available to merge into {os.path.basename(output_filename)}.")


    @staticmethod
    def clean_up(files_to_delete):
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


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if not MasechetDownloader.check_internet_connection():
        print("[ERROR] No internet connection detected.")
        return

    print(f"Detected environment: {MasechetDownloader.env}")
    app = MasechetDownloader()

    if not sys.stdin.isatty():
        # Non-interactive mode, read from stdin
        inputs = sys.stdin.read().splitlines()

        app.masechta_name = list(app.masechtos_info_static.keys())[int(inputs[0])-1]
        app.select_type = "Dapim" if inputs[1] == '1' else "Amudim"

        selection_mode_choice = int(inputs[2])
        if selection_mode_choice == 1:
            app.selection_mode = "All"
        elif selection_mode_choice == 2:
            app.selection_mode = "Range"
        else:
            app.selection_mode = "Individual"

        if app.selection_mode == "Range":
            if app.select_type == "Dapim":
                app.range_start = int(inputs[3])
                app.range_end = int(inputs[4])
            else:
                app.range_start = inputs[3]
                app.range_end = inputs[4]

        elif app.selection_mode == "Individual":
            if app.select_type == "Dapim":
                app.individual_selections = [int(s.strip()) for s in inputs[3].split(',')]
            else:
                app.individual_selections = [s.strip() for s in inputs[3].split(',')]

        app.merge_all_selection = inputs[5].lower() == 'y'
        if app.select_type == "Amudim":
            app.merge_amudim_into_dapim = inputs[6].lower() == 'y'
            if not app.merge_amudim_into_dapim:
                app.keep_individual_amudim = inputs[7].lower() == 'y'
    else:
        # Interactive mode
        app.get_user_input()

    app.start_download()

if __name__ == "__main__":
    main()
