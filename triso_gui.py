import sys
import numpy as np

from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# -------------------------------------------------
# 1. Задаём ПЯТЬ слоёв (в микрометрах) и их названия
# -------------------------------------------------
DEFAULT_LAYER_THICKNESSES = [250.0, 95.0, 40.0, 35.0, 40.0]  # мкм
DEFAULT_LAYER_NAMES = ["1", "2", "3", "4", "5"]

# -------------------------------------------------
# 2. Функция для вычисления основных параметров
# -------------------------------------------------
def calculate_sphere_segment(R, D):
    """
    Параметры:
      R (float): радиус сферы, мкм
      D (float): диаметр среза шарового сегмента, мкм

    Возвращает:
      d         = расстояние от центра сферы до плоскости сечения (мкм)
      h         = высота шарового сегмента (мкм)
      delta     = глубина шлифовки (R - h) (мкм)
      V_removed = объём снятого материала (куб. мкм)
    """
    # Расстояние от центра сферы до плоскости
    d = (R ** 2 - (D / 2) ** 2) ** 0.5

    # Высота шарового сегмента
    h = R - d

    # Глубина шлифовки
    delta = R - h  # то же, что d

    # Объём снятого сегмента по формуле: V = (π*h²*(3R - h)) / 3
    # Используем np.pi для числа π
    V_removed = (np.pi * (h ** 2) * (3 * R - h)) / 3.0

    return d, h, delta, V_removed

# -------------------------------------------------
# 3. Функция для визуализации многослойной сферы (через ось Ax)
# -------------------------------------------------
def plot_multilayer_sphere(ax, R, layer_thicknesses, layer_names, D=None, d=None):
    """
    Рисует в 2D поперечное сечение многослойной сферы:
      - несколько (по числу слоёв) концентрических окружностей,
      - Хорду (диаметр D) на высоте y = d, если D и d заданы,
      - Заштрихованный шаровой сегмент выше этой хорды,
      - Подписи с названиями слоёв.

    Параметры:
      ax               : объект осей matplotlib (Axes)
      R                (float): общий радиус сферы (мкм)
      layer_thicknesses (list) : толщины слоёв (мкм)
      layer_names       (list) : названия слоёв
      D                 (float): диаметр основания сегмента (мкм) [необязателен]
      d                 (float): расстояние от центра до плоскости среза (мкм) [необязателен]
    """
    ax.set_title("Многослойный шарик топлива (сечение), мкм")

    # Найдём границы каждого слоя от центра наружу.
    # Пример: [5000, 3000] -> границы [0, 5000, 8000]
    boundaries = [0.0]
    cum_sum = 0.0
    for t in layer_thicknesses:
        cum_sum += t
        boundaries.append(cum_sum)

    # Подготовим массив углов
    theta = np.linspace(0, 2 * np.pi, 360)

    # Зададим 5 цветов — по одному на каждый слой (можно изменить)
    colors = ["#FFDF00", "#db7093", "#494d4e", "#6495ed", "#3b3d3e"]

    for i in range(len(layer_thicknesses)):
        r_inner = boundaries[i]
        r_outer = boundaries[i + 1]
        color = colors[i % len(colors)]  # если слоёв больше 5, просто повторяем
        name = layer_names[i]

        # Нарисуем внешнюю границу (окружность) радиуса r_outer
        x_outer = r_outer * np.cos(theta)
        y_outer = r_outer * np.sin(theta)
        ax.plot(x_outer, y_outer, color='k', linewidth=1)

        # Заливка кольца между r_inner и r_outer
        angles = np.linspace(0, 2 * np.pi, 360)
        x_outer_fill = r_outer * np.cos(angles)
        y_outer_fill = r_outer * np.sin(angles)
        x_inner_fill = r_inner * np.cos(angles)
        y_inner_fill = r_inner * np.sin(angles)

        # Формируем замкнутый контур слоя
        x_layer = np.concatenate([x_outer_fill, x_inner_fill[::-1]])
        y_layer = np.concatenate([y_outer_fill, y_inner_fill[::-1]])

        ax.fill(x_layer, y_layer, color=color, alpha=0.6)

        # Добавим текстовое обозначение слоя (радиально по середине)
        r_mid = (r_inner + r_outer) / 2
        ax.text(r_mid, 0, name, fontsize=9,
                ha='left', va='center', color='black', rotation=0)

    # Если D и d заданы, рисуем хорду и заштриховку
    if D is not None and d is not None and D > 0:
        chord_y = d
        half_d = D / 2.0

        # Хорда (красная линия)
        ax.plot([-half_d, half_d], [chord_y, chord_y],
                'r-', linewidth=2, label="Диаметр (D)")

        # Заштриховка "срезанного" сегмента
        x_fill_segment = np.linspace(-half_d, half_d, 200)
        # верхняя дуга сферы
        y_fill_upper = np.sqrt(R ** 2 - x_fill_segment ** 2)
        y_fill_lower = np.full_like(x_fill_segment, chord_y)

        ax.fill_between(x_fill_segment, y_fill_lower, y_fill_upper,
                        color='gray', alpha=0.3, label="Снятый слой")

        # Обозначим центр сферы
        ax.plot(0, 0, 'ko', label="Центр (0,0)")
        ax.legend(loc='best')

    ax.set_aspect('equal', 'box')
    ax.grid(True)

    # Зададим разумные границы по осям
    pad = 0.1 * R
    ax.set_xlim(-R - pad, R + pad)
    ax.set_ylim(-R - pad, R + pad)


