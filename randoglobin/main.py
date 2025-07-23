import os
import sys
import random
import struct
import hashlib
import traceback
import configparser
from io import BytesIO
from copy import deepcopy
from functools import partial

import ndspy.rom
import ndspy.codeCompression
from PySide6 import QtCore, QtGui, QtMultimedia, QtWidgets
from mnllib.bis import FEventScriptManager, BattleScriptManager, LanguageTable, TextTable, BIS_ENCODING

from randoglobin.constants import *
from randoglobin.patch import skip_intro, remove_enemies, multiply_exp, change_start_level, open_worldify
from randoglobin.treasure import TreasureTab, randomize_treasure
from randoglobin.palette import PaletteTab, randomize_colors
from randoglobin.music import MusicTab, randomize_music
from randoglobin.image import create_MObj_sprite, create_textbox
from randoglobin.popups import SetupPopUp
from randoglobin.arm import apply_arm_patches


def main():
    app = QtWidgets.QApplication(sys.argv)

    if os.name == 'nt':
        app.setStyle('Fusion')

    window = MainWindow(app)

    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent):
        super(MainWindow, self).__init__()

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(QtGui.QIcon(str(FILES_DIR / 'ico_randoglobin.ico')))

        self.globin_anim_timer = QtCore.QTimer()
        self.globin_anim_timer.setInterval(1000 / 30)
        self.globin_anim_timer.timeout.connect(self.animate_globin)

        self.rando_start_sfx = QtMultimedia.QSoundEffect(self)
        self.rando_start_sfx.setSource(QtCore.QUrl.fromLocalFile(FILES_DIR / "snd_randoglobin_wait.wav"))
        self.rando_start_sfx.setLoopCount(999)
        self.rando_end_sfx = QtMultimedia.QSoundEffect(self)
        self.rando_end_sfx.setSource(QtCore.QUrl.fromLocalFile(FILES_DIR / "snd_randoglobin_success.wav"))
        self.rando_fail_sfx = QtMultimedia.QSoundEffect(self)
        self.rando_fail_sfx.setSource(QtCore.QUrl.fromLocalFile(FILES_DIR / "snd_randoglobin_fail.wav"))

        self.parent = parent

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not (CONFIG_DIR / "config.ini").exists():
            setup_popup = SetupPopUp(parent)

            if setup_popup.exec() != 1:
                sys.exit(2)
            target_lang = setup_popup.language_box.currentIndex()
            muted = setup_popup.mute_audio.isChecked()

            config = configparser.ConfigParser()
            config['UserPreferences'] = {
                'lang': LANGUAGES[target_lang][1],
                'muted': str(muted)
            }

            with (CONFIG_DIR / "config.ini").open("w") as config_file:
                config.write(config_file)
        
        config = configparser.ConfigParser()
        config.read(str(CONFIG_DIR / "config.ini"))

        translator = QtCore.QTranslator()
        if translator.load(str(LANG_DIR / f'{config.get('UserPreferences', 'lang')}.qm')):
            parent.installTranslator(translator)

        # -------------------------------------------------------------------------------

        self.import_rom(False)

        # -------------------------------------------------------------------------------

        self.muted = config.get('UserPreferences', 'muted')
        target_lang = config.get('UserPreferences', 'lang')
        for i, language in enumerate(LANGUAGES):
            if language[1] == target_lang:
                self.change_lang(i)
                return
        
        self.change_lang(LANGUAGES.index(["English (NA)", "NA-EN", 1]))

    def import_rom(self, repeat_import = True):
        QtWidgets.QMessageBox.information(
            self,
            self.tr("Choose a ROM"),
            self.tr("Please choose a North American or European Bowser's Inside Story ROM to open."),
        )
        while True: # lmao
            path, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
                parent=self,
                caption=self.tr("Open ROM"),
                filter=NDS_ROM_FILENAME_FILTER,
            )

            if path == '':
                if repeat_import:
                    return
                else:
                    sys.exit(2)

            try:
                rom = ndspy.rom.NintendoDSRom.fromFile(path)
            except struct.error:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Invalid File"),
                    self.tr("The chosen file is not a Nintendo DS ROM file."),
                )
                continue

            if rom.name != b"MARIO&LUIGI3":
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Invalid ROM"),
                    self.tr("The chosen ROM is not a valid Bowser's Inside Story ROM."),
                )
                continue
            
            if rom.idCode[3] == NA_REGION_CODE or rom.idCode[3] == EU_REGION_CODE:
                self.rom = rom
                self.path = path
                self.new_path = self.path
                if repeat_import:
                    self.init_ui()
                break
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Invalid ROM"),
                    self.tr("The chosen ROM is not from a valid region.\n\nOnly a North American or European Bowser's Inside Story ROM will work."),
                )
        
        chunk_size = 4096
        hasher = hashlib.new("sha256")
        with open(self.path, 'rb') as rom:
            while True:
                chunk = rom.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        
        rom_is_modded = True
        match hasher.hexdigest():
            case "9126963d6c6b6f81a9a666ba766e223781ff286634486e2a56d07a4c82eef4f1":
                if self.rom.idCode[3] == NA_REGION_CODE:
                    rom_is_modded = False
            case "e7417640d1b0c65cb01924a4a38bd1fc6b330ead88710152f13677a896147f39":
                if self.rom.idCode[3] == EU_REGION_CODE:
                    rom_is_modded = False
            # other region checksums will need to be calculated when support for those is added
        
        if rom_is_modded:
            QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Modded ROM Detected"),
                    self.tr("The chosen ROM appears to be modded.\nAlready modded ROMs, especially those that have already been randomized, may become unusable when exported with Randoglobin.\n\nProceed with caution."),
                )
    
    def toggle_mute(self, state):
        self.muted = str(state)

        self.rando_start_sfx.setVolume(0.3 * int(not state))
        self.rando_end_sfx.setVolume(0.3 * int(not state))
        self.rando_fail_sfx.setVolume(0.3 * int(not state))

        config = configparser.ConfigParser()
        config.read(CONFIG_DIR / "config.ini")
        config['UserPreferences']['muted'] = self.muted
        with open(CONFIG_DIR / "config.ini", "w") as config_file:
            config.write(config_file)
    
    def change_lang(self, lang):
        self.lang = deepcopy(LANGUAGES[lang])

        config = configparser.ConfigParser()
        config.read(CONFIG_DIR / "config.ini")
        config['UserPreferences']['lang'] = self.lang[1]
        with open(CONFIG_DIR / "config.ini", "w") as config_file:
            config.write(config_file)

        translator = QtCore.QTranslator()
        if translator.load(str(LANG_DIR / f'{self.lang[1]}.qm')):
            self.parent.installTranslator(translator)

        if self.rom.idCode[3] == JP_REGION_CODE:
            allowed_language_names = ["日本語"]
            allowed_languages = ["JP-JA"]
            lang_codes = [0]
        elif self.rom.idCode[3] == TW_REGION_CODE:
            allowed_language_names = ["臺灣話"]
            allowed_languages = ["TW-ZH"]
            lang_codes = [0]
        elif self.rom.idCode[3] == NA_REGION_CODE:
            allowed_language_names = ["English (NA)", "Français (NA)", "Español"]
            allowed_languages = ["NA-EN", "NA-ES", "NA-FR"]
            lang_codes = [1, 2, 5]
        elif self.rom.idCode[3] == EU_REGION_CODE:
            allowed_language_names = ["English (EU)", "Français (EU)", "Deutsch", "Italiano", "Castellano"]
            allowed_languages = ["EU-EN", "EU-FR", "EU-DE", "EU-IT", "EU-ES"]
            lang_codes = [1, 2, 3, 4, 5]
        elif self.rom.idCode[3] == KR_REGION_CODE:
            allowed_language_names = ["한글"]
            allowed_languages = ["KR-KO"]
            lang_codes = [0]
        
        if self.lang[1] not in allowed_languages:
            if (self.lang[2] in lang_codes):
                QtWidgets.QMessageBox.information(
                    self,
                    self.tr("Language Not in ROM"),
                    self.tr("The dialect you have chosen is not present in your current ROM.\n\nText ripped from the game will be:") + f" {allowed_language_names[lang_codes.index(self.lang[2])]}"
                )
            elif (len(lang_codes) == 1):
                self.lang[2] = lang_codes[0]
                QtWidgets.QMessageBox.information(
                    self,
                    self.tr("Language Not in ROM"),
                    self.tr("The language you have chosen is not present in your current ROM.\n\nText ripped from the game will be:") + f" {allowed_language_names[0]}"
                )
            else:
                lang_ask = QtWidgets.QMessageBox()
                lang_ask.setWindowTitle(self.tr("Language Not in ROM"))
                lang_ask.setWindowIcon(QtGui.QIcon(str(FILES_DIR / 'ico_randoglobin.ico')))
                lang_ask.setText(self.tr("The language you have chosen is not present in your current ROM.\n\nWhich language would you like to use in ripped text?"))
                lang_ask.setIcon(QtWidgets.QMessageBox.Question)

                for language in allowed_language_names:
                    lang_ask.addButton(language, QtWidgets.QMessageBox.ButtonRole.AcceptRole)
                result = lang_ask.exec()
                self.lang[2] = lang_codes[result - 2]

        self.init_ui()
    
    def show_credits(self):
        credit = QtWidgets.QMessageBox()
        credit.setWindowTitle("Credits")
        credit.setWindowIcon(QtGui.QIcon(str(FILES_DIR / 'ico_randoglobin.ico')))
        credit.setText(f'''{self.tr("Randoglobin Credits")}:<br><br>
            <a href="https://bsky.app/profile/thepurpleanon.bsky.social">ThePurpleAnon</a><br>- {self.tr("Python Code")} / {self.tr("UI Design")}<br>
            <a href="https://github.com/DimiDimit">DimiDimit</a><br>- {self.tr("Additional Code and Patches")} / <a href="https://github.com/MnL-Modding/mnllib.py"><code>mnllib.py</code></a> & <a href="https://github.com/MnL-Modding/mnllib.rs"><code>.rs</code></a><br>
            <a href="https://bsky.app/profile/miikheaven.bsky.social">MiiK</a><br>- {self.tr("Randoglobin Icon")} / {self.tr("Additional Graphics")}
            <br><br>
            {self.tr("Translators")}:<br>
            - Español <img src="{str(LANG_DIR / 'NA-ES.png')}" alt="NA-ES Flag" style="vertical-align: middle;"> - <a href="https://bsky.app/profile/angelthem.bsky.social">AngelThe_M</a>
        ''')
        credit.setTextFormat(QtCore.Qt.RichText)
        credit.exec()
    
    def init_ui(self):
        translator = QtCore.QTranslator()
        if translator.load(str(LANG_DIR / f'{self.lang[1]}.qm')):
            self.parent.installTranslator(translator)

        # =====================================================================================================

        self.menuBar().clear()
        menu_bar = self.menuBar()
        menu_bar_file = menu_bar.addMenu(self.tr("&File"))
        menu_bar_file.addAction(
            self.tr("&Import"),
            QtGui.QKeySequence.StandardKey.Open,
            self.import_rom,
        )
        menu_bar_file.addSeparator() # -----------------------------------------
        menu_bar_file.addAction(
            self.tr("&Quit"),
            QtGui.QKeySequence.StandardKey.Quit,
            QtWidgets.QApplication.quit,
        )

        menu_bar_options = menu_bar.addMenu(self.tr("&Options"))
        language_selector = QtWidgets.QMenu(self.tr("&Language"), self)
        for i, lang in enumerate(LANGUAGES):
            lang_string = lang[0]
            if self.lang[1] == lang[1]:
                lang_string += " ✓"
            language_selector.addAction(
                QtGui.QIcon(str(LANG_DIR / f"{lang[1]}.png")),
                lang_string,
                partial(self.change_lang, i)
            )
        menu_bar_options.addMenu(language_selector)
        audio_mute = QtGui.QAction(self.tr("&Mute Audio"), self)
        audio_mute.setCheckable(True)
        audio_mute.setChecked(self.muted == "True")
        audio_mute.toggled.connect(self.toggle_mute)
        menu_bar_options.addAction(audio_mute)

        menu_bar.addAction(
            self.tr("&Credits"),
            self.show_credits,
        )

        arm9 = BytesIO(ndspy.codeCompression.decompress(self.rom.arm9))
        
        if self.rom.idCode[3] == NA_REGION_CODE or self.rom.idCode[3] == EU_REGION_CODE:                                           # US-base
            self.icon_overlay_BObj_offsets = (0x8C1C, 0x7548, 0x6290) # filedata, sprite groups, palette groups
            self.icon_overlay_BObj = [self.rom.loadArm9Overlays([14])[14].data, self.rom.loadArm9Overlays([13])[13].data]
            self.icon_overlay_FObj_offsets = (0xE8A0, 0x165E4, 0x150C8) # filedata, sprite groups, palette groups
            self.icon_overlay_FObjPc_offsets = (0xBDB0, 0x15854, 0x148D4) # filedata, sprite groups, palette groups
            self.icon_overlay_FObj = self.rom.loadArm9Overlays([3])[3].data
            self.icon_overlay_MObj_offsets = (0x20EC, 0x2E94, 0x2C80) # filedata, sprite groups, palette groups
            self.icon_overlay_MObj = self.rom.loadArm9Overlays([132])[132].data
            textbox_pal_offset = 0x4C144
            textbox_graph_offset = 0x4C6BC
            arm9.seek(0x43D3C)
            test0, test1 = struct.unpack('<II', arm9.read(0x8))
            arm9.seek(-8, 1)
            self.font_file = arm9.read(test0 + test1)
            self.latin_font_file = self.font_file
        elif self.rom.idCode[3] == JP_REGION_CODE or self.rom.idCode[3] == TW_REGION_CODE or self.rom.idCode[3] == KR_REGION_CODE: # JP-base
            self.icon_overlay_MObj = self.rom.loadArm9Overlays([126])[126].data
            self.icon_overlay_MObj_offsets = (0x2098, 0x2DA0, 0x2BA0) # filedata, sprite groups, palette groups
        self.fobj_icon_file = self.rom.getFileByName('FObj/FObj.dat')
        self.fobjpc_icon_file = self.rom.getFileByName('FObjPc/FObjPc.dat')
        self.mobj_icon_file = self.rom.getFileByName('MObj/MObj.dat')
        self.bobj_icon_file = self.rom.getFileByName('BObjPc/BObjPc.dat')

        mfset_Help = self.rom.getFileByName('BData/mfset_Help.dat')
        self.battle_help_text = []
        menu_text = LanguageTable.from_bytes(mfset_Help, False)
        if menu_text.text_tables[self.lang[2] + 1]:
            for string in menu_text.text_tables[self.lang[2] + 1].entries:
                index = string.index(0xFF)
                self.battle_help_text.append(string[:index].decode(BIS_ENCODING, "ignore"))

        arm9.seek(textbox_pal_offset)
        self.textbox_pal = [arm9.read(16 * 0x2), arm9.read(16 * 0x2)]
        arm9.seek(textbox_graph_offset)
        self.textbox_graph = arm9.read(100 * 0x20)

        main = QtWidgets.QWidget()
        main_layout = QtWidgets.QGridLayout(main)

        self.main_tabs = QtWidgets.QTabWidget()
        self.main_tabs.setUsesScrollButtons(False)
        #self.main_tabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.East)

        self.main_tabs.addTab(main, QtGui.QIcon(str(FILES_DIR / 'ico_randoglobin.ico')), self.tr("Randomizer"))

        self.treasure_settings = TreasureTab(self.icon_overlay_FObj_offsets, self.icon_overlay_FObjPc_offsets, self.icon_overlay_FObj, self.fobj_icon_file, self.fobjpc_icon_file, self.icon_overlay_MObj_offsets, self.icon_overlay_MObj, self.mobj_icon_file)
        tex = create_MObj_sprite(self.icon_overlay_MObj_offsets, self.icon_overlay_MObj, self.mobj_icon_file, 0x9, 0x16, 0)
        self.main_tabs.addTab(self.treasure_settings, tex, self.tr("Treasure"))

        #tex = create_MObj_sprite(self.icon_overlay_MObj_offsets, self.icon_overlay_MObj, self.mobj_icon_file, 0x9, 0x28, 0)
        #self.main_tabs.addTab(QtWidgets.QWidget(), tex, self.tr("Specials"))

        self.palette_settings = PaletteTab(self.icon_overlay_BObj_offsets, self.icon_overlay_BObj, self.bobj_icon_file, self.icon_overlay_FObj_offsets, self.icon_overlay_FObj, self.fobj_icon_file, self.textbox_pal, self.textbox_graph, self.font_file, self.latin_font_file, self.battle_help_text)
        tex = QtGui.QPixmap(str(FILES_DIR / 'img_pal.png'))
        self.main_tabs.addTab(self.palette_settings, tex, self.tr("Palette"))

        self.music_settings = MusicTab()
        tex = QtGui.QPixmap(str(FILES_DIR / 'img_mus.png'))
        self.main_tabs.addTab(self.music_settings, tex, self.tr("Music"))

        self.setCentralWidget(self.main_tabs)
        # ------------------------------------------

        # main_layout.addWidget(QtWidgets.QLabel("This randomizer is still in active development. Options prefaced with \"!!\"\n  are either incomplete or still have known issues that need to be fixed."), 0, 0, 1, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(QtWidgets.QLabel("- " + self.tr("Quality of Life Settings") + " -"), 0, 0, 1, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # # ------------------------------------------
        # line = QtWidgets.QFrame()
        # line.setFrameShape(QtWidgets.QFrame.HLine)
        # line.setFrameShadow(QtWidgets.QFrame.Sunken)
        # main_layout.addWidget(line, 1, 0, 1, 3)
        # # ------------------------------------------

        settings = QtWidgets.QWidget()
        settings_layout = QtWidgets.QGridLayout(settings)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(settings, 1, 0, 1, 1)

        self.write_spoiler = QtWidgets.QCheckBox()
        settings_layout.addWidget(self.write_spoiler, 0, 1, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        string = QtWidgets.QLabel(self.tr("Write Spoiler File"))
        settings_layout.addWidget(string, 0, 0)
        string.setBuddy(self.write_spoiler)

        self.use_custom_seed = QtWidgets.QCheckBox()
        self.use_custom_seed.checkStateChanged.connect(self.custom_seed_box_enable)
        settings_layout.addWidget(self.use_custom_seed, 1, 1, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        string = QtWidgets.QLabel(self.tr("Use Specific Seed"))
        settings_layout.addWidget(string, 1, 0)
        string.setBuddy(self.use_custom_seed)

        self.custom_seed = QtWidgets.QLineEdit()
        settings_layout.addWidget(self.custom_seed, 2, 1, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        string = QtWidgets.QLabel(self.tr("Seed"))
        settings_layout.addWidget(string, 2, 0)
        string.setBuddy(self.custom_seed)

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line, 2, 0, 1, 3)
        # ------------------------------------------
        main_layout.addWidget(QtWidgets.QLabel("- " + self.tr("Main Randomization Settings") + " -"), 3, 0, 1, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        # ------------------------------------------

        random = QtWidgets.QWidget()
        random_layout = QtWidgets.QVBoxLayout(random)
        random_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(random, 4, 0, 1, 3)

        bg = QtWidgets.QFrame()
        bg_layout = QtWidgets.QHBoxLayout(bg)
        #bg.setStyleSheet("QFrame { background-color: " + TAB_COLORS[1] + "; }")
        #bg.setFrameShape(QtWidgets.QFrame.StyledPanel)
        #bg_layout.setContentsMargins(3, 3, 3, 3)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        self.rand_treasure = QtWidgets.QCheckBox()
        self.rand_treasure.checkStateChanged.connect(self.tabs_enable)
        text = QtWidgets.QLabel(self.tr("Randomize Treasure"))
        text.setStyleSheet("background-color: #00000000")
        text.setBuddy(self.rand_treasure)
        bg_layout.addWidget(text)
        bg_layout.addWidget(self.rand_treasure, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        random_layout.addWidget(bg)

        # bg = QtWidgets.QFrame()
        # bg_layout = QtWidgets.QHBoxLayout(bg)
        # #bg.setStyleSheet("QFrame { background-color: " + TAB_COLORS[2] + "; }")
        # #bg.setFrameShape(QtWidgets.QFrame.StyledPanel)
        # #bg_layout.setContentsMargins(3, 3, 3, 3)
        # bg_layout.setContentsMargins(0, 0, 0, 0)
        self.rand_attacks = QtWidgets.QCheckBox()
        # self.rand_attacks.checkStateChanged.connect(self.tabs_enable)
        # text = QtWidgets.QLabel("!! " + self.tr("Randomize Special Attacks"))
        # text.setStyleSheet("background-color: #00000000")
        # text.setBuddy(self.rand_attacks)
        # bg_layout.addWidget(text)
        # bg_layout.addWidget(self.rand_attacks, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        # random_layout.addWidget(bg)

        bg = QtWidgets.QFrame()
        bg_layout = QtWidgets.QHBoxLayout(bg)
        #bg.setStyleSheet("QFrame { background-color: " + TAB_COLORS[0] + "; }")
        #bg.setFrameShape(QtWidgets.QFrame.StyledPanel)
        #bg_layout.setContentsMargins(3, 3, 3, 3)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        self.rand_colors = QtWidgets.QCheckBox()
        self.rand_colors.checkStateChanged.connect(self.tabs_enable)
        text = QtWidgets.QLabel(self.tr("Randomize Player Palettes"))
        text.setStyleSheet("background-color: #00000000")
        text.setBuddy(self.rand_colors)
        bg_layout.addWidget(text)
        bg_layout.addWidget(self.rand_colors, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        random_layout.addWidget(bg)

        bg = QtWidgets.QFrame()
        bg_layout = QtWidgets.QHBoxLayout(bg)
        #bg.setStyleSheet("QFrame { background-color: " + TAB_COLORS[3] + "; }")
        #bg.setFrameShape(QtWidgets.QFrame.StyledPanel)
        #bg_layout.setContentsMargins(3, 3, 3, 3)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        self.rand_music = QtWidgets.QCheckBox()
        self.rand_music.checkStateChanged.connect(self.tabs_enable)
        text = QtWidgets.QLabel(self.tr("Randomize Music"))
        text.setStyleSheet("background-color: #00000000")
        text.setBuddy(self.rand_music)
        bg_layout.addWidget(text)
        bg_layout.addWidget(self.rand_music, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        random_layout.addWidget(bg)

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line, 1, 1, 1, 1)
        # ------------------------------------------

        qol = QtWidgets.QWidget()
        qol_layout = QtWidgets.QGridLayout(qol)
        qol_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(qol, 1, 2, 1, 1)

        self.intro = QtWidgets.QComboBox()
        self.intro.addItems([self.tr("Blorbs Intro"), self.tr("Peach's Castle"), self.tr("Trash Pit")])
        qol_layout.addWidget(self.intro, 0, 1, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        string = QtWidgets.QLabel(self.tr("Game Intro"))
        qol_layout.addWidget(string, 0, 0)
        string.setBuddy(self.intro)

        self.no_enemies = QtWidgets.QCheckBox()
        qol_layout.addWidget(self.no_enemies, 1, 1, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        string = QtWidgets.QLabel(self.tr("No Enemies"))
        qol_layout.addWidget(string, 1, 0)
        string.setBuddy(self.no_enemies)

        self.exp_mult = QtWidgets.QDoubleSpinBox()
        self.exp_mult.setValue(1)
        self.exp_mult.setDecimals(1)
        self.exp_mult.setSingleStep(0.1)
        self.exp_mult.setRange(0.0, 100.0)
        self.exp_mult.setSuffix("x")
        qol_layout.addWidget(self.exp_mult, 2, 1, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        string = QtWidgets.QLabel(self.tr("EXP Multiplier"))
        qol_layout.addWidget(string, 2, 0)
        string.setBuddy(self.exp_mult)

        self.starting_level = QtWidgets.QSpinBox()
        self.starting_level.setValue(1)
        self.starting_level.setRange(1, 99)
        qol_layout.addWidget(self.starting_level, 3, 1, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        string = QtWidgets.QLabel(self.tr("Initial Player Level"))
        qol_layout.addWidget(string, 3, 0)
        string.setBuddy(self.starting_level)

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line, 5, 0, 1, 3)
        # ------------------------------------------
        main_layout.addWidget(QtWidgets.QLabel("- " + self.tr("Chaotic Randomization Settings") + " -"), 6, 0, 1, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        # ------------------------------------------

        chaos = QtWidgets.QWidget()
        chaos_layout = QtWidgets.QVBoxLayout(chaos)
        chaos_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(chaos, 7, 0, 1, 3)

        setting = QtWidgets.QWidget()
        setting_layout = QtWidgets.QHBoxLayout(setting)
        setting_layout.setContentsMargins(0, 0, 0, 0)
        self.chaos_badges = QtWidgets.QCheckBox()
        text = QtWidgets.QLabel(self.tr("Randomize Badge Combo Effects") + "  " + self.tr("(kinda broken)"))
        text.setBuddy(self.chaos_badges)
        setting_layout.addWidget(text)
        setting_layout.addWidget(self.chaos_badges, alignment = QtCore.Qt.AlignmentFlag.AlignRight)
        chaos_layout.addWidget(setting)

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line, 8, 0, 1, 3)
        # ------------------------------------------

        self.the_button = QtWidgets.QPushButton(self.tr("Randomize!"))
        self.the_button.clicked.connect(self.randomize)
        main_layout.addWidget(self.the_button, 9, 0, 1, 3)

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line, 10, 0, 1, 3)
        # ------------------------------------------

        self.log_scroll_area = QtWidgets.QScrollArea()
        self.log_scroll_area.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.log_scroll_area.setWidgetResizable(True)
        self.log_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        log_widget = QtWidgets.QWidget()
        self.log_scroll_area.setWidget(log_widget)
        self.log_scroll_area.verticalScrollBar().rangeChanged.connect(self.scroll_widget_to_bottom)
        self.log = QtWidgets.QVBoxLayout(log_widget)
        self.log.setAlignment(QtCore.Qt.AlignTop)
        main_layout.addWidget(self.log_scroll_area, 11, 0, 1, 3)
        
        # ------------------------------------------
        # default settings
        self.write_spoiler.setChecked(True)
        self.use_custom_seed.setChecked(False)
        self.custom_seed.setEnabled(False)
        self.custom_seed.setText(self.tr("Random"))

        self.rand_treasure.setChecked(True)
        # self.rand_attacks.setChecked(False)
        self.rand_colors.setChecked(False)
        self.rand_music.setChecked(False)

        self.chaos_badges.setChecked(False)

        self.intro.setCurrentIndex(2)
        self.no_enemies.setChecked(False)
        self.exp_mult.setValue(1.5)
        self.starting_level.setValue(5)

        self.log.addWidget(QtWidgets.QLabel("Awaiting Randomization..."))
    
    def tabs_enable(self):
        self.main_tabs.setTabEnabled(1, self.rand_treasure.isChecked())
        self.main_tabs.setTabEnabled(2, self.rand_colors.isChecked())
        self.main_tabs.setTabEnabled(3, self.rand_music.isChecked())
    
    def custom_seed_box_enable(self, value):
        translator = QtCore.QTranslator()
        if translator.load(str(LANG_DIR / f'{self.lang[1]}.qm')):
            self.parent.installTranslator(translator)

        self.custom_seed.setEnabled(value == QtCore.Qt.Checked)
        if value == QtCore.Qt.Checked:
            self.custom_seed.setText(str(random.randint(0, 0xFFFFFFFF)))
        else:
            self.custom_seed.setText(self.tr("Random"))
    
    def log_entry(self, seed, string):
        log_entry = QtWidgets.QWidget()
        log_entry_layout = QtWidgets.QHBoxLayout(log_entry)
        log_entry_layout.setContentsMargins(0, 0, 0, 0)

        message = QtWidgets.QLabel(string)
        log_entry_layout.addWidget(message)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        log_entry_layout.addWidget(line)

        globin = QtWidgets.QLabel()
        globin.setFixedWidth(16)
        globin.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        probability = 1 + (hash(seed) % 14)
        random.seed(seed + str(len(self.globin_list)))
        if random.randint(0, probability) == 0:
            match random.randint(0, 2):
                case 0: globin_icon = QtGui.QIcon(str(FILES_DIR / 'ico_spritoglobin.ico'))
                case 1: globin_icon = QtGui.QIcon(str(FILES_DIR / 'ico_cheatoglobin.ico'))
                case 2: globin_icon = QtGui.QIcon(str(FILES_DIR / 'ico_dataglobin.ico'))
        else:
            globin_icon = QtGui.QIcon(str(FILES_DIR / 'ico_randoglobin.ico'))
        globin.setPixmap(globin_icon.pixmap(16, 16))
        log_entry_layout.addWidget(globin, alignment = QtCore.Qt.AlignmentFlag.AlignRight)

        self.globin_list.append((globin, globin_icon))
        self.animating_globin = len(self.globin_list) - 1
        self.animate_globin()

        self.log.addWidget(log_entry)
        self.log_scroll_area.ensureWidgetVisible(log_entry)
    
    def animate_globin(self):
        for i, globin in enumerate(self.globin_list):
            globin_icon = globin[1]
            if i == self.animating_globin:
                anim = globin_icon.pixmap(16, 16)
                anim = anim.transformed(QtGui.QTransform().scale([
                    1,
                    0.81,
                    0.31,
                    -0.31,
                    -0.81,
                    -1,
                    -0.81,
                    -0.31,
                    0.31,
                    0.81
                ][self.globin_anim_offset], 1))
                globin[0].setPixmap(anim)
            else:
                globin[0].setPixmap(globin_icon.pixmap(16, 16))
        self.globin_anim_offset = (self.globin_anim_offset + 1) % 10
    
    def scroll_widget_to_bottom(self):
        self.log_scroll_area.verticalScrollBar().setValue(self.log_scroll_area.verticalScrollBar().maximum())
    
    def randomize(self):
        self.new_path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Save ROM",
            dir=self.new_path,
            filter=NDS_ROM_FILENAME_FILTER,
        )

        if self.new_path == '':
            return

        for i in reversed(range(self.log.count())): 
            widgetToRemove = self.log.itemAt(i).widget()
            self.log.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

        self.toggle_mute(self.muted == "True")
        
        self.thread = QtCore.QThread()
        self.worker = RandoWorker(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.log_entry)
        self.worker.finished.connect(self.celebrate)
        self.worker.failed.connect(self.uncelebrate)
        self.worker.error.connect(self.throw_error_window)
        self.thread.start()
        self.the_button.setEnabled(False)
        self.rando_start_sfx.play()

        self.globin_anim_offset = 0
        self.globin_anim_timer.start()
    
    def celebrate(self):
        self.rando_start_sfx.stop()
        self.the_button.setEnabled(True)
        self.rando_end_sfx.play()
        self.globin_anim_timer.stop()
        for globin in self.globin_list:
            globin[0].setPixmap(globin[1].pixmap(16, 16))
        self.thread.quit()
    
    def uncelebrate(self):
        self.rando_start_sfx.stop()
        self.the_button.setEnabled(True)
        self.rando_fail_sfx.play()
        self.globin_anim_timer.stop()
        for globin in self.globin_list:
            globin[0].setPixmap(globin[1].pixmap(16, 16))
        self.thread.quit()
    
    def throw_error_window(self, error_mes, seed, critical):
        err = QtWidgets.QMessageBox()
        err.setWindowTitle("Error!")
        err.setWindowIcon(QtGui.QIcon(str(FILES_DIR / 'ico_randoglobin.ico')))
        err.setText(f"{error_mes}<br><br>Seed: {seed}")
        if critical:
            err.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        else:
            err.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        err.setTextFormat(QtCore.Qt.RichText)
        err.exec()

class RandoWorker(QtCore.QObject):
    log = QtCore.Signal(str, str)
    finished = QtCore.Signal()
    failed = QtCore.Signal()
    error = QtCore.Signal(str, str, bool)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def run(self):
        try:
            translator = QtCore.QTranslator()
            if translator.load(str(LANG_DIR / f'{self.parent.lang[1]}.qm')):
                self.parent.parent.installTranslator(translator)

            write_spoiler_file = self.parent.write_spoiler.isChecked()
            if self.parent.use_custom_seed.isChecked():
                seed = self.parent.custom_seed.text()
            else:
                seed = str(random.randint(0, 0xFFFFFFFF))

            rand_special_attacks = self.parent.rand_attacks.isChecked()
            rand_treasure = self.parent.rand_treasure.isChecked()
            rand_music = self.parent.rand_music.isChecked()
            rand_colors = self.parent.rand_colors.isChecked()

            intro_skip = self.parent.intro.currentIndex()
            no_enemies = self.parent.no_enemies.isChecked()
            exp_mult = round(self.parent.exp_mult.value(), 1)
            test_target_level = self.parent.starting_level.value()

            chaos_badges = self.parent.chaos_badges.isChecked()

            unlinear = True # TO DO: add this to options

            # -----------------------------------------------------------------------------------------------------
            # import rom

            self.parent.globin_list = []
            self.log.emit(seed, "Loading ROM")
            self.rom = ndspy.rom.NintendoDSRom.fromFile(self.parent.path)
            y=y

            needs_shop_patch = rand_treasure and self.parent.treasure_settings.rando_shop.isChecked()

            needs_arm_patch = needs_shop_patch # or [other conditional here]
            if needs_arm_patch:
                self.log.emit(seed, "Applying ARM Patches")
                rom_return = apply_arm_patches(self.rom, {
                    "shop_patch": needs_shop_patch
                })
                match rom_return[0]:
                    case 0:
                        self.rom = rom_return[1]
                    case 1:
                        self.throw_error('Armips is not installed!<br>Install the armips executable from <a href="https://github.com/MnL-Modding/armips/releases">https://github.com/MnL-Modding/armips/releases</a> and place it in Randoglobin\'s "files" directory.<br><br>This may have happened due to your antivirus removing armips from the program!<br>(ROM will be exported without patches)', seed)
                    case 2:
                        self.throw_error(f"Error with armips!<br><br>== STDOUT ==<br>{rom_return[1]}<br><br>== STDERR ==<br>{rom_return[2]}<br><br>REPORT THIS TO THEPURPLEANON<br>(ROM will be exported without patches)", seed)

            self.log.emit(seed, "Extracting ROM Files")
            arm9_data = ndspy.codeCompression.decompress(self.rom.arm9)
            mfset_MenuMes = self.rom.getFileByName('MData/mfset_MenuMes.dat')
            mfset_AItmN = self.rom.getFileByName('BData/mfset_AItmN.dat')
            mfset_BadgeN = self.rom.getFileByName('BData/mfset_BadgeN.dat')
            mfset_EMesPlace = self.rom.getFileByName('EDataSave/mfset_EMesPlace.dat')
            treasure = self.rom.getFileByName('Treasure/TreasureInfo.dat')
            shops = self.rom.getFileByName('MData/MDataShopBuyList.dat')
            bobjpc_file = self.rom.getFileByName('BObjPc/BObjPc.dat')
            bobjmon_file = self.rom.getFileByName('BObjMon/BObjMon.dat')
            bobjui_file = self.rom.getFileByName('BObjUI/BObjUI.dat')
            eobjsave_file = self.rom.getFileByName('EObjSave/EObjSave.dat')
            fobj_file = self.rom.getFileByName('FObj/FObj.dat')
            fobjpc_file = self.rom.getFileByName('FObjPc/FObjPc.dat')
            fobjmon_file = self.rom.getFileByName('FObjMon/FObjMon.dat')
            mobj_file = self.rom.getFileByName('MObj/MObj.dat')
            fmap_file = self.rom.getFileByName('FMap/FMapData.dat')

            self.parent.menu_text = []
            menu_text = LanguageTable.from_bytes(mfset_MenuMes, False)
            if menu_text.text_tables[self.parent.lang[2] + 1]:
                for string in menu_text.text_tables[self.parent.lang[2] + 1].entries:
                    index = string.index(0xFF)
                    self.parent.menu_text.append(string[:index].decode(BIS_ENCODING, "ignore"))

            self.parent.attack_item_text = []
            attack_item_text = LanguageTable.from_bytes(mfset_AItmN, False)
            if attack_item_text.text_tables[self.parent.lang[2] + 1]:
                for string in attack_item_text.text_tables[self.parent.lang[2] + 1].entries:
                    index = string.index(0xFF)
                    self.parent.attack_item_text.append(string[:index].decode(BIS_ENCODING, "ignore"))

            self.parent.badge_name_text = []
            badge_name_text = LanguageTable.from_bytes(mfset_BadgeN, False)
            if badge_name_text.text_tables[self.parent.lang[2] + 1]:
                for string in badge_name_text.text_tables[self.parent.lang[2] + 1].entries:
                    index = string.index(0xFF)
                    self.parent.badge_name_text.append(string[:index].decode(BIS_ENCODING, "ignore"))

            self.parent.place_text = []
            place_text = LanguageTable.from_bytes(mfset_EMesPlace, True)
            if place_text.text_tables[self.parent.lang[2] + 0x43]:
                for string in place_text.text_tables[self.parent.lang[2] + 0x43].entries:
                    index = string.index(0xFF)
                    self.parent.place_text.append(string[:index].decode(BIS_ENCODING, "ignore"))

            self.parent.fevent_manager = FEventScriptManager(None)
            self.parent.battle_manager = BattleScriptManager(None)

            if self.rom.idCode[3] == NA_REGION_CODE or self.rom.idCode[3] == EU_REGION_CODE:                                           # US-base
                self.parent.overlays = self.rom.loadArm9Overlays()
                self.parent.overlay_field_data = self.parent.overlays[3]
                self.parent.overlay_treasure_data = self.parent.overlays[4]
                self.parent.overlay_fevent_data = self.parent.overlays[6]
                self.parent.overlay_monster_data = self.parent.overlays[11]
                self.parent.overlay_bai_data_file = self.parent.overlays[12]
                self.parent.overlay_bobj_data_group = self.parent.overlays[13]
                self.parent.overlay_bobj_data_file = self.parent.overlays[14]
                self.parent.overlay_menu_data = self.parent.overlays[123]
                self.parent.overlay_shop_data = self.parent.overlays[124]
                self.parent.overlay_eobj_data_group = self.parent.overlays[127]
                self.parent.overlay_eobj_data_file = self.parent.overlays[128]
                self.parent.overlay_map_icon_data_file = self.parent.overlays[129]
                self.parent.overlay_MObj = self.parent.overlays[132]

                self.log.emit(seed, "Parsing FEvent")
                self.parent.fevent_manager.load_overlay3(BytesIO(self.parent.overlay_field_data.data))
                self.parent.fevent_manager.load_overlay6(BytesIO(self.parent.overlay_fevent_data.data))
                FEvent = self.rom.getFileByName('FEvent/FEvent.dat')
                self.parent.fevent_manager.load_fevent(BytesIO(FEvent))

                self.log.emit(seed, "Parsing BAI")
                self.parent.battle_manager.load_overlay12(BytesIO(self.parent.overlay_bai_data_file.data))
                self.parent.battle_manager.load_overlay14(BytesIO(self.parent.overlay_bobj_data_file.data))
                bai_scn_yo = self.rom.getFileByName('BAI/BAI_scn_yo.dat')
                bai_scn_ji = self.rom.getFileByName('BAI/BAI_scn_ji.dat')
                self.parent.battle_manager.load_battle_scripts_file(0x1000, BytesIO(bai_scn_yo))
                self.parent.battle_manager.load_battle_scripts_file(0x3000, BytesIO(bai_scn_ji))

                self.parent.overlay_BObjPc_offsets = (0x8C1C, 0x6290) # filedata, palette groups
                self.parent.overlay_BObjMon_offsets = (0x9C18, 0x6610) # filedata, palette groups
                self.parent.overlay_BObjUI_offsets = (0x91C0, 0x645C) # filedata, palette groups
                self.parent.overlay_EObjSave_offsets = (0x56A4, 0x32A4) # filedata, palette groups
                self.parent.overlay_FObj_offsets = (0xE8A0, 0x150C8) # filedata, palette groups
                self.parent.overlay_FObjPc_offsets = (0xBDB0, 0x148D4) # filedata, palette groups
                self.parent.overlay_FObjMon_offsets = (0xBA3C, 0x14CCC) # filedata, palette groups
                self.parent.overlay_MObj_offsets = (0x20EC, 0x2C80) # filedata, palette groups
                self.parent.overlay_FMap_offsets = (0x11310, 0x19FD0) # filedata, map chunks

                self.rom_base = 1
            elif self.rom.idCode[3] == JP_REGION_CODE or self.rom.idCode[3] == TW_REGION_CODE or self.rom.idCode[3] == KR_REGION_CODE: # JP-base

                self.rom_base = 0

            # -----------------------------------------------------------------------------------------------------
            # modify rom

            # randomization ---------------------------------
            spoiler_file = self.tr("Seed") + f": {seed}"

            if unlinear:
                #self.log.emit(seed, "Destroying Linearity")
                self.log.emit(seed, "Skipping Tutorials") # temporary more honest log entry
                self.parent.fevent_manager = open_worldify(self.parent.fevent_manager)

            if rand_treasure:
                self.log.emit(seed, "Randomizing Treasure")

                treasure_strings = [
                    [
                        self.tr("Broque Monsieur's Item Shop"),
                        self.tr("Broggy's Gear Shop"),
                        self.tr("Badge Shop"),
                        self.tr("Toad Town Gear Shop"),
                        self.tr("Toadles Boutique"),
                        self.tr("Toad Town Star Shop"),
                        self.tr("Toad Town/Toad Square Item Shop"),
                        self.tr("Toad Square Gear Shop"),
                    ], [
                        self.tr("Available after 1 shop upgrade"),
                        self.tr("Available after 2 shop upgrades"),
                        self.tr("Available after 3 shop upgrades"),
                        self.tr("Available after 4 shop upgrades"),
                        self.tr("Available after 5 shop upgrades"),
                        self.tr("Available after 6 shop upgrades"),
                        self.tr("Available after 7 shop upgrades"),
                    ],
                    self.tr("Room"),
                    self.tr("Important Items"),
                ]

                treasure, shops, self.parent.overlay_shop_data.data, arm9_data, spoiler_file = randomize_treasure(
                    self,
                    seed,
                    self.parent.treasure_settings,
                    treasure,
                    shops,
                    BytesIO(arm9_data),
                    [0, 0x000145C0][self.rom_base],
                    [0, 0x0004E6F8][self.rom_base],
                    [0, 0x000098A0][self.rom_base],
                    self.parent.overlay_FMap_offsets[1],
                    [0, 0x0004AA30][self.rom_base],
                    [0, 0x0000864C][self.rom_base],
                    [self.parent.overlay_shop_data.data, self.parent.overlay_field_data.data, self.parent.overlay_treasure_data.data, self.parent.overlay_map_icon_data_file.data],
                    treasure_strings,
                    self.parent.place_text,
                    self.parent.badge_name_text,
                    spoiler_file,
                )

            if rand_special_attacks:
                self.log.emit(seed, "Randomizing Special Attacks")

                bros_attack_string = self.tr("Bros Attacks")
                brawl_attack_string = self.tr("Brawl Attacks")

                self.parent.overlay_menu_data.data, self.parent.fevent_manager, spoiler_file = randomize_special_attacks(
                    seed,
                    bros_attack_string,
                    self.parent.fevent_manager,
                    self.parent.overlay_menu_data.data,
                    [0, 0x000304D4][self.rom_base],
                    [0, 0x0004EA68][self.rom_base],
                    arm9_data,
                    spoiler_file,
                    [self.parent.menu_text, self.parent.attack_item_text],
                    self,
                )

            if rand_music:
                self.log.emit(seed, "Modifying Music")
                self.parent.overlay_field_data.data, self.parent.fevent_manager, self.parent.battle_manager = randomize_music(
                    seed,
                    self.parent.music_settings,
                    self.parent.overlay_field_data.data,
                    [0, 0x000098A0][self.rom_base],
                    self.parent.fevent_manager,
                    self.parent.battle_manager,
                )

            if rand_colors:
                self.log.emit(seed, "Modifying Palette")
                arm9_data, bobjpc_file, bobjmon_file, bobjui_file, eobjsave_file, fobj_file, fobjpc_file, fobjmon_file, mobj_file, fmap_file, spoiler_file, self.parent.overlay_field_data.data = randomize_colors(
                    self,
                    seed,
                    self.parent.palette_settings,
                    arm9_data,
                    [0, 0x0004C144][self.rom_base],
                    [bobjpc_file, bobjmon_file, bobjui_file],
                    [self.parent.overlay_bobj_data_file.data, self.parent.overlay_bobj_data_group.data],
                    [self.parent.overlay_BObjPc_offsets, self.parent.overlay_BObjMon_offsets, self.parent.overlay_BObjUI_offsets],
                    eobjsave_file,
                    [self.parent.overlay_eobj_data_file.data, self.parent.overlay_eobj_data_group.data],
                    self.parent.overlay_EObjSave_offsets,
                    [fobj_file, fobjpc_file, fobjmon_file],
                    [self.parent.overlay_field_data.data, self.parent.overlay_treasure_data.data],
                    [self.parent.overlay_FObj_offsets, self.parent.overlay_FObjPc_offsets, self.parent.overlay_FObjMon_offsets],
                    mobj_file,
                    self.parent.overlay_MObj.data,
                    self.parent.overlay_MObj_offsets,
                    fmap_file,
                    self.parent.overlay_FMap_offsets,
                    spoiler_file,
                    self.tr("Palette"),
                    [self.parent.battle_help_text[0x13], self.parent.battle_help_text[0x14], self.parent.battle_help_text[0x15]],
                    treasure,
                )

            if write_spoiler_file:
                self.log.emit(seed, "Writing Spoiler File")
                with open(os.path.splitext(self.parent.new_path)[0] + "_spoiler.txt", "w") as spoiler_file_w:
                    spoiler_file_w.write(spoiler_file)

            # patching --------------------------------------
            if intro_skip > 0:
                self.log.emit(seed, "Patching Intro")
                self.parent.fevent_manager = skip_intro(self.parent.fevent_manager, intro_skip == 2)

            if no_enemies:
                self.log.emit(seed, "Removing Enemies")
                self.parent.fevent_manager = remove_enemies(self.parent.fevent_manager)

            if exp_mult != 1.0:
                self.log.emit(seed, "Multiplying EXP")
                self.parent.overlay_monster_data.data = multiply_exp(
                    self.parent.overlay_monster_data.data,
                    [0, 0x0000E074][self.rom_base],
                    exp_mult,
                )

            if test_target_level > 1:
                self.log.emit(seed, "Changing Player Level")
                self.parent.fevent_manager = change_start_level(
                    self.parent.fevent_manager,
                    test_target_level,
                    arm9_data,
                    [
                        [0, 0x0004F1B8][self.rom_base],
                        [0, 0x0004ED08][self.rom_base],
                        [0, 0x0004F668][self.rom_base],
                    ]
                )

            if chaos_badges:
                self.log.emit(seed, "Randomizing Badge Combo Effects")
                arm9 = BytesIO(arm9_data)
                arm9.seek([0, 0x0004E778][self.rom_base])
                badge_list = [arm9.read(8) for i in range(16)]
                random.seed(seed)
                random.shuffle(badge_list)
                arm9.seek([0, 0x0004E778][self.rom_base])
                badge_list = [arm9.write(entry) for entry in badge_list]
                arm9.seek(0)
                arm9_data = arm9.read()

            # -----------------------------------------------------------------------------------------------------
            # export rom

            self.log.emit(seed, "Rebuilding FEvent")
            FEvent = BytesIO()
            self.parent.fevent_manager.save_fevent(FEvent)
            FEvent.seek(0)
            self.rom.setFileByName('FEvent/FEvent.dat', FEvent.read())

            self.log.emit(seed, "Rebuilding BAI")
            bai_scn_yo = BytesIO()
            bai_scn_ji = BytesIO()
            self.parent.battle_manager.save_battle_scripts_file(0x1000, bai_scn_yo)
            self.parent.battle_manager.save_battle_scripts_file(0x3000, bai_scn_ji)
            bai_scn_yo.seek(0)
            bai_scn_ji.seek(0)
            self.rom.setFileByName('BAI/BAI_scn_yo.dat', bai_scn_yo.read())
            self.rom.setFileByName('BAI/BAI_scn_ji.dat', bai_scn_ji.read())

            self.log.emit(seed, "Packing ROM")
            overlay_3 = BytesIO(self.parent.overlay_field_data.data)
            self.parent.fevent_manager.save_overlay3(overlay_3)
            overlay_3.seek(0)
            self.parent.overlay_field_data.data = overlay_3.read()

            self.rom.setFileByName('Treasure/TreasureInfo.dat', treasure)
            self.rom.setFileByName('MData/MDataShopBuyList.dat', shops)

            self.rom.setFileByName('BObjPc/BObjPc.dat', bobjpc_file)
            self.rom.setFileByName('BObjMon/BObjMon.dat', bobjmon_file)
            self.rom.setFileByName('BObjUI/BObjUI.dat', bobjui_file)
            self.rom.setFileByName('EObjSave/EObjSave.dat', eobjsave_file)
            self.rom.setFileByName('FObj/FObj.dat', fobj_file)
            self.rom.setFileByName('FObjPc/FObjPc.dat', fobjpc_file)
            self.rom.setFileByName('FObjMon/FObjMon.dat', fobjmon_file)
            self.rom.setFileByName('MObj/MObj.dat', mobj_file)
            self.rom.setFileByName('FMap/FMapData.dat', fmap_file)

            if self.rom_base == 1:
                self.rom.files[self.parent.overlays[3].fileID] = self.parent.overlay_field_data.save(compress = True)
                self.rom.files[self.parent.overlays[6].fileID] = self.parent.overlay_fevent_data.save(compress = True)
                self.rom.files[self.parent.overlays[11].fileID] = self.parent.overlay_monster_data.save(compress = True)
                self.rom.files[self.parent.overlays[123].fileID] = self.parent.overlay_menu_data.save(compress = True)
                self.rom.files[self.parent.overlays[124].fileID] = self.parent.overlay_shop_data.save(compress = True)
            else:
                pass

            banner = BytesIO(self.rom.iconBanner)
            with open(str(FILES_DIR / 'dat_icon.dat'), 'rb') as icon_file:
                banner.seek(0x20)
                banner.write(icon_file.read())
            for i in range(0x240, 0x840, 0x100):
                banner.seek(i)
                banner.write("Bowser's Inside Story\n(Randomized)\nNintendo / Randoglobin".encode('utf-16'))

            banner.seek(0)
            self.rom.iconBanner = banner.read()

            if self.rom_base == 1:
                self.rom.arm9 = ndspy.code.MainCodeFile(arm9_data, self.rom.arm9RamAddress, self.rom.arm9CodeSettingsPointerAddress).save(compress = True)
            else:
                pass
            self.rom.arm9OverlayTable = ndspy.code.saveOverlayTable(self.parent.overlays)

            if random.randrange(0, 10) == 4:
                self.log.emit(seed, "Reticulating splines")
            self.rom.saveToFile(self.parent.new_path)

            self.log.emit(seed, "Complete!")
            self.finished.emit()
        except Exception as e:
            string = traceback.format_exc().replace("\n", "<br>")

            self.throw_error(f'An exception has occurred!<br><br>Traceback:<pre>{string}</pre>', seed)
            self.log.emit(seed, "Failed...")
            self.failed.emit()
    
    def throw_error(self, error_mes, seed, critical = True):
        self.error.emit(error_mes, seed, critical)
