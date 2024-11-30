import sys
import random
import json
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton, QStackedWidget, QMenu, QFrame
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import QTimer, QRectF, Qt

class Cabbage:
    def __init__(self, window_width, window_height):
        self.x = random.randint(50, window_width - 50)
        self.y = random.randint(50, window_height - 50)
        self.size = random.randint(10, 30)
        self.nutrition = self.size * 2
        self.being_eaten = False

    def is_eaten(self):
        return self.size <= 0

class Goat:
    def __init__(self, window_width, window_height):
        self.x = random.randint(50, window_width - 50)
        self.y = random.randint(50, window_height - 50)
        self.size = 20
        self.speed = random.uniform(1.0, 3.0)
        self.eating_speed = random.uniform(1.0, 3.0)
        self.eating = False
        self.moving = True
        self.stamina = 100
        self.target_cabbage = None
        self.wander_direction = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.steps_in_direction = 0
        self.fertility = random.uniform(0.1, 1.0)

    def move_towards(self, target_x, target_y):
        direction_x = target_x - self.x
        direction_y = target_y - self.y
        distance = (direction_x ** 2 + direction_y ** 2) ** 0.5

        if distance > 0:
            self.x += (direction_x / distance) * self.speed
            self.y += (direction_y / distance) * self.speed

    def is_near_cabbage(self, cabbage):
        goat_left = self.x
        goat_right = self.x + self.size
        goat_top = self.y
        goat_bottom = self.y + self.size

        cabbage_left = cabbage.x
        cabbage_right = cabbage.x + cabbage.size
        cabbage_top = cabbage.y
        cabbage_bottom = cabbage.y + cabbage.size

        overlaps_horizontally = goat_right >= cabbage_left and goat_left <= cabbage_right
        overlaps_vertically = goat_bottom >= cabbage_top and goat_top <= cabbage_bottom
        
        return overlaps_horizontally and overlaps_vertically

    def wander(self, window_width, window_height):
        if self.steps_in_direction >= random.randint(30, 60):
            self.wander_direction = [random.choice([-1, 1]), random.choice([-1, 1])]
            self.steps_in_direction = 0

        self.x += self.wander_direction[0] * self.speed
        self.y += self.wander_direction[1] * self.speed

        self.x = max(0, min(self.x, window_width - self.size))
        self.y = max(0, min(self.y, window_height - self.size))

        self.steps_in_direction += 1


