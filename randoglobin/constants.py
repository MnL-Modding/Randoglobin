from pathlib import Path

from PySide6 import QtCore, QtWidgets

SCRIPT_DIR = Path(__file__).parent
FILES_DIR = SCRIPT_DIR / 'files'
LANG_DIR = SCRIPT_DIR / 'lang'

QtWidgets.QApplication.setApplicationName("randoglobin")
QtWidgets.QApplication.setApplicationDisplayName("Randoglobin")
CONFIG_DIR = Path(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.AppConfigLocation))

APP_DISPLAY_NAME = "Randoglobin"

NDS_ROM_FILENAME_FILTER = "NDS ROMs (*.nds);;All Files (*)"

JP_REGION_CODE = ord("J")
TW_REGION_CODE = ord("C")
NA_REGION_CODE = ord("E")
EU_REGION_CODE = ord("P")
KR_REGION_CODE = ord("K")

LANGUAGES = [ # display name, language key, in-game language value, incomplete flag (the length of this list just has to be 4)
    #["日本語",         "JP-JA", 0],
    #["臺灣話",         "TW-ZH", 0],
    ["English (NA)",  "NA-EN", 1],
    #["English (EU)",  "EU-EN", 1],
    #["Français (NA)", "NA-FR", 2],
    ["Français (EU)", "EU-FR", 2, "incomplete"],
    #["Deutsch",       "EU-DE", 3],
    #["Italiano",      "EU-IT", 4],
    ["Español",       "NA-ES", 5, "incomplete"],
    #["Castellano",    "EU-ES", 5],
    #["한글",           "KR-KO", 0],
]