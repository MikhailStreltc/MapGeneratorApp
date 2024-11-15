import sys
import pandas as pd
import folium
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QVBoxLayout, QWidget, QTabWidget, QComboBox, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Основное окно приложения
class MapGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Переменные для хранения выбранного пути
        self.selected_folder = None
        self.selected_file = None
        self.save_folder = None

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
        self.lat_input.setPlaceholderText("Широта (Coordinate_N)")
        input_layout.addWidget(self.lat_input)

        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText("Долгота (Coordinate_E)")
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
        self.result_label.setText(f"Обработано файлов: {processed_files}")
        self.result_label.setAlignment(Qt.AlignCenter)

    # Функция для обработки отдельного файла
    def process_file(self, file_path):
        try:
            df = pd.read_csv(file_path)
            prepeared_df = df[['Cyrilic_name_of_site', 'Coordinate_N', 'Coordinate_E']].dropna(how='any')
            output_path = os.path.join(self.save_folder, f"{os.path.basename(file_path).split('.')[0]}.html")

            self.mapping(prepeared_df).save(output_path)

            self.map_view.setUrl(QUrl.fromLocalFile(output_path))
            return 1  # Возвращаем 1 для подсчета обработанных файлов
        except Exception as e:
            print(f"Ошибка при обработке файла {file_path}: {e}")
            return 0
        
    # Функция для создания карты
    def mapping(self, prep_df):
        center_lat = prep_df['Coordinate_N'].mean()
        center_lon = prep_df['Coordinate_E'].mean()

        selected_basemap = self.basemap_selector.currentText()

        # Создаем карту с выбранной подложкой
        if selected_basemap == "OpenStreetMap":
            mymap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="OpenStreetMap")
        elif selected_basemap == "CartoDB Positron":
            mymap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="CartoDB positron")
        elif selected_basemap == "CartoDB Dark Matter":
            mymap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="CartoDB dark_matter")

        for _, row in prep_df.iterrows():
            folium.Marker(
                location=[row['Coordinate_N'], row['Coordinate_E']],
                popup=row['Cyrilic_name_of_site'],
                icon=folium.Icon(color='blue')
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
            #getting gata out from fields
            name = self.name_input.text()
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())

            if not name:
                raise ValueError('Empty is not possible')
        
            if not hasattr(self, 'current_map'):
                self.current_map = folium.Map(location=[0, 0], zoom_start=4, tiles=self.basemap_selector.currentText())

            # Добавление точки на карту
            folium.Marker(
                location=[lat, lon],
                popup=name,
                icon=folium.Icon(color='blue')
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

# Запуск приложения
app = QApplication(sys.argv)
window = MapGeneratorApp()
window.show()
sys.exit(app.exec_())
