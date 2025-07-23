import random
from io import BytesIO
from PySide6 import QtCore, QtGui, QtWidgets

from mnllib import CodeCommand

from randoglobin.data_classes import MapMetadata
from randoglobin.constants import *

# =========================================================================================================================

def randomize_music(seed, settings, overlay_data, map_metadata_offset, fevent_manager, battle_manager):
    random.seed(seed)
    double_map_music = []
    single_map_music = []

    overlay_data = BytesIO(overlay_data)
    overlay_data.seek(map_metadata_offset)
    for i in range(0x2A9):
        current_map = MapMetadata(overlay_data.read(12))
        if current_map.music in VALID_DOUBLE_TRACKS and not (current_map.music, current_map.select_map) in double_map_music:
            double_map_music.append((current_map.music, current_map.select_map))
        elif current_map.music in VALID_SINGLE_TRACKS and not (current_map.music, current_map.select_map) in single_map_music:
            single_map_music.append((current_map.music, current_map.select_map))

    # field music
    single_music_tracks = []
    if len(settings.cutscene_music_list) > 0:
        for i in single_map_music:
            single_music_tracks.append(random.choice(settings.cutscene_music_list))

    double_music_tracks = []
    if len(settings.overworld_music_list) > 0:
        for i in double_map_music:
            music_choice = random.choice(settings.overworld_music_list)
            double_music_tracks.append(music_choice)

    if settings.affect_overworld.isChecked():
        overlay_data.seek(map_metadata_offset)
        for i in range(0x2A9):
            current_map = MapMetadata(overlay_data.read(12))

            if (current_map.music, current_map.select_map) in double_map_music and len(double_music_tracks) > 0:
                current_map.music = double_music_tracks[double_map_music.index((current_map.music, current_map.select_map))]
            elif (current_map.music, current_map.select_map) in single_map_music and len(single_music_tracks) > 0:
                current_map.music = single_music_tracks[single_map_music.index((current_map.music, current_map.select_map))]

            overlay_data.seek(-12, 1)
            overlay_data.write(current_map.pack())

        for i, chunk_triple in enumerate(fevent_manager.fevent_chunks):
            chunk = chunk_triple[0]
            for subroutine in chunk.subroutines:
                for command in subroutine.commands:
                    if isinstance(command, CodeCommand) and command.command_id == 0x01D3:
                        match (i, command.arguments[1]): # i hate this
                            case (0x032, 0x33): command.arguments[1] = double_music_tracks[double_map_music.index(( 0x33, 0x1ED))]
                            case (0x039, 0x32): command.arguments[1] = double_music_tracks[double_map_music.index(( 0x31,  0x44))] + 1
                            case (0x03A, 0x34): command.arguments[1] = double_music_tracks[double_map_music.index(( 0x33, 0x1ED))] + 1
                            case (0x12E, 0x3B): command.arguments[1] = double_music_tracks[double_map_music.index(( 0x3A, 0x263))] + 1
                            case (0x15D, 0x42): command.arguments[1] = double_music_tracks[double_map_music.index(( 0x42, 0x263))]
                            case (0x1F9, 0x39): command.arguments[1] = double_music_tracks[double_map_music.index(( 0x38, 0x261))] + 1
                            case (0x1FB, 0x42): command.arguments[1] = double_music_tracks[double_map_music.index(( 0x42, 0x263))]
                            case (0x1FB, 0x43): command.arguments[1] = double_music_tracks[double_map_music.index(( 0x42, 0x263))] + 1
                            case (0x252, 0x44): command.arguments[1] = double_music_tracks[double_map_music.index(( 0x44, 0x265))]
    
    if settings.affect_cutscenes.isChecked() and len(settings.cutscene_music_list) > 0:
        for chunk_triple in fevent_manager.fevent_chunks:
            chunk = chunk_triple[0]
            for subroutine in chunk.subroutines:
                for command in subroutine.commands:
                    if isinstance(command, CodeCommand) and command.command_id == 0x01D3 and command.arguments[1] in VALID_SINGLE_TRACKS:
                        command.arguments[1] = random.choice(settings.cutscene_music_list)
    
    # battle music
    if settings.affect_battles.isChecked() and len(settings.battle_music_list) > 0:
        for file in [0x1000, 0x3000]:
            for i, script in enumerate(battle_manager.battle_scripts_files[file]):
                if i + file == 0x1079 and not settings.affect_final_boss.isChecked():
                    continue
                for i, command in enumerate(script.main_subroutine.commands):
                    if command.command_id == 0x201 and command.arguments[0] in VALID_BATTLE_TRACKS:
                        music_choice = random.choice(settings.battle_music_list)
                        command.arguments[0] = music_choice
                        script.main_subroutine.commands[i + 1].arguments[0] = music_choice

    overlay_data.seek(0)
    return overlay_data.read(), fevent_manager, battle_manager

