# -*- coding: utf-8 -*-
"""
This script downloads specific pages (Dapim or Amudim) of the Talmud
from a central Google Drive account, merges them into PDFs, and saves them locally.

This version uses a SERVICE ACCOUNT for authentication, which is ideal for
distributing this script to other people so they can all access the files
from a single, shared Google Drive account without needing to log in.

**** SERVICE ACCOUNT SETUP (IMPORTANT!) ****
To use this script, you must create a Service Account, give it access to your
Google Drive files, and get its credentials.

1.  **Enable the Google Drive API:**
    a. Go to the Google Cloud Console: https://console.cloud.google.com/
    b. Create a new project (or select an existing one).
    c. In the navigation menu, go to "APIs & Services" > "Library".
    d. Search for "Google Drive API" and click "Enable".

2.  **Create a Service Account:**
    a. In the navigation menu, go to "IAM & Admin" > "Service Accounts".
    b. Click "+ CREATE SERVICE ACCOUNT".
    c. Give it a name (e.g., "talmud-downloader-sa") and a description.
    d. Click "CREATE AND CONTINUE".
    e. You can skip granting roles to the service account. Click "CONTINUE".
    f. You can skip granting users access. Click "DONE".

3.  **Generate a Key:**
    a. Find the service account you just created in the list.
    b. Click the three-dot menu (Actions) on the right and select "Manage keys".
    c. Click "ADD KEY" > "Create new key".
    d. Choose "JSON" as the key type and click "CREATE".
    e. A JSON file will be downloaded. **Rename this file to `service_account.json`**.
    f. **Place this `service_account.json` file in the SAME directory as this Python script.**

4.  **Share Your Google Drive Folder with the Service Account:**
    a. Open the `service_account.json` file you downloaded. Find the line with "client_email".
       It will look something like: "client_email": "your-sa-name@your-project.iam.gserviceaccount.com"
    b. Copy this entire email address.
    c. Go to the Google Drive account that holds the PDF files (your "dummy account").
    d. Right-click the folder containing the Talmud PDFs and click "Share".
    e. Paste the service account's email address into the "Add people and groups" field.
    f. Make sure it has at least "Viewer" permissions.
    g. Click "Share".

5.  **Set the Drive Folder ID in this script:**
    a. Open your Google Drive folder in your browser.
    b. The URL will look like: https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
    c. Copy the long string of characters at the end (the part after 'folders/').
    d. Paste this ID into the `DRIVE_FOLDER_ID` variable below.

Now, you can distribute this script along with the `service_account.json` file.
Anyone who runs it will be able to access the files in the shared folder.

**Dependencies Installation:**
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib PyPDF2
"""
import os
import sys
import time
import io
import logging

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
SERVICE_ACCOUNT_FILE = 'service_account.json'

