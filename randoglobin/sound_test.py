import yaml
from functools import partial

from PySide6 import QtCore, QtGui, QtMultimedia, QtWidgets

from randoglobin.constants import *
from randoglobin.image import generate_sprites_from_sheet

class SoundTest(QtWidgets.QDialog):
    closed = QtCore.Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle(self.tr("Sound Test"))
        self.setWindowIcon(QtGui.QIcon(str(FILES_DIR / 'ico_randoglobin.ico')))

        self.sound_player = QtMultimedia.QSoundEffect(self)
        self.sound_player.setVolume(0.5)
        self.loop_timer = QtCore.QTimer(self)
        self.loop_timer.timeout.connect(self.start_dance_loop)
        self.dance_timer = QtCore.QTimer(self)
        self.dance_timer.timeout.connect(self.dance_update)

        with open(str(FILES_DIR / 'randodance_randoglobin.yaml')) as file:
            self.dance_data = yaml.safe_load(file)

        self.sprite_size = (self.dance_data.get('sprite_width'), self.dance_data.get('sprite_height'))
        self.sprite_num = self.dance_data.get('sprite_amount')
        self.sprite_scale = self.dance_data.get('sprite_scale')
        self.background_sprite = self.dance_data.get('background_sprite', None)
        self.idle_dance = self.dance_data.get('idle_dance', '')
        self.framerate = self.dance_data.get('framerate')
        self.dance_sprites = generate_sprites_from_sheet(str(FILES_DIR / self.dance_data.get('sprite_sheet')), self.sprite_num, self.sprite_size)
        self.running_timers = []

        main_layout = QtWidgets.QGridLayout(self)

        self.track_info = QtWidgets.QLabel()
        self.track_info.setTextFormat(QtCore.Qt.TextFormat.RichText) # if i ever allow users to use their own randodance files i need to sanitize the fuck out of this
        self.track_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.track_info, 1, 0, 1, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.sound_list = QtWidgets.QListWidget()
        self.sound_list.currentRowChanged.connect(self.update_track_info)
        self.sound_list.itemDoubleClicked.connect(self.play_sound)
        self.sound_internals = []
        for sound in self.dance_data['sounds']:
            if sound == self.idle_dance: continue

            self.sound_internals.append(sound)
            sound_name = self.dance_data['sounds'][sound].get('name', "???")
            sound_credit = self.dance_data['sounds'][sound].get('credit', None)
            sound_icon = self.dance_data['sounds'][sound].get('icon', "img_mus.png")

            sound_widget = QtWidgets.QListWidgetItem()
            sound_widget.setText(sound_name)
            sound_widget.setIcon(QtGui.QIcon(str(FILES_DIR / sound_icon)))
            self.sound_list.addItem(sound_widget)
        main_layout.addWidget(self.sound_list, 0, 0, 1, 2)

        play_button = QtWidgets.QPushButton(self.tr("Play"))
        play_button.clicked.connect(self.play_sound)
        main_layout.addWidget(play_button, 2, 0)

        stop_button = QtWidgets.QPushButton(self.tr("Stop"))
        stop_button.clicked.connect(self.stop_sound)
        main_layout.addWidget(stop_button, 2, 1)

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line, 3, 0, 1, 2)
        # ------------------------------------------

        self.rando_dancer = QtWidgets.QLabel()
        self.rando_dancer.setFixedSize(self.sprite_size[0] * self.sprite_scale, self.sprite_size[1] * self.sprite_scale)
        main_layout.addWidget(self.rando_dancer, 4, 0, 1, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        artist = self.dance_data.get('art_credit', None)
        dance_file_creator = self.dance_data.get('randodance_credit', None)
        if artist or dance_file_creator:
            dance_info_widget = QtWidgets.QLabel()
            dance_info_widget.setTextFormat(QtCore.Qt.TextFormat.RichText) # again, definitely need to sanitize this like crazy
            dance_info_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            dance_info_string_0 = self.tr("Dancer Sprites by:")
            dance_info_string_1 = self.tr("Dancer Scripting by:")

            dance_info = ""
            if artist:
                dance_info += f"{dance_info_string_0} {artist}"
            
            if dance_file_creator:
                if dance_info != "": dance_info += "<br>"
                dance_info += f"{dance_info_string_1} {dance_file_creator}"

            dance_info_widget.setText('<span style="color: rgb(127, 127, 127); font-size: 11px;">' + dance_info + '</span')
            main_layout.addWidget(dance_info_widget, 5, 0, 1, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        if self.idle_dance != "":
            current_sound_data = self.dance_data['sounds'].get(self.idle_dance)
            self.start_dance(current_sound_data)
    
    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
    
    def update_track_info(self):
        sound = self.sound_internals[self.sound_list.currentRow()]

        sound_name = self.dance_data['sounds'][sound].get('name', "???")
        sound_credit = self.dance_data['sounds'][sound].get('credit', None)
        sound_icon = self.dance_data['sounds'][sound].get('icon', "img_mus.png")

        info_string = f'<img src="{str(FILES_DIR / sound_icon)}" alt="{sound_name}" style="vertical-align: middle;"> {sound_name}'
        if sound_credit: info_string += f'<br><span style="color: rgb(127, 127, 127); font-size: 11px;">{sound_credit}</span>'

        self.track_info.setText(info_string)

    def play_sound(self):
        self.stop_sound()

        sound = self.sound_internals[self.sound_list.currentRow()]
        current_sound_data = self.dance_data['sounds'].get(sound)

        self.sound_player.setSource('')
        self.sound_player.setSource(QtCore.QUrl.fromLocalFile(FILES_DIR / current_sound_data.get('filename', 'snd_randoglobin_fail.wav')))

        if current_sound_data.get('loop'):
            self.sound_player.setLoopCount(-2)
        else:
            self.sound_player.setLoopCount(0)
        self.sound_player.play()

        self.start_dance(current_sound_data)

    def start_dance(self, current_sound_data):
        for timer in self.running_timers:
            timer.stop()
            timer.deleteLater()
        self.running_timers = []

        self.dance_timer.stop()
        self.loop_timer.stop()

        current_dance_data = self.dance_data['dances']

        self.current_tempo = current_sound_data.get('tempo', 120) * current_sound_data.get('subdiv', 1)

        self.current_dance = []

        dance_loops = current_sound_data.get('dance', None)
        if dance_loops:
            for dance_loop in dance_loops.split(' '):
                dance, loop_num = dance_loop.split(';')
                dance_data = str(current_dance_data.get(dance))

                frames = dance_data.split(' ')

                for i in range(int(loop_num)):
                    for frame in frames:
                        if ";" in frame:
                            sprite, anim = frame.split(';')
                        else:
                            sprite = frame
                            anim = ''
                        self.current_dance.append((sprite, anim))

            if current_sound_data.get('loop', False):
                self.loop_timer.start(current_sound_data.get('length') * 1000)

            self.start_dance_loop()
    
    def stop_sound(self):
        for timer in self.running_timers:
            timer.stop()
            timer.deleteLater()
        self.running_timers = []

        self.sound_player.stop()
        self.dance_timer.stop()
        self.loop_timer.stop()

        if self.idle_dance != "":
            current_sound_data = self.dance_data['sounds'].get(self.idle_dance)
            self.start_dance(current_sound_data)
    
    def start_dance_loop(self):
        self.anim_timer = 0

        self.dance_update()
        if len(self.current_dance) > 1:
            self.dance_timer.start(60000 / self.current_tempo)
    
    def dance_update(self):
        dance_frame = self.current_dance[self.anim_timer]
        self.draw_image_with_offset(dance_frame[0])

        if dance_frame[1] != '':
            anim = self.dance_data['animations'].get(dance_frame[1], '')

            x_offsets = anim.get('x_offset_list', [])
            y_offsets = anim.get('y_offset_list', [])

            if x_offsets != []: x_offsets = x_offsets.split(',')
            if y_offsets != []: y_offsets = y_offsets.split(',')

            self.dance_anim(dance_frame[0], x_offsets, y_offsets)

        self.anim_timer += 1
        if self.anim_timer == len(self.current_dance):
            self.dance_timer.stop()
    
    def dance_anim(self, sprite, x_offset_list, y_offset_list):
        for timer in self.running_timers:
            timer.stop()
            timer.deleteLater()
        self.running_timers = []

        if len(x_offset_list) > len(y_offset_list):
            y_offset_list.extend([0] * (len(x_offset_list) - len(y_offset_list)))
        else:
            x_offset_list.extend([0] * (len(y_offset_list) - len(x_offset_list)))

        for i in range(len(x_offset_list)):
            timer = QtCore.QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(partial(self.draw_image_with_offset, sprite, int(x_offset_list[i]), int(y_offset_list[i])))
            timer.start(i * (1000 / self.framerate))
            self.running_timers.append(timer)
        
    def draw_image_with_offset(self, sprite, offset_x = 0, offset_y = 0):
        pixmap = QtGui.QPixmap(*self.sprite_size)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)

        if self.background_sprite:
            painter.drawPixmap(0, 0, self.dance_sprites[self.background_sprite])
        
        shadow = self.dance_data['images'][sprite].get('shadow', None)
        if shadow:
            shadow_offset_x = self.dance_data['images'][sprite].get('shadow_offset_x', 0)
            shadow_offset_y = self.dance_data['images'][sprite].get('shadow_offset_y', 0)
            painter.drawPixmap(offset_x + shadow_offset_x, shadow_offset_y, self.dance_sprites[shadow])
        
        sprite_id = self.dance_data['images'][sprite].get('sprite')
        painter.drawPixmap(offset_x, offset_y, self.dance_sprites[sprite_id])
        painter.end()
        self.rando_dancer.setPixmap(pixmap.transformed(QtGui.QTransform().scale(self.sprite_scale, self.sprite_scale)))