import sys
import os
import time
import threading
import queue
import tempfile
from io import BytesIO

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QFileDialog, QScrollArea, QFrame, QCheckBox, QMessageBox, 
                            QProgressBar, QTextEdit, QGridLayout, QMenu, QMenuBar, QDialog, QFormLayout,
                            QLineEdit, QButtonGroup, QRadioButton, QGroupBox, QSplitter, QStyleFactory)
from PyQt5.QtGui import QFont, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.offline import plot
import requests
import csv
GITHUB_API_URL = "https://api.github.com/repos/alopez5301/AFREPO/contents/images"
DOWNLOAD_DIR = "downloaded_images" 


if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


class BaseResistanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Base Resistance")
        self.resize(300, 100)
        
        layout = QFormLayout()
        
        self.base_resistance = QLineEdit()
        self.base_resistance.setText("1.0")
        layout.addRow("Base Resistance Value:", self.base_resistance)
        
        button_box = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_box.addWidget(self.ok_button)
        button_box.addWidget(self.cancel_button)
        
        layout.addRow("", button_box)
        self.setLayout(layout)
    
    def get_base_resistance(self):
        try:
            return float(self.base_resistance.text())
        except ValueError:
            return 1.0

class SkrunksEasyTFR(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("TFR Curve Calculator")
        self.resize(600, 600)
        
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        main_layout = QVBoxLayout()
        
        title_label = QLabel("TFR Curve Calculator")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        curve_group_box = QGroupBox("Curve Type")
        curve_group_box.setFont(QFont("Arial", 10))
        curve_layout = QHBoxLayout()
        
        self.curve_group = QButtonGroup(self)
        self.radio_7point = QRadioButton("7-Point Curve")
        self.radio_8point = QRadioButton("8-Point Curve")
        self.radio_tsm = QRadioButton("TSM Fix Mode")
        self.radio_auto = QRadioButton("Auto TFR Clean")
        self.radio_7point.setChecked(True)
        
        self.curve_group.addButton(self.radio_7point)
        self.curve_group.addButton(self.radio_8point)
        self.curve_group.addButton(self.radio_tsm)
        self.curve_group.addButton(self.radio_auto)
        
        self.radio_7point.toggled.connect(lambda: self.switch_curve_type(self.temperatures_7pt))
        self.radio_8point.toggled.connect(lambda: self.switch_curve_type(self.temperatures_8pt))
        self.radio_tsm.toggled.connect(lambda: self.switch_curve_type(self.temperatures_tsm))
        self.radio_auto.toggled.connect(lambda: self.switch_curve_type(self.temperatures_auto))
        
        curve_layout.addWidget(self.radio_7point)
        curve_layout.addWidget(self.radio_8point)
        curve_layout.addWidget(self.radio_tsm)
        curve_layout.addWidget(self.radio_auto)
        curve_layout.addStretch(1)
        
        curve_group_box.setLayout(curve_layout)
        main_layout.addWidget(curve_group_box)
        
        self.extrapolateCheck = QCheckBox("Extrapolate 800°F value (enter 0 in 800 res)")
        main_layout.addWidget(self.extrapolateCheck)
        
        
        io_button_layout = QHBoxLayout()
        
        self.importButton = QPushButton("Import CSV")
        self.importButton.setFont(QFont("Arial", 10))
        self.importButton.clicked.connect(self.import_csv)
        io_button_layout.addWidget(self.importButton)
        
        self.exportButton = QPushButton("Export CSV")
        self.exportButton.setFont(QFont("Arial", 10))
        self.exportButton.clicked.connect(self.export_csv)
        io_button_layout.addWidget(self.exportButton)
        
        main_layout.addLayout(io_button_layout)
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(8)
        main_layout.addLayout(self.grid_layout)
        
        self.temperatures_7pt = [70, 200, 300, 400, 500, 570, 800]
        self.temperatures_8pt = [-40, 70, 200, 300, 400, 500, 570, 800]  
        self.temperatures_tsm = [70, 200, 220, 300, 500, 570, 800] 
        self.temperatures_auto = [70, 200, 300, 400, 500, 600, 800]
        
        self.current_temperatures = self.temperatures_7pt
        self.temp_inputs = {}
        self.value_inputs = {}
        
        self.create_temperature_fields(self.temperatures_7pt)
        
        calculate_button_layout = QHBoxLayout()
        
        self.calcButton = QPushButton("Calculate TFR")
        self.calcButton.setFont(QFont("Arial", 10, QFont.Bold))
        self.calcButton.clicked.connect(self.calculate_tfr)
        calculate_button_layout.addWidget(self.calcButton)
        
        main_layout.addLayout(calculate_button_layout)
        
        self.resultText = QTextEdit()
        self.resultText.setReadOnly(True)
        self.resultText.setFont(QFont("Consolas", 10))
        main_layout.addWidget(self.resultText)
        

        self.calculated_coefficients = []
        
        self.setLayout(main_layout)
    
    def switch_curve_type(self, temperatures):
        if self.sender() and self.sender().isChecked():
            self.current_temperatures = temperatures
            self.create_temperature_fields(temperatures)
    
    def create_temperature_fields(self, temperatures):
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        temp_header = QLabel("Temperature (°F)")
        temp_header.setFont(QFont("Arial", 10, QFont.Bold))
        self.grid_layout.addWidget(temp_header, 0, 0)
        
        value_header = QLabel("Resistance Value")
        value_header.setFont(QFont("Arial", 10, QFont.Bold))
        self.grid_layout.addWidget(value_header, 0, 1)
        
        self.temp_inputs = {}
        self.value_inputs = {}
        
        is_tsm_mode = self.radio_tsm.isChecked()
        is_auto_mode = self.radio_auto.isChecked()
        
        for i, temp in enumerate(temperatures):
            row = i + 1  
            
            if is_tsm_mode and temp == 200:
                temp_label = QLabel(f"{temp} °F")
                temp_label.setFont(QFont("Arial", 10))
                self.grid_layout.addWidget(temp_label, row, 0)
                
                value_input = QLineEdit("")
                value_input.setFont(QFont("Arial", 10))
                value_input.setReadOnly(True)
                value_input.setStyleSheet("background-color: #f0f0f0;")
                self.grid_layout.addWidget(value_input, row, 1)
                
                self.value_inputs[temp] = value_input
                continue
            
            if is_auto_mode:
                temp_label = QLabel(f"{temp} °F")
                temp_label.setFont(QFont("Arial", 10))
                self.grid_layout.addWidget(temp_label, row, 0)
                
                value_input = QLineEdit("")
                value_input.setFont(QFont("Arial", 10))
                
                if temp != 70:
                    value_input.setReadOnly(True)
                    value_input.setStyleSheet("background-color: #f0f0f0;")
                else:
                    value_input.textChanged.connect(self.auto_fill_values)
                
                self.grid_layout.addWidget(value_input, row, 1)
                self.value_inputs[temp] = value_input
                continue
                
            if is_tsm_mode and temp == 220:
                temp_label = QLabel(f"{temp} °F")
                temp_label.setFont(QFont("Arial", 10))
                self.grid_layout.addWidget(temp_label, row, 0)
            else:
                temp_input = QLineEdit(str(temp))
                temp_input.setFont(QFont("Arial", 10))
                self.grid_layout.addWidget(temp_input, row, 0)
                self.temp_inputs[temp] = temp_input
            
            value_input = QLineEdit("")
            value_input.setFont(QFont("Arial", 10))
            self.grid_layout.addWidget(value_input, row, 1)
            
            self.value_inputs[temp] = value_input
       
            if is_tsm_mode and temp == 70:
                value_input.textChanged.connect(self.update_tsm_200_value)
    
    def auto_fill_values(self):
        if not self.radio_auto.isChecked() or 70 not in self.value_inputs:
            return
        try:
            r70 = float(self.value_inputs[70].text())
            if r70 <= 0:
                return
            target_ratio_at_600 = 0.79

            if 200 in self.value_inputs:
                self.value_inputs[200].setText(f"{(r70 + 0.001):.3f}")

            for temp in self.temperatures_auto:
                if temp == 70 or temp == 200:
                    continue
                elif temp == 600:
                    self.value_inputs[600].setText("0.79")
                elif temp == 800:
                    if 600 in self.value_inputs and self.value_inputs[600].text():
                        try:
                            r600 = float(self.value_inputs[600].text())
                            r800 = r600 * 0.96
                            self.value_inputs[800].setText(f"{r800:.3f}")
                        except ValueError:
                            pass
                else:
                    ratio = 1.0 - ((1.0 - target_ratio_at_600) * (temp - 70) / (600 - 70))
                    res_value = r70 * ratio
                    self.value_inputs[temp].setText(f"{res_value:.3f}")
        except (ValueError, KeyError):
            pass

    
    def update_tsm_200_value(self):
        if self.radio_tsm.isChecked() and 70 in self.value_inputs and 200 in self.value_inputs:
            try:
                base_value = float(self.value_inputs[70].text())
                self.value_inputs[200].setText(f"{(base_value + 0.001):.3f}")
            except (ValueError, KeyError):
                self.value_inputs[200].setText("")
    
    def calculate_tfr(self):
        try:
            temperatures = []
            
            if self.radio_auto.isChecked():
                temperatures = self.temperatures_auto.copy()
                self.auto_fill_values()
            elif self.radio_tsm.isChecked():
                for temp in self.current_temperatures:
                    if temp in self.temp_inputs:
                        try:
                            edited_temp = float(self.temp_inputs[temp].text())
                            temperatures.append(edited_temp)
                        except ValueError:
                            temperatures.append(temp)
                    else:
                        temperatures.append(temp)
            else:
                for temp in self.current_temperatures:
                    if temp in self.temp_inputs:
                        try:
                            edited_temp = float(self.temp_inputs[temp].text())
                            temperatures.append(edited_temp)
                        except ValueError:
                            temperatures.append(temp)
            
            if self.radio_tsm.isChecked():
                self.update_tsm_200_value()
            
            values = []
            for i, temp in enumerate(self.current_temperatures):
                text = self.value_inputs[temp].text()
                values.append(round(float(text), 3) if text else None)
            
            if None in values:
                QMessageBox.warning(self, "Input Error", "Please enter all resistance values.")
                return
            
            R0 = values[0]
            coefficients = [(temp, (R / R0)) for temp, R in zip(temperatures, values)]
            
            if (self.extrapolateCheck.isChecked() or self.radio_auto.isChecked()) and 800 in self.current_temperatures:
                idx_800 = self.current_temperatures.index(800)
                prev_temp_idx = idx_800 - 1
                if prev_temp_idx >= 0:
                    prev_coef = values[prev_temp_idx] / R0
                    coefficients[idx_800] = (800, round(prev_coef * 0.96, 3))
            
            self.calculated_coefficients = coefficients
            
            result_str = "Temperature (degF),Electrical Resistivity\n"
            for temp, coef in coefficients:
                result_str += f"{temp},{coef:.3f}\n"
            
            self.resultText.setText(result_str)
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid resistance values!")
    
    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            temperatures = []
            resistances = []
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)
                for row in reader:
                    if len(row) >= 2:
                        try:
                            temp = float(row[0].strip('"'))
                            resistance = float(row[1].strip('"'))
                            temperatures.append(temp)
                            resistances.append(resistance)
                        except ValueError:
                            continue
            
            if not temperatures:
                QMessageBox.warning(self, "Import Error", "No valid data found in CSV file.")
                return
            
            if len(temperatures) == 8 and abs(temperatures[0] + 40) < 5: 
                self.radio_8point.setChecked(True)
                self.current_temperatures = self.temperatures_8pt
            elif len(temperatures) == 8:
                self.radio_8point.setChecked(True)
                self.current_temperatures = self.temperatures_8pt
            elif len(temperatures) == 7:
                if 220 in temperatures or any(abs(t - 220) < 1 for t in temperatures):
                    self.radio_tsm.setChecked(True)
                    self.current_temperatures = self.temperatures_tsm
                else:
                    self.radio_7point.setChecked(True)
                    self.current_temperatures = self.temperatures_7pt
            
            dialog = BaseResistanceDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                base_resistance = dialog.get_base_resistance()
                for i, temp in enumerate(temperatures):
                    closest_temp = min(self.current_temperatures, key=lambda x: abs(x - temp))
                    absolute_resistance = resistances[i] * base_resistance
                    if closest_temp in self.value_inputs:
                        self.value_inputs[closest_temp].setText(f"{absolute_resistance:.3f}")
                
                if self.radio_tsm.isChecked():
                    self.update_tsm_200_value()
                elif self.radio_auto.isChecked():
                    self.auto_fill_values()
                
                QMessageBox.information(self, "Import Complete", 
                    f"CSV data imported successfully with base resistance of {base_resistance}.")
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import CSV: {str(e)}")
    
    def export_csv(self):
        if not hasattr(self, 'calculated_coefficients') or not self.calculated_coefficients:
            QMessageBox.warning(self, "Export Error", "Please calculate TFR values first!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                    writer.writerow(["Temperature (degF)", "Electrical Resistivity"])
                    for temp, coef in self.calculated_coefficients:
                        writer.writerow([temp, f"{coef:.3f}"])
                
                QMessageBox.information(self, "Success", "TFR data saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")

class ImageLoaderThread(QThread):
    progress_update = pyqtSignal(int, int)
    image_loaded = pyqtSignal(dict)
    loading_finished = pyqtSignal()

    def __init__(self, image_urls):
        super().__init__()
        self.image_urls = image_urls
        self.stop_loading = False

    def run(self):
        total_images = len(self.image_urls)
        for i, url in enumerate(self.image_urls):
            if self.stop_loading:
                break
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
                dimensions = f"{image.width}x{image.height}"
                self.image_loaded.emit({'url': url, 'dimensions': dimensions, 'content': response.content})
            except requests.RequestException as e:
                print(f"Error fetching {url}: {e}")
            
     
            self.progress_update.emit(i + 1, total_images)
            time.sleep(0.1)  
            
        self.loading_finished.emit()


class SkrunksAfFE(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Skrunks AF FE")
        self.setupUI()
        
    def setupUI(self):
        self.layout = QVBoxLayout()
        
  
        self.convert_btn = QPushButton("Select Font and Convert")
        self.convert_btn.setMinimumHeight(70)
        self.convert_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.convert_btn.setStyleSheet(
            "QPushButton {"
            "    background-color: #8A2BE2;"
            "    color: white;"
            "    border-radius: 35px;"
            "    padding: 10px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #7A378B;"
            "}"
        )
        self.convert_btn.clicked.connect(self.run_conversion)
        
      
        self.menu_frame = QWidget()
        self.menu_layout = QHBoxLayout(self.menu_frame)
        
 
        self.text_output = QTextEdit()
        self.text_output.setFont(QFont("Courier", 10))
        self.text_output.setReadOnly(True)
        

        self.layout.addWidget(self.convert_btn, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.menu_frame)
        self.layout.addWidget(self.text_output)
        
        self.setLayout(self.layout)
        self.resize(800, 600)

    def categorize_characters(self, chars):
        categories = {
            "numbers": "",
            "UPPERCASE": "",
            "lowercase": "",
            "symbols": "",
        }
        for char in chars:
            if char.isdigit():
                categories["numbers"] += char
            elif char.isupper():
                categories["UPPERCASE"] += char
            elif char.islower():
                categories["lowercase"] += char
            else:
                categories["symbols"] += char
        return categories

    def convert_font_to_pixels(self, font_path, width, height, chars):
        images = {}

        for char in chars:
            font_size = height
            font = ImageFont.truetype(font_path, font_size)

            while True:
                temp_image = Image.new('1', (width, height), color=1)
                draw = ImageDraw.Draw(temp_image)
                bbox = draw.textbbox((0, 0), char, font=font)
                char_width = bbox[2] - bbox[0]
                char_height = bbox[3] - bbox[1]

                if char_width <= width and char_height <= height:
                    break
                font_size -= 1
                font = ImageFont.truetype(font_path, font_size)

            image = Image.new('1', (width, height), color=1)
            draw = ImageDraw.Draw(image)

            x_pos = (width - char_width) // 2 - bbox[0]
            y_pos = (height - char_height) // 2 - bbox[1]

            draw.text((x_pos, y_pos), char, font=font, fill=0)

            pixels = []
            for y in range(height):
                line = []
                for x in range(width):
                    line.append('X' if image.getpixel((x, y)) == 0 else '.')
                pixels.append("".join(line))

            images[char] = pixels

        return images

    def print_char_images(self, images):
        output = ""
        for char, pixels in images.items():
            hex_index = format(ord(char), '02X')
            output += f'<Image Index="{hex_index}" Width="{len(pixels[0])}" Height="{len(pixels)}">\n'
            output += '  <Data>\n'
            for line in pixels:
                output += line + "\n"
            output += '  </Data>\n'
            output += '</Image>\n'
        return output

    def run_conversion(self):
        try:
            font_path, _ = QFileDialog.getOpenFileName(self, "Select Font File", "", "TrueType Font (*.ttf)")
            if not font_path:
                QMessageBox.information(self, "Info", "No font file selected.")
                return

            specs = [
                (6, 8, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-%"),
                (7, 16, "0123456789"),
                (8, 16, "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
                (12, 16, "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
                (14, 32, "0123456789"),
                (16, 24, "0123456789"),
            ]

            output = ""
            sections = []
            sub_sections = {}
            for width, height, chars in specs:
                categories = self.categorize_characters(chars)
                section_title = f"SIZE {width}x{height}"
                sections.append(section_title)
                sub_sections[section_title] = []
                output += f"\n{section_title}\n"
                for category, characters in categories.items():
                    if characters:
                        images = self.convert_font_to_pixels(font_path, width, height, characters)
                        sub_section_title = f"{category.upper()}"
                        sub_sections[section_title].append(sub_section_title)
                        output += f"\n{sub_section_title}\n"
                        output += self.print_char_images(images)

            self.text_output.setText(output)
            self.create_navigation_menu(sections, sub_sections)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def create_navigation_menu(self, sections, sub_sections):
     
        while self.menu_layout.count():
            item = self.menu_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


        for section in sections:
            btn = QPushButton(section)
            btn.setStyleSheet(
                "QPushButton {"
                "    background-color: #8A2BE2;"
                "    color: white;"
                "    border-radius: 15px;"
                "    padding: 5px;"
                "} "
                "QPushButton:hover {"
                "    background-color: #7A378B;"
                "} "
            )
            btn.clicked.connect(lambda checked, sec=section: self.scroll_to_section(sec))
            self.menu_layout.addWidget(btn)

    def scroll_to_section(self, section):
        cursor = self.text_output.textCursor()
        cursor.movePosition(cursor.Start)
        self.text_output.setTextCursor(cursor)
        

        if self.text_output.find(section):
            cursor = self.text_output.textCursor()
            self.text_output.setTextCursor(cursor)


class SkrunksImageRepository(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Skrunks Image Repository")
        
        self.size_categories = ['449x121', '64x80', '64x64', '96x32', '64x48', '64x40', '96x16']
        
       
        self.image_list = []
        self.filtered_list = []
        
        self.setupUI()
        self.load_images()
        
    def setupUI(self):
        main_layout = QVBoxLayout()
        
 
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        

        show_all_button = QPushButton("Show All")
        show_all_button.clicked.connect(self.show_all_images)
        button_layout.addWidget(show_all_button)
        

        for category in self.size_categories:
            button = QPushButton(category)
            button.clicked.connect(lambda checked, c=category: self.filter_images(c))
            button_layout.addWidget(button)
        
        button_layout.addStretch()
        main_layout.addWidget(button_frame)
        

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_container = QWidget()
        self.image_layout = QVBoxLayout(self.image_container)
        self.scroll_area.setWidget(self.image_container)
        main_layout.addWidget(self.scroll_area)
        

        refresh_button = QPushButton("Refresh Images")
        refresh_button.clicked.connect(self.load_images)
        main_layout.addWidget(refresh_button)
        

        progress_frame = QWidget()
        progress_layout = QHBoxLayout(progress_frame)
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("0%")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        main_layout.addWidget(progress_frame)
        
        self.setLayout(main_layout)
        self.resize(800, 600)
        
    def fetch_image_list(self):
        try:
            response = requests.get(GITHUB_API_URL)
            response.raise_for_status()
            return [file['download_url'] for file in response.json() if file['type'] == 'file']
        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch image list: {e}")
            return []
    
    def load_images(self):

        self.image_list = []
        self.filtered_list = []
        self.progress_bar.setValue(0)
        self.progress_label.setText("0%")
        
        self.clear_image_layout()
        

        image_urls = self.fetch_image_list()
        if not image_urls:
            return
            

        self.loader_thread = ImageLoaderThread(image_urls)
        self.loader_thread.progress_update.connect(self.update_progress)
        self.loader_thread.image_loaded.connect(self.add_image)
        self.loader_thread.loading_finished.connect(self.loading_finished)
        self.loader_thread.start()
        
    def update_progress(self, current, total):
        percentage = int((current / total) * 100)
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(f"{percentage}%")
        
    def add_image(self, image_data):
        self.image_list.append(image_data)
        self.filtered_list = self.image_list.copy()
        self.display_images()
        
    def loading_finished(self):
        self.progress_label.setText("Loading Complete!")
        
    def clear_image_layout(self):
        while self.image_layout.count():
            item = self.image_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
    def show_all_images(self):
        self.filtered_list = self.image_list.copy()
        self.display_images()
        
    def filter_images(self, category_filter):
        self.filtered_list = [img for img in self.image_list if img['dimensions'] == category_filter]
        self.display_images()
        
    def display_images(self):
        self.clear_image_layout()
        
        for img in self.filtered_list:
            url, dimensions, content = img['url'], img['dimensions'], img['content']
            filename = os.path.basename(url)
            

            frame = QFrame()
            frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
            frame_layout = QVBoxLayout(frame)
            

            label = QLabel(f"{filename}\nDimensions: {dimensions}")
            frame_layout.addWidget(label)
            

            pil_image = Image.open(BytesIO(content))
            pil_image.thumbnail((150, 150))
            

            if filename.lower().endswith('.bmp'):

                qimage = QImage(pil_image.convert("RGB").tobytes(), 
                               pil_image.width, pil_image.height, 
                               pil_image.width * 3,  
                               QImage.Format_RGB888)
            elif filename.lower().endswith('.png') and pil_image.mode == 'RGBA':

                qimage = QImage(pil_image.tobytes(), 
                               pil_image.width, pil_image.height,
                               pil_image.width * 4,
                               QImage.Format_RGBA8888)
            else:

                rgb_image = pil_image.convert("RGB")
                qimage = QImage(rgb_image.tobytes(), 
                               rgb_image.width, rgb_image.height,
                               rgb_image.width * 3,  
                               QImage.Format_RGB888)
                
            pixmap = QPixmap.fromImage(qimage)
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            frame_layout.addWidget(image_label, alignment=Qt.AlignCenter)
            

            download_btn = QPushButton("Download")
            download_btn.clicked.connect(lambda checked, u=url, f=filename: self.download_image(u, f))
            frame_layout.addWidget(download_btn)
            
            self.image_layout.addWidget(frame)
            

        self.image_layout.addStretch()
        
    def download_image(self, url, filename):
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(response.content)
            QMessageBox.information(self, "Download Complete", f"Image saved to {filepath}")
        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to download {filename}: {e}")


class SkrunksDataPlotter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Skrunks Data Plotter")
        self.data = None
        self.cached_columns = {}
        self.columns_to_plot = []
        
        self.setupUI()
        
    def setupUI(self):
        layout = QVBoxLayout()
        

        title_label = QLabel("Skrunks Data Plotter")
        title_label.setFont(QFont("Helvetica", 16))
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        

        self.select_btn = QPushButton("Select CSV File")
        self.select_btn.clicked.connect(self.select_file)
        layout.addWidget(self.select_btn)
        

        self.checkbox_frame = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_frame)
        layout.addWidget(self.checkbox_frame)
        

        self.plot_btn = QPushButton("Generate Plot")
        self.plot_btn.clicked.connect(self.generate_plot)
        self.plot_btn.setEnabled(False)
        layout.addWidget(self.plot_btn)
        

        self.status_label = QLabel("Status: Waiting for file...")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.resize(400, 400)
        
    def select_file(self):
        self.file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV files (*.csv)")
        if self.file_path:
            self._load_data()
            self._setup_checkboxes()
            self.plot_btn.setEnabled(True)
            
    def _load_data(self):
        self.status_label.setText(f"Status: File selected: {os.path.basename(self.file_path)}")
        self.data = pd.read_csv(self.file_path)
        self.cached_columns = {col: self.data[col].copy() for col in self.data.columns if col.lower() != "time"}
        
    def _setup_checkboxes(self):

        while self.checkbox_layout.count():
            item = self.checkbox_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                

        self.checkboxes = {}
        for column in self.cached_columns.keys():
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_columns_to_plot)
            self.checkbox_layout.addWidget(checkbox)
            self.checkboxes[column] = checkbox
            
        self.update_columns_to_plot()
        
    def update_columns_to_plot(self):
        self.columns_to_plot = [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]
        self.status_label.setText(f"Status: Selected columns: {', '.join(self.columns_to_plot)}")
        
    def generate_plot(self):
        if self.data is not None and self.columns_to_plot:
            fig = make_subplots(rows=1, cols=1)
            for column in self.columns_to_plot:
                mask = ~self.data[column].isna()
                filtered_time = self.data["Time"][mask]
                filtered_values = self.cached_columns[column][mask]
                fig.add_trace(go.Scatter(x=filtered_time, y=filtered_values, mode='lines', name=column))
                last_time, last_value = filtered_time.iloc[-1], filtered_values.iloc[-1]
                fig.add_annotation(x=last_time, y=last_value, text=f"{last_value:.2f}", showarrow=True, arrowhead=2)
            fig.update_layout(title="Skrunks AF Data Plotter", xaxis_title="Time", yaxis_title="Values", showlegend=True)

            temp_path = os.path.join(tempfile.gettempdir(), 'temp-plot.html')
            plot(fig, filename=temp_path, config={"scrollZoom": True}, auto_open=True)

            self.status_label.setText("Status: Interactive plot displayed.")
        else:
            self.status_label.setText("Status: No columns selected for plotting.")


class SkrunksNFETools(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Skrunks MOD EXT")
        self.setupUI()
        
    def setupUI(self):

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        

        title_label = QLabel("Skrunks MOD EXT")
        title_label.setFont(QFont("Helvetica", 20))
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        

        af_fe_btn = QPushButton("Open Skrunks af FE")
        af_fe_btn.setMinimumWidth(250)
        af_fe_btn.clicked.connect(self.open_af_fe)
        layout.addWidget(af_fe_btn, alignment=Qt.AlignCenter)
        
        data_plotter_btn = QPushButton("Open Skrunks Data Plotter")
        data_plotter_btn.setMinimumWidth(250)
        data_plotter_btn.clicked.connect(self.open_data_plotter)
        layout.addWidget(data_plotter_btn, alignment=Qt.AlignCenter)
        
        image_repo_btn = QPushButton("Open Image Repository")
        image_repo_btn.setMinimumWidth(250)
        image_repo_btn.clicked.connect(self.open_image_repository)
        layout.addWidget(image_repo_btn, alignment=Qt.AlignCenter)

        easy_tfr_btn = QPushButton("Open Skrunks Easy TFR")
        easy_tfr_btn.setMinimumWidth(250)
        easy_tfr_btn.clicked.connect(self.open_easy_tfr)
        layout.addWidget(easy_tfr_btn, alignment=Qt.AlignCenter)
        

        self.setCentralWidget(central_widget)
        self.resize(400, 300)
        
    def open_af_fe(self):
        self.af_fe_window = SkrunksAfFE()
        self.af_fe_window.show()
        
    def open_data_plotter(self):
        self.data_plotter_window = SkrunksDataPlotter()
        self.data_plotter_window.show()
        
    def open_image_repository(self):
        self.image_repo_window = SkrunksImageRepository()
        self.image_repo_window.show()
        
    def open_easy_tfr(self):
        self.easy_tfr_window = SkrunksEasyTFR()
        self.easy_tfr_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  
    main_window = SkrunksNFETools()
    main_window.show()
    sys.exit(app.exec_())