# -------------------------------------------------
# 4. Главное окно приложения на PyQt5
# -------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TRISO многослойная сфера")

        # Основной центральный виджет
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Главный горизонтальный лейаут (два блока: слева/справа)
        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # ---------- Блок для matplotlib ---------- #
        self.figure = Figure(figsize=(5, 5))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        plot_layout = QtWidgets.QVBoxLayout()
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)

        # ---------- Блок для ввода/вывода ---------- #
        io_widget = QtWidgets.QWidget()
        io_layout = QtWidgets.QVBoxLayout(io_widget)

        # Поле для ввода D
        self.line_edit_D = QtWidgets.QLineEdit()
        self.line_edit_D.setPlaceholderText("Введите диаметр D (мкм)")
        label_input = QtWidgets.QLabel("Диаметр шлифа (D, мкм):")

        # Кнопка "Рассчитать"
        self.calc_button = QtWidgets.QPushButton("Рассчитать")
        self.calc_button.clicked.connect(self.on_calculate)

        # Поле для вывода результатов
        self.output_text = QtWidgets.QTextEdit()
        self.output_text.setReadOnly(True)

        io_layout.addWidget(label_input)
        io_layout.addWidget(self.line_edit_D)
        io_layout.addWidget(self.calc_button)
        io_layout.addWidget(QtWidgets.QLabel("Результаты расчёта:"))
        io_layout.addWidget(self.output_text)

        # Добавляем оба блока в главный лейаут
        main_layout.addLayout(plot_layout, stretch=2)
        main_layout.addWidget(io_widget, stretch=1)

        # Инициализация данных
        self.layer_thicknesses = DEFAULT_LAYER_THICKNESSES
        self.layer_names = DEFAULT_LAYER_NAMES
        self.R = sum(self.layer_thicknesses)  # суммарный радиус

        # Первичная отрисовка (без хорды, если D ещё не задан)
        self.update_plot()

    def on_calculate(self):
        """
        Слот, вызываемый по нажатию кнопки "Рассчитать".
        Считывает D, выполняет расчёты и обновляет график/вывод.
        """
        text_D = self.line_edit_D.text().strip()
        if not text_D:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не введён диаметр D.")
            return

        try:
            D = float(text_D)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Некорректное значение D.")
            return

        if D <= 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "D должен быть положительным числом.")
            return

        if D > 2*self.R:
            QtWidgets.QMessageBox.warning(
                self, "Ошибка",
                f"D = {D} мкм больше диаметра сферы (2*R = {2*self.R} мкм). Срез невозможен."
            )
            return

        # Вычисляем
        d, h, delta, V_removed = calculate_sphere_segment(self.R, D)

        # Формируем текст результата
        result_str = (
            f"Расстояние d от центра до плоскости шлифа:  {d:.4f} мкм\n"
            f"Высота снятого слоя (h):                   {h:.4f} мкм\n"
            f"Глубина шлифовки (Δ = R - h):              {delta:.4f} мкм\n"
            f"Объём снятого материала (V_removed):       {V_removed:.4f} куб. мкм\n"
        )
        self.output_text.setPlainText(result_str)

        # Обновляем график (передаём D, d для рисования хорды и сегмента)
        self.update_plot(D, d)

    def update_plot(self, D=None, d=None):
        """
        Функция для обновления рисунка на Canvas.
        Если D и d не заданы, рисует просто многослойную сферу без "среза".
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Вызываем функцию отрисовки
        plot_multilayer_sphere(ax, self.R, self.layer_thicknesses, self.layer_names, D, d)

        self.canvas.draw()

# -------------------------------------------------
# 5. Точка входа
# -------------------------------------------------
def main():
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.resize(1000, 600)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
