# Shas Downloader (Google Drive Edition)

**Note:** The most up-to-date version of this application is `DownloaderShasDriveGUI_new.py`. Please use this file to run the application. The older versions have been moved to the `archive` directory.

## About the Project

This project is a graphical user interface (GUI) application built with Python and `tkinter` that allows users to download PDF files of the Talmud (Masechet) from a Google Drive folder.

### Features

*   **User-friendly Interface:** Provides a simple GUI to select and download tractates.
*   **Flexible Downloading:** Download entire tractates, a range of pages (Dapim), or individual pages (Amudim).
*   **PDF Merging:** Automatically merge downloaded pages into a single, convenient PDF file.
*   **Theme Support:** Adapts to your system's light or dark theme for comfortable viewing.

## Getting Started

### Prerequisites

You will need to have Python 3 installed on your system.

### Installation

1.  **Clone the repository or download the source code.**

2.  **Install the required dependencies.** Open a terminal or command prompt in the project directory and run:
    ```bash
    pip install PyPDF2 google-api-python-client google-auth-httplib2 google-auth-oauthlib darkdetect sv_ttk
    ```

3.  **Set up Google Drive API access.**
    *   You will need a Google Cloud project with the Google Drive API enabled.
    *   Create a service account and generate a JSON key file.
    *   **Important:** Rename the downloaded key file to `service_account.json` and place it inside the `assets` directory.
    *   Share your Google Drive folder containing the PDFs with the service account's email address.

### Running the Application

Once you have completed the setup, you can run the application with the following command:

```bash
python DownloaderShasDriveGUI_new.py
```

The application will launch, and you can start downloading the files you need. Downloaded files will be saved in the `downloads` directory.