class TheGame(QWidget):
    def __init__(self, config_file='config.json'):
        super().__init__()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_file)

        if not os.path.exists(config_path):
            default_config = {
                "window_width": 1500,
                "window_height": 800,
                "num_goats": 10,
                "num_cabbages": 20,
                "cabbage_generation_choices": [1, 2, 3, 4   ]
            }
            with open(config_path, 'w') as file:
                json.dump(default_config, file, indent=4)

        with open(config_path, 'r') as file:
            config = json.load(file)

        self.window_width = config["window_width"]
        self.window_height = config["window_height"]
        
        num_goats = config["num_goats"]
        num_cabbages = config["num_cabbages"]
        self.cabbage_generation_choices = config["cabbage_generation_choices"]

        self.cabbages = [Cabbage(self.window_width, self.window_height) for _ in range(num_cabbages)]
        self.goats = [Goat(self.window_width, self.window_height) for _ in range(num_goats)]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(60)

        self.cabbage_timer = QTimer(self)
        self.cabbage_timer.timeout.connect(self.generate_new_cabbage)
        self.cabbage_timer.start(3000)

        self.paused = False
        self.hovered_cabbage = None
        self.hovered_goat = None

        self.setMouseTracking(True)

        self.init_settings_button()
        self.init_settings_window()

        self.setWindowTitle('Огород')

        self.setGeometry(100, 100, self.window_width, self.window_height)
        self.show()


    def init_settings_window(self):
        margin = 50
        self.settings_window = QWidget(self)
        self.settings_window.setGeometry(
            margin,
            margin,
            self.window_width - 2 * margin,
            self.window_height - 2 * margin
        )
        self.settings_window.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self.settings_window.setStyleSheet("""
            background-color: #fefefe;
            border-radius: 12px;
            border: 2px solid #D1D1D1;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            padding: 15px;
        """)

        layout = QVBoxLayout()

        class CustomSlider(QSlider):
            def __init__(self, orientation):
                super().__init__(orientation)
                self.setStyleSheet("""
            QSlider{
                background: #E3DEE2;
            }
            QSlider::groove:horizontal {  
                height: 10px;
                margin: 0px;
                border-radius: 5px;
                background: #B0AEB1;
            }
            QSlider::handle:horizontal {
                background: #fff;
                border: 1px solid #E3DEE2;
                width: 17px;
                margin: -5px 0; 
                border-radius: 8px;
            }
            QSlider::sub-page:qlineargradient {
                background: #3B99FC;
                border-radius: 5px;
            }
        """)

        cabbage_label = QLabel("Размер капусты")
        cabbage_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")
        self.cabbage_size_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.cabbage_size_slider.setMinimum(1)
        self.cabbage_size_slider.setMaximum(100)
        self.cabbage_size_slider.setValue(20)
        cabbage_value_label = QLabel(f"{self.cabbage_size_slider.value()}")
        cabbage_value_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")

        self.cabbage_size_slider.valueChanged.connect(
            lambda: cabbage_value_label.setText(f"{self.cabbage_size_slider.value()}")
        )
        layout.addWidget(cabbage_label)
        layout.addWidget(self.cabbage_size_slider)
        layout.addWidget(cabbage_value_label)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #ff0000; height: 2px; margin: 10px 0;")
        layout.addWidget(separator)

        goat_label = QLabel("Размер стада")
        goat_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")
        self.goat_size_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.goat_size_slider.setMinimum(10)
        self.goat_size_slider.setMaximum(100)
        self.goat_size_slider.setValue(20)
        goat_value_label = QLabel(f"{self.goat_size_slider.value()}")
        goat_value_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")

        self.goat_size_slider.valueChanged.connect(
            lambda: goat_value_label.setText(f"{self.goat_size_slider.value()}")
        )
        layout.addWidget(goat_label)
        layout.addWidget(self.goat_size_slider)
        layout.addWidget(goat_value_label)

        fertility_label = QLabel("Плодовитость стада")
        fertility_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")
        self.goat_fertility_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.goat_fertility_slider.setMinimum(1)
        self.goat_fertility_slider.setMaximum(5)
        self.goat_fertility_slider.setValue(1)
        fertility_value_label = QLabel(f"{self.goat_fertility_slider.value()}")
        fertility_value_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")

        self.goat_fertility_slider.valueChanged.connect(
            lambda: fertility_value_label.setText(f"{self.goat_fertility_slider.value()}")
        )
        layout.addWidget(fertility_label)
        layout.addWidget(self.goat_fertility_slider)
        layout.addWidget(fertility_value_label)

        stamina_label = QLabel("Стамина стада")
        stamina_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")
        self.goat_stamina_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.goat_stamina_slider.setMinimum(50)
        self.goat_stamina_slider.setMaximum(150)
        self.goat_stamina_slider.setValue(100)
        stamina_value_label = QLabel(f"{self.goat_stamina_slider.value()}")
        stamina_value_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")

        self.goat_stamina_slider.valueChanged.connect(
            lambda: stamina_value_label.setText(f"{self.goat_stamina_slider.value()}")
        )
        layout.addWidget(stamina_label)
        layout.addWidget(self.goat_stamina_slider)
        layout.addWidget(stamina_value_label)

        eating_speed_label = QLabel("Скорость поедания стада")
        eating_speed_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")
        self.goat_eating_speed_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.goat_eating_speed_slider.setMinimum(1)
        self.goat_eating_speed_slider.setMaximum(5)
        self.goat_eating_speed_slider.setValue(1)
        eating_speed_value_label = QLabel(f"{self.goat_eating_speed_slider.value()}")
        eating_speed_value_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")

        self.goat_eating_speed_slider.valueChanged.connect(
            lambda: eating_speed_value_label.setText(f"{self.goat_eating_speed_slider.value()}")
        )
        layout.addWidget(eating_speed_label)
        layout.addWidget(self.goat_eating_speed_slider)
        layout.addWidget(eating_speed_value_label)

        speed_label = QLabel("Скорость стада")
        speed_label.setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")
        self.goat_speed_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.goat_speed_slider.setMinimum(1)
        self.goat_speed_slider.setMaximum(5)
        self.goat_speed_slider.setValue(1)
        speed_value_label = QLabel(f"{self.goat_speed_slider.value()}")
        speed_value_label   .setStyleSheet("font-weight: bold; color:black; margin-bottom: 10px;")

        self.goat_speed_slider.valueChanged.connect(
            lambda: speed_value_label.setText(f"{self.goat_speed_slider.value()}")
        )
        layout.addWidget(speed_label)
        layout.addWidget(self.goat_speed_slider)
        layout.addWidget(speed_value_label)

        close_button = QPushButton("Закрыть настройки")
        close_button.setStyleSheet("""
            background-color: #0078d7;
            color: white;
            border-radius: 5px;
            padding: 5px;
        """)
        close_button.clicked.connect(self.toggle_settings)
        layout.addWidget(close_button)

        self.settings_window.setLayout(layout)
        self.settings_window.hide()

    def init_settings_button(self):
        self.settings_button = QPushButton("Настройки", self)
        self.settings_button.setGeometry(10, 10, 100, 30)
        self.settings_button.clicked.connect(self.toggle_settings)

    def toggle_settings(self):
        if self.settings_window.isVisible():
            self.settings_window.hide()
            self.paused = False
        else:
            self.settings_window.show()
            self.paused = True

    def eat_cabbage(self, goat, cabbage):
        if cabbage.size <= 0:
            goat.eating = False
            cabbage.being_eaten = False
            goat.target_cabbage = None
            return

        if cabbage.size > 0:
            stamina_increase = min(cabbage.nutrition * goat.eating_speed / cabbage.size, 100 - goat.stamina)
            goat.stamina = min(goat.stamina + stamina_increase, 100)
            goat.size += 0.2 * goat.fertility

        cabbage.size -= goat.eating_speed
        if cabbage.size <= 0:
            goat.eating = False
            cabbage.being_eaten = False
            goat.target_cabbage = None

    def find_closest_cabbage(self, goat):
        closest_cabbage = None
        min_distance = float('inf')

        for cabbage in self.cabbages:
            if cabbage.being_eaten:
                continue

            distance = ((goat.x - cabbage.x) ** 2 + (goat.y - cabbage.y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_cabbage = cabbage

        return closest_cabbage

    def update_frame(self):
        if self.paused:
            return

        for goat in self.goats:
            goat.stamina = max(goat.stamina - 0.5 * (goat.size / 20), 0)

            if goat.stamina <= 0:
                goat.size -= 0.01

            if goat.size > 5:
                if goat.eating and goat.target_cabbage:
                    self.eat_cabbage(goat, goat.target_cabbage)
                else:
                    closest_cabbage = self.find_closest_cabbage(goat)

                    if closest_cabbage:
                        if goat.is_near_cabbage(closest_cabbage):
                            goat.eating = True
                            goat.target_cabbage = closest_cabbage
                            closest_cabbage.being_eaten = True
                        else:
                            goat.move_towards(closest_cabbage.x, closest_cabbage.y)
                    else:
                        goat.wander(self.window_width, self.window_height)

        self.cabbages = [cabbage for cabbage in self.cabbages if cabbage.size > 0]
        self.goats = [goat for goat in self.goats if goat.size > 5]
        self.update()

    def generate_new_cabbage(self):
        if not self.paused:
            num_new_cabbages = random.choice(self.cabbage_generation_choices)
            for _ in range(num_new_cabbages):
                self.cabbages.append(Cabbage(self.window_width, self.window_height))

    def paintEvent(self, event):
        painter = QPainter(self)

        for goat in self.goats:
            if goat.eating and goat.target_cabbage:
                cabbage = goat.target_cabbage

                goat_size = goat.size
                cabbage_size = cabbage.size

                center_x = (goat.x + cabbage.x) / 2
                center_y = (goat.y + cabbage.y) / 2

                painter.setBrush(QColor(0, 255, 0))  
                painter.drawPie(QRectF(center_x - cabbage_size / 2, center_y - cabbage_size / 2, cabbage_size, cabbage_size), 90 * 16, 180 * 16)

                painter.setBrush(QColor(255, 255, 255)) 
                painter.drawPie(QRectF(center_x - goat_size / 2, center_y - goat_size / 2, goat_size, goat_size), 270 * 16, 180 * 16)
            else:
                painter.setBrush(QColor(255, 255, 255))
                painter.drawEllipse(QRectF(goat.x, goat.y, goat.size, goat.size))

        for cabbage in self.cabbages:
            if not cabbage.is_eaten() and not cabbage.being_eaten:
                painter.setBrush(QColor(0, 255, 0))
                painter.drawEllipse(QRectF(cabbage.x, cabbage.y, cabbage.size, cabbage.size))

        if self.hovered_cabbage:
            font = QFont('Arial', 10)
            painter.setFont(font)
            info_text = f"Size: {self.hovered_cabbage.size:.1f}, Nutrition: {self.hovered_cabbage.nutrition:.1f}"
            painter.drawText(int(self.hovered_cabbage.x + 20), int(self.hovered_cabbage.y - 10), info_text)

        if self.hovered_goat:
            font = QFont('Arial', 10)
            painter.setFont(font)
            info_text = f"Size: {self.hovered_goat.size:.1f}, Stamina: {self.hovered_goat.stamina:.1f}, Eating Speed: {self.hovered_goat.eating_speed:.1f}, Fertility: {self.hovered_goat.fertility:.1f}, Speed: {self.hovered_goat.speed:.1f}"
            painter.drawText(int(self.hovered_goat.x + 20), int(self.hovered_goat.y - 10), info_text)

    def mouseMoveEvent(self, event):
        self.hovered_cabbage = None
        self.hovered_goat = None
        mouse_x = event.position().x()
        mouse_y = event.position().y()

        for cabbage in self.cabbages:
            distance = ((cabbage.x + cabbage.size / 2 - mouse_x) ** 2 + (cabbage.y + cabbage.size / 2 - mouse_y) ** 2) ** 0.5
            if distance <= cabbage.size / 2:
                self.hovered_cabbage = cabbage
                break

        if not self.hovered_cabbage:  
            for goat in self.goats:
                distance = ((goat.x + goat.size / 2 - mouse_x) ** 2 + (goat.y + goat.size / 2 - mouse_y) ** 2) ** 0.5
                if distance <= goat.size / 2:
                    self.hovered_goat = goat
                    break

        self.update() 

    def mousePressEvent(self, event):
        x, y = event.position().x(), event.position().y()

        if event.button() == Qt.MouseButton.RightButton:
            for goat in self.goats:
                if goat.x <= x <= goat.x + goat.size and goat.y <= y <= goat.y + goat.size:
                    self.paused = True
                    self.last_click_position = (x, y)
                    context_menu = self.create_context_menu_for_object("goat", goat)
                    context_menu.exec(event.globalPosition().toPoint())
                    return

            for cabbage in self.cabbages:
                if cabbage.x <= x <= cabbage.x + cabbage.size and cabbage.y <= y <= cabbage.y + cabbage.size:
                    self.paused = True
                    self.last_click_position = (x, y)
                    context_menu = self.create_context_menu_for_object("cabbage", cabbage)
                    context_menu.exec(event.globalPosition().toPoint())
                    return

            self.last_click_position = (x, y)
            context_menu = self.create_context_menu(x, y)
            context_menu.exec(event.globalPosition().toPoint())

    def create_context_menu(self, x, y):
        menu = QMenu(self)

        add_cabbage_action = menu.addAction("Добавить капусту")
        add_cabbage_action.triggered.connect(lambda: self.add_cabbage(x, y))

        add_goat_action = menu.addAction("Добавить стадо")
        add_goat_action.triggered.connect(lambda: self.add_goat(x, y))

        return menu

    def create_context_menu_for_object(self, obj_type, obj):
        menu = QMenu(self)

        if obj_type == "goat":
            modify_action = menu.addAction("Изменить параметры стада")
            modify_action.triggered.connect(lambda: self.modify_goat(obj))
        elif obj_type == "cabbage":
            modify_action = menu.addAction("Изменить параметры капусты")
            modify_action.triggered.connect(lambda: self.modify_cabbage(obj))

        cancel_action = menu.addAction("Отмена")
        cancel_action.triggered.connect(self.continue_game)

        return menu
    
    def continue_game(self):
        self.paused = False
        self.update()

    def add_cabbage(self, x, y):
        cabbage_size = self.cabbage_size_slider.value()
        new_cabbage = Cabbage(self.window_width, self.window_height)
        new_cabbage.x = x
        new_cabbage.y = y
        new_cabbage.size = cabbage_size
        new_cabbage.nutrition = cabbage_size * 2
        self.cabbages.append(new_cabbage)
        self.update()

    def add_goat(self, x, y):
        goat_size = self.goat_size_slider.value()
        goat_speed = self.goat_speed_slider.value()
        goat_fertility = self.goat_fertility_slider.value()
        goat_stamina = self.goat_stamina_slider.value()
        goat_eating_speed = self.goat_eating_speed_slider.value()

        new_goat = Goat(self.window_width, self.window_height)
        new_goat.x = x
        new_goat.y = y
        new_goat.size = goat_size
        new_goat.speed = goat_speed
        new_goat.fertility = goat_fertility
        new_goat.stamina = goat_stamina
        new_goat.eating_speed = goat_eating_speed
        self.goats.append(new_goat)
        self.update()

    def modify_goat(self, goat):
        goat.size = self.goat_size_slider.value()
        goat.speed = self.goat_speed_slider.value()
        goat.fertility = self.goat_fertility_slider.value()
        goat.stamina = self.goat_stamina_slider.value()
        goat.eating_speed = self.goat_eating_speed_slider.value()
        self.paused = False
        self.update()

    def modify_cabbage(self, cabbage):
        cabbage.size = self.cabbage_size_slider.value()
        cabbage.nutrition = cabbage.size * 2
        self.paused = False
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.paused = not self.paused
            self.update()
        elif event.key() == Qt.Key.Key_Escape:
            if self.settings_window.isVisible():
                self.settings_window.hide()
                self.paused = False
            else:
                self.settings_window.show()
                self.paused = True
        else:
            super().keyPressEvent(event)

def main():
    app = QApplication(sys.argv)
    ex = TheGame()
    app.exec()

main()
