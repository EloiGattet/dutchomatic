#!/usr/bin/env python3
"""Interface graphique interactive pour conversion d'images avec dithering."""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QFileDialog, QMessageBox,
    QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image

# Ajouter le répertoire parent au path pour importer le module dithering
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.dithering import apply_error_diffusion


class ImageLabel(QLabel):
    """Label personnalisé qui supporte le drag & drop."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setText("Glissez-déposez une image ici\nou cliquez sur 'Parcourir'")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                background-color: #f5f5f5;
                padding: 20px;
            }
        """)
        self.drop_callback = None
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files and self.drop_callback:
            self.drop_callback(files[0])


class ImageConverterGUI(QMainWindow):
    """Interface graphique pour conversion d'images avec dithering."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convertisseur d'images - Dithering N&B")
        self.setGeometry(100, 100, 1100, 750)
        
        # Variables
        self.original_image = None
        self.processed_image = None
        self.current_image_name = None
        self.current_algorithm = 'atkinson_plus'
        
        # Dossier de sortie
        project_root = Path(__file__).parent.parent
        self.output_dir = project_root / 'data' / 'surprise_photos'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Timer pour debounce
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_processed_image)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Zone de sélection d'image
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Image:", styleSheet="font-weight: bold; font-size: 12pt;"))
        
        browse_btn = QPushButton("Parcourir...")
        browse_btn.clicked.connect(self.select_image)
        browse_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                font-size: 11pt;
            }
        """)
        select_layout.addWidget(browse_btn)
        
        self.image_path_label = QLabel("Aucune image sélectionnée")
        self.image_path_label.setStyleSheet("color: gray;")
        select_layout.addWidget(self.image_path_label)
        select_layout.addStretch()
        
        main_layout.addLayout(select_layout)
        
        # Frame principal pour contrôles et prévisualisation
        content_layout = QHBoxLayout()
        
        # Colonne gauche : Contrôles
        controls_frame = QFrame()
        controls_frame.setFixedWidth(300)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setSpacing(15)
        
        # Algorithme
        algo_label = QLabel("Algorithme:")
        algo_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        controls_layout.addWidget(algo_label)
        
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(['atkinson_plus', 'atkinson', 'floyd_steinberg', 'sierra24a', 'stucki'])
        self.algorithm_combo.setCurrentText('atkinson_plus')
        self.algorithm_combo.currentTextChanged.connect(self.on_algorithm_change)
        controls_layout.addWidget(self.algorithm_combo)
        
        # Luminosité
        brightness_label = QLabel("Luminosité:")
        brightness_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        controls_layout.addWidget(brightness_label)
        
        brightness_layout = QVBoxLayout()
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(-100)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.on_brightness_change)
        brightness_layout.addWidget(self.brightness_slider)
        
        self.brightness_value_label = QLabel("0")
        self.brightness_value_label.setStyleSheet("font-size: 9pt;")
        brightness_layout.addWidget(self.brightness_value_label)
        controls_layout.addLayout(brightness_layout)
        
        # Contraste
        contrast_label = QLabel("Contraste:")
        contrast_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        controls_layout.addWidget(contrast_label)
        
        contrast_layout = QVBoxLayout()
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(200)  # 0.0 à 2.0 avec résolution 0.01
        self.contrast_slider.setValue(100)  # 1.0
        self.contrast_slider.valueChanged.connect(self.on_contrast_change)
        contrast_layout.addWidget(self.contrast_slider)
        
        self.contrast_value_label = QLabel("1.0")
        self.contrast_value_label.setStyleSheet("font-size: 9pt;")
        contrast_layout.addWidget(self.contrast_value_label)
        controls_layout.addLayout(contrast_layout)
        
        controls_layout.addStretch()
        
        # Bouton de sauvegarde
        self.save_button = QPushButton("Sauvegarder")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)
        controls_layout.addWidget(self.save_button)
        
        content_layout.addWidget(controls_frame)
        
        # Colonne droite : Prévisualisation
        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(10)
        
        # Image originale
        original_label = QLabel("Original")
        original_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        preview_layout.addWidget(original_label)
        
        self.original_label = ImageLabel()
        self.original_label.drop_callback = self.load_image_from_path
        self.original_label.setMinimumHeight(300)
        self.original_label.setScaledContents(False)
        preview_layout.addWidget(self.original_label)
        
        # Image traitée
        processed_label = QLabel("Résultat (Dithering N&B)")
        processed_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        preview_layout.addWidget(processed_label)
        
        self.processed_label = QLabel()
        self.processed_label.setAlignment(Qt.AlignCenter)
        self.processed_label.setMinimumHeight(300)
        self.processed_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                background-color: white;
            }
        """)
        self.processed_label.setScaledContents(False)
        preview_layout.addWidget(self.processed_label)
        
        content_layout.addLayout(preview_layout)
        main_layout.addLayout(content_layout)
        
        # Label de statut
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("color: gray; font-size: 9pt;")
        main_layout.addWidget(self.status_label)
    
    def select_image(self):
        """Ouvre un dialogue pour sélectionner une image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.webp *.bmp);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            self.load_image_from_path(file_path)
    
    def load_image_from_path(self, file_path: str):
        """Charge une image depuis un chemin de fichier."""
        try:
            self.load_image(Path(file_path))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger l'image:\n{str(e)}")
    
    def load_image(self, image_path: Path):
        """Charge une image et met à jour l'interface."""
        try:
            # Charger l'image
            img = Image.open(image_path)
            
            # Convertir en RGB si nécessaire
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Stocker l'image originale (pleine résolution)
            self.original_image = img.copy()
            
            # Afficher l'image originale
            self.display_image(img, self.original_label, max_size=(500, 400))
            
            # Mettre à jour le label et stocker le nom
            self.image_path_label.setText(image_path.name)
            self.image_path_label.setStyleSheet("color: black;")
            self.current_image_name = image_path.stem
            
            # Activer le bouton de sauvegarde
            self.save_button.setEnabled(True)
            
            # Traiter l'image
            self.update_processed_image()
            
        except Exception as e:
            raise Exception(f"Erreur lors du chargement: {str(e)}")
    
    def display_image(self, img: Image.Image, label: QLabel, max_size: tuple = None):
        """Affiche une image PIL sur un QLabel."""
        # Redimensionner pour l'affichage si nécessaire
        if max_size:
            display_img = img.copy()
            if display_img.width > max_size[0] or display_img.height > max_size[1]:
                display_img.thumbnail(max_size, Image.LANCZOS)
        else:
            display_img = img
        
        # Convertir en RGB pour l'affichage (unifie tous les modes)
        if display_img.mode != 'RGB':
            display_img = display_img.convert('RGB')
        
        # Convertir PIL Image en QPixmap avec le bon stride
        # Pour RGB888, le stride doit être width * 3 (3 bytes par pixel)
        width, height = display_img.size
        rgb_data = display_img.tobytes('raw', 'RGB')
        stride = width * 3  # 3 bytes par pixel pour RGB
        
        q_image = QImage(rgb_data, width, height, stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        label.setPixmap(pixmap)
        
        # Ajuster la taille du label
        label.setFixedSize(pixmap.size())
    
    def on_algorithm_change(self, algorithm: str):
        """Callback lors du changement d'algorithme."""
        self.current_algorithm = algorithm
        self.update_processed_image()
    
    def on_brightness_change(self, value: int):
        """Callback lors du changement de luminosité."""
        self.brightness_value_label.setText(str(value))
        self.schedule_update()
    
    def on_contrast_change(self, value: int):
        """Callback lors du changement de contraste."""
        contrast = value / 100.0
        self.contrast_value_label.setText(f"{contrast:.1f}")
        self.schedule_update()
    
    def schedule_update(self):
        """Planifie une mise à jour avec debounce."""
        self.update_timer.stop()
        self.update_timer.start(150)
    
    def update_processed_image(self):
        """Met à jour l'image traitée selon les paramètres actuels."""
        if self.original_image is None:
            return
        
        try:
            self.status_label.setText("Traitement en cours...")
            self.status_label.setStyleSheet("color: blue; font-size: 9pt;")
            QApplication.processEvents()
            
            # Récupérer les paramètres
            algorithm = self.current_algorithm
            brightness = self.brightness_slider.value()
            contrast = self.contrast_slider.value() / 100.0
            
            # Redimensionner à 384px de large pour le traitement
            img_to_process = self.original_image.copy()
            if img_to_process.width > 384:
                ratio = 384 / float(img_to_process.width)
                new_height = int(img_to_process.height * ratio)
                img_to_process = img_to_process.resize((384, new_height), Image.LANCZOS)
            
            # Appliquer le dithering
            processed = apply_error_diffusion(
                img_to_process,
                algorithm=algorithm,
                brightness=brightness,
                contrast=contrast
            )
            
            # Stocker l'image traitée (pleine résolution)
            self.processed_image = processed.copy()
            
            # Afficher l'image traitée
            self.display_image(processed, self.processed_label, max_size=(500, 400))
            
            self.status_label.setText("Prêt")
            self.status_label.setStyleSheet("color: green; font-size: 9pt;")
            
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)}")
            self.status_label.setStyleSheet("color: red; font-size: 9pt;")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du traitement:\n{str(e)}")
    
    def save_image(self):
        """Sauvegarde l'image traitée dans le dossier de sortie."""
        if self.processed_image is None:
            QMessageBox.warning(self, "Attention", "Aucune image à sauvegarder")
            return
        
        try:
            # Générer le nom de fichier
            if self.current_image_name:
                base_name = self.current_image_name
            else:
                base_name = 'image'
            
            output_filename = f"{base_name}.png"
            output_path = self.output_dir / output_filename
            
            # Gérer les doublons
            counter = 1
            while output_path.exists():
                output_filename = f"{base_name}_{counter}.png"
                output_path = self.output_dir / output_filename
                counter += 1
            
            # Sauvegarder en PNG compressé
            self.processed_image.save(str(output_path), 'PNG', optimize=True, compress_level=9)
            
            QMessageBox.information(self, "Succès", f"Image sauvegardée:\n{output_path.name}")
            self.status_label.setText(f"Sauvegardé: {output_path.name}")
            self.status_label.setStyleSheet("color: green; font-size: 9pt;")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")
            self.status_label.setText(f"Erreur: {str(e)}")
            self.status_label.setStyleSheet("color: red; font-size: 9pt;")


def main():
    """Point d'entrée principal."""
    app = QApplication(sys.argv)
    window = ImageConverterGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
