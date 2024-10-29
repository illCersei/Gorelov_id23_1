import math
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QApplication, QWidget


class RotatingPointWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FFGGGGG")
        self.setGeometry(0, 0, 600, 600)
        self.radius = 200 
        self.angle = -90  

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1)  

    def update_position(self):
        self.angle += 0.2
        if self.angle >= 360:
            self.angle = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2
        painter.setPen(QColor(240, 11, 1))
        painter.drawEllipse(center_x - self.radius, center_y - self.radius, self.radius * 2, self.radius * 2)

        point_x = center_x + self.radius * math.cos(math.radians(self.angle))
        point_y = center_y + self.radius * math.sin(math.radians(self.angle))
        painter.drawEllipse(int(point_x) - 5, int(point_y) - 5, 10, 10)


app = QApplication([])
window = RotatingPointWidget()
window.show()
app.exec()
