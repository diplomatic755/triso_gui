import sys
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

# -------------------------------------------------
# 1. Задаём ПЯТЬ слоёв (в микрометрах) и их названия
# -------------------------------------------------
layer_thicknesses = [250.0, 95.0, 40.0, 35.0, 40.0]  # мкм
layer_names = ["1", "2", "3", "4", "5"]

# Суммарный радиус сферы (мкм)
R = sum(layer_thicknesses)


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

    # Глубина шлифовки (то есть сколько "убрали" сверху)
    delta = R - h  # то же, что d

    # Объём снятого сегмента по формуле: V = (π*h²*(3R - h)) / 3
    V_removed = (3.141592 * (h ** 2) * (3 * R - h)) / 3.0

    return d, h, delta, V_removed


# -------------------------------------------------
# 3. Функция для визуализации многослойной сферы
# -------------------------------------------------
def visualize_multilayer_sphere(R, layer_thicknesses, layer_names, D, d):
    """
    Рисует в 2D поперечное сечение многослойной сферы:
      - 5 концентрических окружностей (каждый слой своим цветом),
      - Хорду (диаметр D) на высоте y = d,
      - Заштрихованный шаровой сегмент выше этой хорды,
      - Подписи с названиями слоёв (1-UO2, 2-Buffer, и т.д.).

    Параметры:
      R                 (float): общий радиус сферы (мкм)
      layer_thicknesses (list) : толщины слоёв (мкм)
      layer_names       (list) : названия слоёв
      D                 (float): диаметр основания сегмента (мкм)
      d                 (float): расстояние от центра до плоскости среза (мкм)
    """
    # Найдём границы каждого слоя от центра наружу
    # Пример: если layer_thicknesses = [5000,3000,2000,4000,5000]
    # то границы будут [0, 5000, 8000, 10000, 14000, 19000]
    boundaries = [0.0]
    cum_sum = 0.0
    for t in layer_thicknesses:
        cum_sum += t
        boundaries.append(cum_sum)

    # Подготовим массив углов для окружностей
    theta = np.linspace(0, 2 * 3.141592, 360)

    # Хорда на высоте chord_y = d
    chord_y = d

    plt.figure(figsize=(7, 7))
    plt.title("Многослойный шарик топлива (сечение) в микрометрах")

    # 1) Отрисовка слоёв в виде концентрических колец
    # Зададим 5 цветов — по одному на каждый слой
    colors = ["#FFDF00", "#db7093", "#494d4e", "#6495ed", "#3b3d3e"]

    for i in range(len(layer_thicknesses)):
        r_inner = boundaries[i]  # внутренний радиус i-го слоя
        r_outer = boundaries[i + 1]  # внешний радиус i-го слоя
        color = colors[i]  # цвет для i-го слоя
        name = layer_names[i]  # название слоя, напр. "1-UO2"

        # Нарисуем внешнюю границу (окружность) радиуса r_outer
        x_outer = r_outer * np.cos(theta)
        y_outer = r_outer * np.sin(theta)
        plt.plot(x_outer, y_outer, color='k', linewidth=1)

        # Заполним цветом кольцо между r_inner и r_outer
        # Сгенерируем координаты для заливки
        angles = np.linspace(0, 2 * 3.141592, 360)
        x_outer_fill = r_outer * np.cos(angles)
        y_outer_fill = r_outer * np.sin(angles)
        x_inner_fill = r_inner * np.cos(angles)
        y_inner_fill = r_inner * np.sin(angles)

        # Формируем замкнутый контур слоя
        x_layer = np.concatenate([x_outer_fill, x_inner_fill[::-1]])
        y_layer = np.concatenate([y_outer_fill, y_inner_fill[::-1]])

        plt.fill(x_layer, y_layer, color=color, alpha=0.6)

        # Добавим текстовое обозначение слоя
        # Возьмём радиус "по середине" и поставим текст справа от центра
        r_mid = (r_inner + r_outer) / 2
        plt.text(r_mid, 0, name, fontsize=9,
                 ha='left', va='center',
                 color='black',
                 rotation=0)

    # 2) Хорда (красная линия) — диаметр среза
    half_d = D / 2.0
    plt.plot([-half_d, half_d], [chord_y, chord_y],
             'r-', linewidth=2, label="Диаметр шлифа (D)")

    # 3) Заштриховываем "срезанный" шаровой сегмент сверху
    x_fill_segment = np.linspace(-half_d, half_d, 200)
    y_fill_upper = np.sqrt(R ** 2 - x_fill_segment ** 2)  # верхняя дуга сферы
    y_fill_lower = np.full_like(x_fill_segment, chord_y)

    plt.fill_between(x_fill_segment, y_fill_lower, y_fill_upper,
                     color='gray', alpha=0.3, label="Снятый слой")

    # Отметим центр сферы (0,0)
    plt.plot(0, 0, 'ko', label="Центр топлива (0,0)")

    plt.axis('equal')
    plt.grid(True)

    # Зададим границы
    pad = 0.1 * R
    plt.xlim(-R - pad, R + pad)
    plt.ylim(-R - pad, R + pad)

    plt.legend()
    plt.show()


# -------------------------------------------------
# 4. Главная функция (точка входа)
# -------------------------------------------------
def main():
    print("TRISO из 5 слоёв (в микрометрах).")
    print(f"Слои (толщины, мкм): {layer_thicknesses}")
    print(f"Названия слоёв: {layer_names}")
    print(f"Радиус топлива R = {R:.2f} мкм\n")

    # Спросим диаметр среза
    D = float(input("Введите диаметр D шлифа в микроскопе (мкм): "))

    # Проверка: нельзя, чтобы D > 2*R (тогда срез не пересечёт сферу корректно)
    if D > 2 * R:
        print("Ошибка: введённый D больше диаметра топлива! Срез невозможен.")
        return

    # Считаем основные параметры
    d, h, delta, V_removed = calculate_sphere_segment(R, D)

    # Вывод результатов
    print("\n--- Результаты расчётов ---")
    print(f"Расстояние d от центра топлива до плоскости шлифа: {d:.4f} мкм")
    print(f"Высота снятого слоя h:              {h:.4f} мкм")
    print(f"Глубина шлифовки (Δ = R - h):            {delta:.4f} мкм")
    print(f"Объём снятого материала V_removed:       {V_removed:.4f} куб. мкм")

    # Визуализация
    visualize_multilayer_sphere(R, layer_thicknesses, layer_names, D, d)

if __name__ == "__main__":
    main()