# =========================================================================================================================

VALID_DOUBLE_TRACKS = [
    0x31, # plack beach
    0x33, # dimble wood
    0x35, # bowser castle
    0x38, # deep castle
    0x3A, # bowser path
    0x3C, # bowser path 2 (fuck you game devs)
    0x42, # cavi cape cave
    0x44, # peach's castle gardens
    0x48, # bumpsy plains
    0x4A, # blubble lake
    0x53, # toad town
]

VALID_DOUBLE_TRACKS_PRESET = [
    0x31, # plack beach
    0x33, # dimble wood
    0x35, # bowser castle
    0x38, # deep castle
    0x3A, # bowser path
    0x42, # cavi cape cave
    0x44, # peach's castle gardens
    0x48, # bumpsy plains
    0x4A, # blubble lake
    0x53, # toad town
]



VALID_SINGLE_TRACKS = [
    0x37, # panic theme
    0x3E, # file select
    0x3F, # fawful's evil plan
    0x40, # fawful is there
    0x41, # bowser's theme
    0x46, # toadley's clinic
    0x47, # peach's castle
    0x4C, # charles block theme
    0x4D, # block waifu theme
    0x50, # dark bowser theme
    0x51, # shock theme
    0x52, # tutorial theme
]

VALID_SINGLE_TRACKS_PRESET = [
    0x37, # panic theme
    0x3F, # fawful's evil plan
    0x40, # fawful is there
    0x41, # bowser's theme
    0x46, # toadley's clinic
    0x47, # peach's castle
    0x4C, # charles block theme
    0x4D, # block waifu theme
    0x50, # dark bowser theme
    0x51, # shock theme
    0x52, # tutorial theme
]



VALID_BATTLE_TRACKS = [
    0x5A, # last boss
    0x4E, # minigame
    0x55, # oki doki
    0x56, # tough guy
    0x57, # showtime
    0x58, # giant
    0x5D, # title theme
    0x5E, # the end
]

VALID_BATTLE_TRACKS_PRESET = [
    0x4E, # minigame
    0x55, # oki doki
    0x56, # tough guy
    0x57, # showtime
    0x58, # giant
]

# TO DO: add a randomization subroutine to graft into battles to randomize music per-battle

###############################################################################################################################################
###############################################################################################################################################
###############################################################################################################################################

class MusicTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.set_constants()

        self.overworld_music_list = VALID_DOUBLE_TRACKS_PRESET
        self.cutscene_music_list = VALID_SINGLE_TRACKS_PRESET
        self.battle_music_list = VALID_BATTLE_TRACKS_PRESET

        main_layout = QtWidgets.QVBoxLayout(self)

        self.affect_final_boss = QtWidgets.QCheckBox(self.tr("Randomize Final Boss Music"))
        main_layout.addWidget(self.affect_final_boss, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.affect_final_boss.setIcon(QtGui.QIcon(str(FILES_DIR / 'img_mus_dk.png')))

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)
        # ------------------------------------------

        music_lists = QtWidgets.QWidget()
        music_lists_layout = QtWidgets.QGridLayout(music_lists)
        music_lists_layout.setAlignment(QtCore.Qt.AlignTop)
        music_lists_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(3):
            music_lists_layout.setColumnStretch(i, 1)
        main_layout.addWidget(music_lists)

        self.affect_overworld = QtWidgets.QCheckBox(self.tr("Randomize Overworld"))
        music_lists_layout.addWidget(self.affect_overworld, 0, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.affect_cutscenes = QtWidgets.QCheckBox(self.tr("Randomize Cutscenes"))
        music_lists_layout.addWidget(self.affect_cutscenes, 0, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.affect_battles = QtWidgets.QCheckBox(self.tr("Randomize Battles"))
        music_lists_layout.addWidget(self.affect_battles, 0, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.affect_overworld.setCheckState(QtCore.Qt.CheckState.Checked)
        self.affect_cutscenes.setCheckState(QtCore.Qt.CheckState.Checked)
        self.affect_battles.setCheckState(QtCore.Qt.CheckState.Checked)
        self.affect_overworld.checkStateChanged.connect(self.update_lists)
        self.affect_cutscenes.checkStateChanged.connect(self.update_lists)
        self.affect_battles.checkStateChanged.connect(self.update_lists)

        self.music_list_boxes = [None, None, None]
        for i in range(3):
            string = QtWidgets.QLabel([
                self.tr("Overworld Music Whitelist") + f" <html><img src='{str(FILES_DIR / 'img_mus_g.png')}' align='top'></html>",
                self.tr("Cutscene Music Whitelist") + f" <html><img src='{str(FILES_DIR / 'img_mus_y.png')}' align='top'></html>",
                self.tr("Battle Music Whitelist") + f" <html><img src='{str(FILES_DIR / 'img_mus_r.png')}' align='top'></html>"][i])
            music_lists_layout.addWidget(string, 1, i, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

            self.music_list_boxes[i] = QtWidgets.QListWidget()
            self.music_list_boxes[i].setSizeAdjustPolicy(QtWidgets.QListWidget.SizeAdjustPolicy.AdjustToContents)
            self.music_list_boxes[i].setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            music_lists_layout.addWidget(self.music_list_boxes[i], 2, i)

            string.setBuddy(self.music_list_boxes[i])


        for entry in self.DOUBLE_TRACKS_NAMES:
            self.music_list_boxes[0].addItem(QtWidgets.QListWidgetItem(QtGui.QIcon(str(FILES_DIR / 'img_mus_g.png')), entry))
        self.overworld_list_meta = VALID_DOUBLE_TRACKS

        for i in range(self.music_list_boxes[0].count()):
            self.music_list_boxes[0].item(i).setCheckState(QtCore.Qt.Unchecked)
        for track in self.overworld_music_list:
            self.music_list_boxes[0].item(self.overworld_list_meta.index(track)).setCheckState(QtCore.Qt.Checked)


        for entry in self.SINGLE_TRACKS_NAMES:
            self.music_list_boxes[1].addItem(QtWidgets.QListWidgetItem(QtGui.QIcon(str(FILES_DIR / 'img_mus_y.png')), entry))
        for entry in self.DOUBLE_TRACKS_NAMES:
            self.music_list_boxes[1].addItem(QtWidgets.QListWidgetItem(QtGui.QIcon(str(FILES_DIR / 'img_mus_g.png')), entry + " - " + self.TRACK_QUALIFIERS[0]))
            self.music_list_boxes[1].addItem(QtWidgets.QListWidgetItem(QtGui.QIcon(str(FILES_DIR / 'img_mus_g_inv.png')), entry + " - " + self.TRACK_QUALIFIERS[1]))
        double_track_meta = [[track, track + 1] for track in VALID_DOUBLE_TRACKS]
        self.cutscene_list_meta = VALID_SINGLE_TRACKS + [item for sublist in [[track, track + 1] for track in VALID_DOUBLE_TRACKS] for item in sublist] # fugly but works

        for i in range(self.music_list_boxes[1].count()):
            self.music_list_boxes[1].item(i).setCheckState(QtCore.Qt.Unchecked)
        for track in self.cutscene_music_list:
            self.music_list_boxes[1].item(self.cutscene_list_meta.index(track)).setCheckState(QtCore.Qt.Checked)


        for i, entry in enumerate(self.BATTLE_TRACKS_NAMES):
            if i > 0:
                self.music_list_boxes[2].addItem(QtWidgets.QListWidgetItem(QtGui.QIcon(str(FILES_DIR / 'img_mus_r.png')), entry))
            else:
                self.music_list_boxes[2].addItem(QtWidgets.QListWidgetItem(QtGui.QIcon(str(FILES_DIR / 'img_mus_dk.png')), entry))
        for entry in self.SINGLE_TRACKS_NAMES:
            self.music_list_boxes[2].addItem(QtWidgets.QListWidgetItem(QtGui.QIcon(str(FILES_DIR / 'img_mus_y.png')), entry))
        for entry in self.DOUBLE_TRACKS_NAMES:
            self.music_list_boxes[2].addItem(QtWidgets.QListWidgetItem(QtGui.QIcon(str(FILES_DIR / 'img_mus_g.png')), entry + " - " + self.TRACK_QUALIFIERS[0]))
            self.music_list_boxes[2].addItem(QtWidgets.QListWidgetItem(QtGui.QIcon(str(FILES_DIR / 'img_mus_g_inv.png')), entry + " - " + self.TRACK_QUALIFIERS[1]))
        double_track_meta = [[track, track + 1] for track in VALID_DOUBLE_TRACKS]
        self.battle_list_meta = VALID_BATTLE_TRACKS + VALID_SINGLE_TRACKS + [item for sublist in [[track, track + 1] for track in VALID_DOUBLE_TRACKS] for item in sublist] # fugly but works
        
        for i in range(self.music_list_boxes[2].count()):
            self.music_list_boxes[2].item(i).setCheckState(QtCore.Qt.Unchecked)
        for track in self.battle_music_list:
            self.music_list_boxes[2].item(self.battle_list_meta.index(track)).setCheckState(QtCore.Qt.Checked)

        
        for i in range(3):
            self.music_list_boxes[i].itemChanged.connect(self.update_lists)

    def update_lists(self, item):
        self.music_list_boxes[0].setEnabled(self.affect_overworld.isChecked())
        self.music_list_boxes[1].setEnabled(self.affect_cutscenes.isChecked())
        self.music_list_boxes[2].setEnabled(self.affect_battles.isChecked())

        if isinstance(item, QtCore.Qt.CheckState):
            for i in range(3):
                if not self.music_list_boxes[i].isEnabled():
                    self.music_list_boxes[i].setCurrentRow(-1)
            return

        test = item.checkState()
        i = self.music_list_boxes.index(item.listWidget())
        self.music_list_boxes[i].blockSignals(True)

        if item in self.music_list_boxes[i].selectedItems():
            for j in range(self.music_list_boxes[i].count()):
                if self.music_list_boxes[i].item(j) in self.music_list_boxes[i].selectedItems():
                    if test == QtCore.Qt.CheckState.Checked:
                        self.music_list_boxes[i].item(j).setCheckState(QtCore.Qt.CheckState.Checked)
                    else:
                        self.music_list_boxes[i].item(j).setCheckState(QtCore.Qt.CheckState.Unchecked)
        else:
            if test == QtCore.Qt.CheckState.Checked:
                item.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                item.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.music_list_boxes[i].blockSignals(False)
        
        self.overworld_music_list = []
        for i in range(self.music_list_boxes[0].count()):
            if self.music_list_boxes[0].item(i).checkState() == QtCore.Qt.CheckState.Checked:
                self.overworld_music_list.append(self.overworld_list_meta[i])

        self.cutscene_music_list = []
        for i in range(self.music_list_boxes[1].count()):
            if self.music_list_boxes[1].item(i).checkState() == QtCore.Qt.CheckState.Checked:
                self.cutscene_music_list.append(self.cutscene_list_meta[i])

        self.battle_music_list = []
        for i in range(self.music_list_boxes[2].count()):
            if self.music_list_boxes[2].item(i).checkState() == QtCore.Qt.CheckState.Checked:
                self.battle_music_list.append(self.battle_list_meta[i])

    def set_constants(self):
        self.TRACK_QUALIFIERS = [
            self.tr("Outside"),
            self.tr("Inside"),
        ]

        self.DOUBLE_TRACKS_NAMES = [
            self.tr("Plack Beach"),
            self.tr("Dimble Wood"),
            self.tr("Bowser Castle"),
            self.tr("Peach's Castle"),
            self.tr("Bowser Path"),
            self.tr("Tunnel"),
            self.tr("Cavi Cape Cave"),
            self.tr("Peach's Castle Gardens"),
            self.tr("Bumpsy Plains"),
            self.tr("Blubble Lake"),
            self.tr("Toad Town"),
        ]
        
        self.SINGLE_TRACKS_NAMES = [
            self.tr("Danger!"),
            self.tr("File Select"),
            self.tr("Fawful's Evil Plan"),
            self.tr("Fawful is There"),
            self.tr("Bowser!"),
            self.tr("Dr. Toadley"),
            self.tr("Peach's Castle (Intro)"),
            self.tr("Have a Nice Talk"),
            self.tr("Have a Sweet Talk"),
            self.tr("Dark Bowser!"),
            self.tr("Shock!"),
            self.tr("Tutorial Time"),
        ]

        self.BATTLE_TRACKS_NAMES = [
            self.tr("In The Final"),
            self.tr("Minigame"),
            self.tr("Oki Doki!"),
            self.tr("Tough Guy Alert"),
            self.tr("SHOWTIME!"),
            self.tr("The Giant"),
            self.tr("Title Theme"),
            self.tr("The End"),
        ]