from PySide6 import QtCore, QtGui, QtWidgets
import random

from randoglobin.constants import *

class SetupPopUp(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__()

        self.setWindowTitle("Randoglobin Setup")
        self.setWindowIcon(QtGui.QIcon(str(FILES_DIR / 'randoglobin.ico')))

        self.parent = parent
        self.language_box_save = LANGUAGES.index(["English (NA)",  "NA-EN", 1])
        self.mute_audio_save = False

        self.init_ui(LANGUAGES.index(["English (NA)",  "NA-EN", 1]))

    def init_ui(self, lang):
        translator = QtCore.QTranslator()
        if translator.load(str(LANG_DIR / f'{LANGUAGES[lang][1]}.qm')):
            self.parent.installTranslator(translator)
        
        if self.layout() is not None:
            while self.layout().count():
                item = self.layout().takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            main_layout = self.layout()
        else:
            main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(QtWidgets.QLabel(self.tr("Please Choose a Language:")), alignment = QtCore.Qt.AlignmentFlag.AlignLeft)

        self.language_box = QtWidgets.QComboBox()
        for lang in LANGUAGES:
            self.language_box.addItem(QtGui.QIcon(str(LANG_DIR / f"{lang[1]}.png")), lang[0])
        main_layout.addWidget(self.language_box)

        self.mute_audio = QtWidgets.QCheckBox(self.tr("Mute Audio"))
        main_layout.addWidget(self.mute_audio, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.language_box.setCurrentIndex(self.language_box_save)
        self.language_box.currentIndexChanged.connect(self.change_lang)
        self.mute_audio.setChecked(self.mute_audio_save)
        self.mute_audio.checkStateChanged.connect(self.change_mute)

        ok_button = QtWidgets.QPushButton(self.tr("OK"))
        ok_button.clicked.connect(self.accept)
        main_layout.addWidget(ok_button, alignment = QtCore.Qt.AlignmentFlag.AlignRight)

        self.setLayout(main_layout)
    
    def change_lang(self, lang):
        self.language_box_save = lang
        self.init_ui(lang)
    
    def change_mute(self, state):
        self.mute_audio_save = state == QtCore.Qt.Checked