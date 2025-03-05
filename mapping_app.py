import sys
import pandas as pd
import folium
import os
from folium.plugins import BeautifyIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QVBoxLayout, QWidget, QTabWidget, QComboBox, QLineEdit, QHBoxLayout, QColorDialog
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QColor

# Основное окно приложения
class MapGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Переменные для хранения выбранного пути
        self.selected_folder = None
        self.selected_file = None
        self.save_folder = None
        self.current_marker_color = "blue"  # Инициализация цвета по умолчанию

        self.setWindowTitle("CSV to Map Generator")
        self.setGeometry(200, 200, 600, 500)

        #вкладки
        self.tabs = QTabWidget()
        self.tab_preview = QWidget()
        self.tab_settings = QWidget()
        self.tabs.addTab(self.tab_preview, "Preview")
        self.tabs.addTab(self.tab_settings, "Settings")

        #preview
        self.init_preview_tab()

        #settings
        self.init_settings_tab()

        #empty map
        self.init_empty_map()

        # Основной виджет и layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Стилизация интерфейса
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                font-size: 14px;
                padding: 10px;
                background-color: #3b83bd;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #306a9e;
            }
            QLabel {
                font-size: 12px;
                color: #333;
            }
        """)

    # Функция для инициализации пустой карты 
    # написать кнопку оновления подложки
    def init_empty_map(self):
        selected_basemap = self.basemap_selector.currentText()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(base_dir, 'empty_maps', f'{selected_basemap}.html')
        # Задаем пустую карту для отображения в preview
        self.map_view.setUrl(QUrl.fromLocalFile(map_path)) 

    #settings tab
    def init_settings_tab(self):
        layout = QVBoxLayout()

        # Кнопка выбора файла
        self.file_button = QPushButton("Выбрать CSV файл")
        self.file_button.clicked.connect(self.select_file)
        layout.addWidget(self.file_button)

        #layout for horizontal selector of fields
        fields_layout = QHBoxLayout()
        
        lat_label = QLabel("Широта:")
        fields_layout.addWidget(lat_label)
        self.lat_field_selector = QComboBox()
        self.lat_field_selector.setMinimumWidth(150)
        fields_layout.addWidget(self.lat_field_selector)

        # Метка и выпадающий список для долготы
        lon_label = QLabel("Долгота:")
        fields_layout.addWidget(lon_label)
        self.lon_field_selector = QComboBox()
        self.lon_field_selector.setMinimumWidth(150)
        fields_layout.addWidget(self.lon_field_selector)

        # Метка и выпадающий список для названия
        name_label = QLabel("Название:")
        fields_layout.addWidget(name_label)
        self.name_field_selector = QComboBox()
        self.name_field_selector.setMinimumWidth(150)
        fields_layout.addWidget(self.name_field_selector)

        layout.addLayout(fields_layout)

        # Кнопка выбора папки
        self.folder_button = QPushButton("Выбрать папку с CSV файлами")
        self.folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_button)

        # Метка для отображения выбранного пути
        self.path_label = QLabel("Файл или папка не выбраны")
        layout.addWidget(self.path_label)

        #Кнопка для сохранения пути
        self.save_button = QPushButton("Выбрать папку для сохранения")
        self.save_button.clicked.connect(self.select_save_folder)
        layout.addWidget(self.save_button)

        #Метка для пути сохранения
        self.save_path_label = QLabel("Путь для сохранения не выбран")
        layout.addWidget(self.save_path_label)

        self.tab_settings.setLayout(layout)

    def init_preview_tab(self):
        layout = QVBoxLayout()

        # Кнопка для запуска обработки
        self.process_button = QPushButton("Создать карту")
        self.process_button.clicked.connect(self.process_files)
        self.process_button.setEnabled(False)  # Отключаем кнопку до выбора файла или папки
        layout.addWidget(self.process_button)

        # # Метка для отображения результата
        # self.result_label = QLabel("")
        # layout.addWidget(self.result_label)

        input_layout = QHBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название точки")
        input_layout.addWidget(self.name_input)

        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("Широта")
        input_layout.addWidget(self.lat_input)

        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText("Долгота")
        input_layout.addWidget(self.lon_input)

        self.add_point_button = QPushButton("Добавить точку")
        self.add_point_button.clicked.connect(self.add_point_to_map)
        input_layout.addWidget(self.add_point_button)

        layout.addLayout(input_layout)

        #Tile chooser
        self.basemap_selector = QComboBox()
        self.basemap_selector.addItem("OpenStreetMap")
        self.basemap_selector.addItem("CartoDB Positron")
        self.basemap_selector.addItem("CartoDB Dark Matter")
        self.basemap_selector.currentIndexChanged.connect(self.update_empty_map)
        layout.addWidget(self.basemap_selector)

        #style of type and color point selector
        marker_style_layout = QHBoxLayout()

        #Type point selector
        self.marker_type_selector = QComboBox()
        self.marker_type_selector.addItems(["Default", "Circle", "Circle-dot", "Doughnut", "Rectangle-dot"])
        marker_style_layout.addWidget(QLabel("Type of point"))
        marker_style_layout.addWidget(self.marker_type_selector)

        #Color point selector
        self.marker_color_button = QPushButton()
        self.marker_color_button.setFixedSize(30, 30)
        self.marker_color_button.setStyleSheet("background-color: blue;")
        self.marker_color_button.clicked.connect(self.choose_marker_color)
        marker_style_layout.addWidget(QLabel("Color of point"))
        marker_style_layout.addWidget(self.marker_color_button)

        layout.addLayout(marker_style_layout)

        #виджет для отображения карты
        self.map_view =QWebEngineView()
        layout.addWidget(self.map_view, stretch= 8)

        self.tab_preview.setLayout(layout)

    # Функция выбора файла
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV файл", "", "CSV Files (*.csv)")
        if file_path:
            self.selected_file = file_path
            self.selected_folder = None  # Очищаем выбранную папку
            self.path_label.setText(f"Выбран файл: {file_path}")
            self.process_button.setEnabled(True)

        #reading headers of csv
        try:
            df = pd.read_csv(file_path, nrows=0)
            columns = df.columns.to_list()

            #fill selectors
            self.lat_field_selector.clear()
            self.lat_field_selector.addItems(columns)
            self.lat_field_selector.setEnabled(True)

            self.lon_field_selector.clear()
            self.lon_field_selector.addItems(columns)
            self.lon_field_selector.setEnabled(True)

            self.name_field_selector.clear()
            self.name_field_selector.addItems(columns)
            self.name_field_selector.setEnabled(True)
        except Exception as e:
            print(f"Error while reading CSV: {e}")


    # Функция выбора папки
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку с CSV файлами")
        if folder_path:
            self.selected_folder = folder_path
            self.selected_file = None  # Очищаем выбранный файл
            self.path_label.setText(f"Выбрана папка: {folder_path}")
            self.process_button.setEnabled(True)

    def select_save_folder(self):
        save_folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения файлов")
        if save_folder:
            self.save_folder = save_folder
            self.save_path_label.setText(f"Сохранение в: {save_folder}")
            # Активируем кнопку обработки только если выбран файл или папка с CSV
            if self.selected_file or self.selected_folder:
                self.process_button.setEnabled(True)

    # Функция обработки файлов
    def process_files(self):
        processed_files = 0

        # Если выбран файл
        if self.selected_file:
            processed_files += self.process_file(self.selected_file)
        
        # Если выбрана папка
        elif self.selected_folder:
            for root, _, files in os.walk(self.selected_folder):
                for file in files:
                    if file.endswith('.csv'):
                        file_path = os.path.join(root, file)
                        processed_files += self.process_file(file_path)
        
        # Обновление метки результата
        # self.result_label.setText(f"Обработано файлов: {processed_files}")
        # self.result_label.setAlignment(Qt.AlignCenter)

    # Функция для обработки отдельного файла
    def process_file(self, file_path):
        try:
            df = pd.read_csv(file_path)

            #use fields from selectors
            lat_field = self.lat_field_selector.currentText()
            lon_field = self.lon_field_selector.currentText()
            name_field = self.name_field_selector.currentText()

            if not all(field in df.columns for field in [lat_field, lon_field, name_field]):
                raise ValueError("Выбранные поля отсутствуют в CSV-файле.")

            prepeared_df = df[[name_field, lat_field, lon_field]].dropna(how='any')
            prepeared_df.columns = ['Name', 'Latitude', 'Longitude']
            output_path = os.path.join(self.save_folder, f"{os.path.basename(file_path).split('.')[0]}.html")

            self.mapping(prepeared_df).save(output_path)

            self.map_view.setUrl(QUrl.fromLocalFile(output_path))
            return 1  # Возвращаем 1 для подсчета обработанных файлов
        except Exception as e:
            print(f"Ошибка при обработке файла {file_path}: {e}")
            return 0
        
    def create_marker_icon(self, marker_type, color):
        """Создает иконку маркера в зависимости от выбранного типа и цвета"""
        if marker_type == "Default":
            return BeautifyIcon(
                icon="info-sign",
                icon_shape="marker",
                background_color=color,
                text_color="white"
            )
        elif marker_type == "Circle":
            return BeautifyIcon(
                icon="info-sign",
                icon_shape="circle",
                background_color=color,
                text_color="white"
            )
        elif marker_type == "Circle-dot":
            return BeautifyIcon(
                icon="info-sign",
                icon_shape="circle-dot",
                background_color=color,
                text_color="white"
            )
        elif marker_type == "Doughnut":
            return BeautifyIcon(
                icon="info-sign",
                icon_shape="doughnut",
                background_color=color,
                text_color="white"
            )
        elif marker_type == "Rectangle-dot":
            return BeautifyIcon(
                icon="info-sign",
                icon_shape="rectangle-dot",
                background_color=color,
                text_color="white"
            )
        else:
            return BeautifyIcon(
                icon="info-sign",
                icon_shape="marker",
                background_color=color,
                text_color="white"
            )

    def mapping(self, prep_df):
        center_lat = prep_df['Latitude'].mean()
        center_lon = prep_df['Longitude'].mean()
        selected_basemap = self.basemap_selector.currentText()
        marker_type = self.marker_type_selector.currentText()

        # Создаем карту с выбранной подложкой
        mymap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles=selected_basemap)

        for _, row in prep_df.iterrows():
            # Создаем иконку для каждого маркера
            icon = self.create_marker_icon(marker_type, self.current_marker_color)
            
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=row['Name'],
                icon=icon
            ).add_to(mymap)
        return mymap
    
    #update empty map depends with settings
    def update_empty_map(self):
        selected_basemap = self.basemap_selector.currentText()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(base_dir, 'empty_maps', f'{selected_basemap}.html')
        if os.path.exists(map_path):
            self.map_view.setUrl(QUrl.fromLocalFile(map_path))
        else:
            print(F'Файл подложки {map_path} не найден.')

    #adding point on the empty map
    def add_point_to_map(self):
        try:
            name = self.name_input.text()
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            marker_type = self.marker_type_selector.currentText()

            if not name:
                raise ValueError('Empty is not possible')
        
            if not hasattr(self, 'current_map'):
                self.current_map = folium.Map(location=[lon, lat], zoom_start=4, tiles=self.basemap_selector.currentText())

            # Создаем иконку для маркера
            icon = self.create_marker_icon(marker_type, self.current_marker_color)

            # Добавление точки на карту
            folium.Marker(
                location=[lat, lon],
                popup=name,
                icon=icon
            ).add_to(self.current_map)

            # Сохранение карты во временный HTML-файл
            temp_map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maps', 'temp_map.html')
            self.current_map.save(temp_map_path)

            # Обновление отображения карты
            self.map_view.setUrl(QUrl.fromLocalFile(temp_map_path))

            # Очистка полей ввода
            self.name_input.clear()
            self.lat_input.clear()
            self.lon_input.clear()

        except ValueError as e:
            print(f'Exeption: {e}')

    def choose_marker_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.marker_color_button.setStyleSheet(f"background-color: {color.name()};")
            self.current_marker_color = color.name()

# Запуск приложения
app = QApplication(sys.argv)
window = MapGeneratorApp()
window.show()
sys.exit(app.exec_())
