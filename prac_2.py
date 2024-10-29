import sys
import random
import json
import os
from PyQt6.QtWidgets import QApplication, QWidget
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

        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_file)

        # Проверяем наличие файла конфигурации и создаем его, если он отсутствует
        if not os.path.exists(config_path):
            default_config = {
                "window_width": 800,
                "window_height": 800,
                "num_goats": 10,
                "num_cabbages": 20,
                "cabbage_generation_choices": [2, 3, 4, 8]
            }
            with open(config_path, 'w') as file:
                json.dump(default_config, file, indent=4)
            print(f"Файл конфигурации не найден. Создан файл с базовыми настройками: {config_path}")



        with open(config_file, 'r') as file:
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
        self.cabbage_timer.start(1000)

        self.paused = False
        self.hovered_cabbage = None
        self.hovered_goat = None

        self.setMouseTracking(True)

        self.setWindowTitle('Огород')
        self.setGeometry(100, 100, self.window_width, self.window_height)
        self.show()

    def eat_cabbage(self, goat, cabbage):
        if cabbage.size <= 0:
            goat.eating = False
            cabbage.being_eaten = False
            goat.target_cabbage = None
            return

        cabbage.size -= goat.eating_speed
        stamina_increase = min(cabbage.nutrition * goat.eating_speed / cabbage.size, 100 - goat.stamina)
        goat.stamina = min(goat.stamina + stamina_increase, 100)
        goat.size += 0.2 * goat.fertility

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
            goat.stamina = max(goat.stamina - 0.01 * (goat.size / 20), 0)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:  
            self.paused = not self.paused  

def main():
    app = QApplication(sys.argv)
    ex = TheGame()
    app.exec()

main()