# --- IMPORTANT: PASTE YOUR FOLDER ID HERE ---
# See Step 5 in the setup instructions above.
DRIVE_FOLDER_ID = '1L94Vy-FQblxPG7XoqIjPWe-ebhRYIs3x'

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

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
        """Calculates daf and amud from a page number."""
        daf = 2 + (page_number - 2) // 2
        amud = "b" if page_number % 2 != 0 else "a"
        return daf, amud

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
        self.drive_service = self.authenticate_google_drive()
        if not self.drive_service:
            print("[ERROR] Could not authenticate with Google Drive. Exiting.")
            sys.exit(1)

    def authenticate_google_drive(self):
        """Authenticates with the Google Drive API using a Service Account."""
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"\n[FATAL ERROR] Service account key file not found: '{SERVICE_ACCOUNT_FILE}'")
            print("Please follow the setup instructions at the top of the script.")
            return None
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            service = build('drive', 'v3', credentials=creds)
            print("[INFO] Successfully authenticated with Google Drive via Service Account.")
            return service
        except HttpError as error:
            print(f'[ERROR] An error occurred building the Drive service: {error}')
            return None
        except Exception as e:
            print(f'[ERROR] An unexpected error occurred during authentication: {e}')
            return None


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

    def start_download(self):
        """Main logic to determine which files to get and then download them."""
        # Check if the user has set the folder ID.
        if not DRIVE_FOLDER_ID or DRIVE_FOLDER_ID == 'PASTE_YOUR_FOLDER_ID_HERE':
            print("\n[FATAL ERROR] Please set the 'DRIVE_FOLDER_ID' variable at the top of the script.")
            print("Follow Step 5 in the setup instructions to get your folder ID.")
            sys.exit(1)

        masechta_name = self.masechta_name
        selection_mode = self.selection_mode
        select_type = self.select_type

        pages_to_download = set()
        _, total_pages = self.masechtos_info_static[masechta_name]
        max_daf = total_pages // 2
        extra_page = ".5" in str(total_pages / 2)

        download_dir = os.path.join(DOWNLOADS_DIR, masechta_name)
        os.makedirs(download_dir, exist_ok=True)

        print(f"\n--- Starting Download for {masechta_name} ---")
        print(f"Selection Mode: {selection_mode}, Select By: {select_type}")

        # --- Calculate which pages are needed based on user input ---
        if selection_mode == "All":
            pages_to_download.update(range(1, total_pages + 1))
        elif selection_mode == "Range":
            if select_type == "Dapim":
                start_daf, end_daf = self.range_start, self.range_end
                for daf in range(start_daf, end_daf + 1):
                    pages_to_download.add(2 * (daf - 2) + 1)
                    pages_to_download.add(2 * (daf - 2) + 2)
            else: # Amudim
                start_daf, start_amud = int(self.range_start[:-1]), self.range_start[-1]
                end_daf, end_amud = int(self.range_end[:-1]), self.range_end[-1]
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
            else: # Amudim
                for item_str in self.individual_selections:
                    daf, amud_char = int(item_str[:-1]), item_str[-1]
                    page = 2 * (daf - 2) + (1 if amud_char == 'a' else 2)
                    pages_to_download.add(page)

        valid_pages = {p for p in pages_to_download if 1 <= p <= total_pages}
        if not valid_pages:
            print("No valid pages selected or found for this Masechet.")
            return

        print(f"Will attempt to find and download {len(valid_pages)} files from Google Drive.")

        downloaded_amud_files = {}
        files_to_delete_later = set()

        # --- Main Download Loop ---
        for i, page_num in enumerate(sorted(list(valid_pages))):
            daf, amud = self.daf_amud_calculator(page_num)
            filename_to_search = f"{masechta_name}_Daf{daf}_Amud{amud}.pdf"
            local_filepath = os.path.join(download_dir, filename_to_search)
            downloaded_amud_files[page_num] = local_filepath

            if not os.path.exists(local_filepath):
                print(f"\n[INFO] Searching for '{filename_to_search}' in folder...")
                if not self.download_from_drive(filename_to_search, local_filepath):
                    print(f"[WARN] Could not find or download '{filename_to_search}'. Skipping.")
                    # Remove from list if download fails
                    downloaded_amud_files.pop(page_num, None)
                time.sleep(0.2) # Be nice to the API
            else:
                print(f"\n[INFO] File already exists locally: {os.path.basename(local_filepath)}")

            # Progress bar
            progress = (i + 1) / len(valid_pages)
            bar_length = 40
            block = int(round(bar_length * progress))
            text = f"\rOverall Progress: [{'#' * block + '-' * (bar_length - block)}] {int(progress * 100)}%"
            sys.stdout.write(text)
            sys.stdout.flush()

        # --- Merging Logic ---
        files_for_final_merge = []
        if self.merge_amudim_into_dapim:
            print("\n[INFO] Merging Amudim into Dapim...")
            daf_files = {}
            for page_num, filepath in downloaded_amud_files.items():
                if not os.path.exists(filepath): continue
                daf, _ = self.daf_amud_calculator(page_num)
                if daf not in daf_files: daf_files[daf] = []
                daf_files[daf].append(filepath)

            for daf, amud_filepaths in daf_files.items():
                if len(amud_filepaths) > 0:
                    daf_filename = os.path.join(download_dir, f"{masechta_name}_Daf{daf}.pdf")
                    self.merge_pdfs(sorted(amud_filepaths), daf_filename)
                    files_for_final_merge.append(daf_filename)
                    if not self.keep_individual_amudim:
                        files_to_delete_later.update(amud_filepaths)
        else:
            files_for_final_merge.extend(downloaded_amud_files.values())

        if self.merge_all_selection:
             print("\n[INFO] Merging selection into single PDF...")
             valid_files_for_merge = [f for f in files_for_final_merge if os.path.exists(f)]
             if valid_files_for_merge:
                 if selection_mode == "All": name_suffix = "All"
                 elif selection_mode == "Range": name_suffix = f"Range_{self.range_start}-{self.range_end}"
                 else: name_suffix = "Individual_Selection"
                 merged_filename = os.path.join(DOWNLOADS_DIR, f"{masechta_name}_{name_suffix}_Full.pdf")
                 self.merge_pdfs(sorted(valid_files_for_merge), merged_filename)

        if not self.keep_individual_amudim:
             self.clean_up(list(files_to_delete_later))
        else:
             print("[INFO] Keeping individual Amud PDFs as requested.")

        print(f"\n--- Download Finished for {masechta_name} ---")
        print(f"Files are located in: {download_dir}")


    def download_from_drive(self, filename, save_path):
        """Searches for a file within a specific Google Drive folder and downloads it."""
        try:
            # This query is much faster as it only searches within the specified folder.
            query = f"name = '{filename}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
            
            results = self.drive_service.files().list(
                q=query,
                # Use 'allDrives' to support both "My Drive" folders and "Shared drives"
                corpora='allDrives',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            items = results.get('files', [])

            if not items:
                return False

            file_id = items[0]['id']
            request = self.drive_service.files().get_media(fileId=file_id)
            
            with io.FileIO(save_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    progress = int(status.progress() * 100)
                    sys.stdout.write(f"\rDownloading {filename}: {progress}%")
                    sys.stdout.flush()
            print() # Newline after download progress
            return True

        except HttpError as error:
            print(f"\n[ERROR] An HTTP error occurred while downloading from Google Drive: {error}")
            return False
        except Exception as e:
            print(f"\n[ERROR] A general error occurred during download: {e}")
            return False

    @staticmethod
    def merge_pdfs(pdf_files, output_filename):
        """Merges a list of PDF files into a single output file."""
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
        """Deletes specified temporary files."""
        if not files_to_delete: return
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
    
    app = MasechetDownloader()
    app.get_user_input()
    app.start_download()

if __name__ == "__main__":
    main()
