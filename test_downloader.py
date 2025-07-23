import unittest
import os
from unittest.mock import patch, MagicMock

# It's better to import the specific class you're testing
from DownloaderShasTextDrive import MasechetDownloader

class TestMasechetDownloader(unittest.TestCase):

    @patch('DownloaderShasTextDrive.build')
    def setUp(self, mock_build):
        # Mock the Google Drive service to avoid actual authentication and API calls
        self.mock_drive_service = MagicMock()
        mock_build.return_value = self.mock_drive_service

        # Create an instance of the downloader
        # We patch 'builtins.input' to simulate user input during initialization if needed
        with patch('builtins.input', side_effect=['1']): # Assume some default input if constructor needs it
            self.downloader = MasechetDownloader()
            # Directly setting attributes to bypass interactive get_user_input
            self.downloader.drive_service = self.mock_drive_service

    def test_daf_amud_calculator(self):
        # Test cases: (page_number, expected_daf, expected_amud)
        cases = [
            (1, 2, "a"), (2, 2, "b"), (3, 3, "a"), (4, 3, "b"),
            (125, 64, "a"), (126, 64, "b"), (127, 65, "a"),
        ]
        for page, expected_daf, expected_amud in cases:
            with self.subTest(page=page):
                daf, amud = MasechetDownloader.daf_amud_calculator(page)
                self.assertEqual(daf, expected_daf)
                self.assertEqual(amud, expected_amud)

        self.assertEqual(MasechetDownloader.daf_amud_calculator(0), (None, None))
        self.assertEqual(MasechetDownloader.daf_amud_calculator(-1), (None, None))

    def test_page_number_from_daf_amud(self):
        cases = [
            (2, 'a', 1), (2, 'b', 2), (3, 'a', 3), (3, 'b', 4),
            (64, 'a', 125), (64, 'b', 126), (65, 'a', 127),
        ]
        for daf, amud_char, expected_page in cases:
            with self.subTest(daf=daf, amud=amud_char):
                page = 2 * (daf - 2) + (1 if amud_char == 'a' else 2)
                self.assertEqual(page, expected_page)

    @patch('DownloaderShasTextDrive.MasechetDownloader.download_from_drive')
    @patch('os.path.exists', return_value=False)
    def test_download_logic_range_dapim(self, mock_exists, mock_download):
        # --- Setup Simulation ---
        self.downloader.masechta_name = "Brachos"
        self.downloader.select_type = "Dapim"
        self.downloader.selection_mode = "Range"
        self.downloader.range_start = 3
        self.downloader.range_end = 4

        # --- Execute ---
        self.downloader.start_download()

        # --- Assert ---
        # It should try to download pages 3, 4, 5, 6 which correspond to daf 3 and 4
        # Page 3 = Daf 3a, Page 4 = Daf 3b
        # Page 5 = Daf 4a, Page 6 = Daf 4b
        expected_calls = [
            unittest.mock.call("Brachos_Daf3_Amuda.pdf", unittest.mock.ANY),
            unittest.mock.call("Brachos_Daf3_Amudb.pdf", unittest.mock.ANY),
            unittest.mock.call("Brachos_Daf4_Amuda.pdf", unittest.mock.ANY),
            unittest.mock.call("Brachos_Daf4_Amudb.pdf", unittest.mock.ANY),
        ]
        mock_download.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_download.call_count, 4)

    @patch('DownloaderShasTextDrive.MasechetDownloader.download_from_drive')
    @patch('os.path.exists', return_value=False)
    def test_download_logic_individual_amudim(self, mock_exists, mock_download):
        # --- Setup Simulation ---
        self.downloader.masechta_name = "Shabbos"
        self.downloader.select_type = "Amudim"
        self.downloader.selection_mode = "Individual"
        self.downloader.individual_selections = ["5a", "10b", "15a"]

        # --- Execute ---
        self.downloader.start_download()

        # --- Assert ---
        # Page for 5a: 2*(5-2)+1 = 7
        # Page for 10b: 2*(10-2)+2 = 18
        # Page for 15a: 2*(15-2)+1 = 27
        expected_calls = [
            unittest.mock.call("Shabbos_Daf5_Amuda.pdf", unittest.mock.ANY),
            unittest.mock.call("Shabbos_Daf10_Amudb.pdf", unittest.mock.ANY),
            unittest.mock.call("Shabbos_Daf15_Amuda.pdf", unittest.mock.ANY),
        ]
        mock_download.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_download.call_count, 3)

    @patch('DownloaderShasTextDrive.MasechetDownloader.download_from_drive')
    @patch('os.path.exists', return_value=False)
    def test_download_logic_all_masechta(self, mock_exists, mock_download):
        # --- Setup Simulation ---
        self.downloader.masechta_name = "Makkos" # Makkos has 46 pages
        self.downloader.select_type = "Dapim" # Does not matter for "All"
        self.downloader.selection_mode = "All"

        # --- Execute ---
        self.downloader.start_download()

        # --- Assert ---
        # Makkos has 46 total pages according to masechtos_info_static
        total_pages = self.downloader.masechtos_info_static["Makkos"][1]
        self.assertEqual(total_pages, 46)
        self.assertEqual(mock_download.call_count, 46)
        # Check the last file it tries to download
        # Page 46 = Daf 24b
        mock_download.assert_any_call("Makkos_Daf24_Amudb.pdf", unittest.mock.ANY)

if __name__ == '__main__':
    unittest.main()
