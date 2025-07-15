import sys
import os
import subprocess
import traceback
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Type, Tuple

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QFileDialog, QLabel, QProgressBar, QFrame,
                           QCheckBox, QMessageBox, QAction, QSizePolicy, QSpacerItem,
                           QGraphicsDropShadowEffect, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QIcon, QFont, QPainter, QPainterPath, QColor, QPixmap
import winreg
import shutil
import ctypes
import win32com.client

# ============================================
# Sistema de Logs Integrado
# ============================================

class AppLogger:
    _instance = None
    
    def __new__(cls, app_name: str = "KiwiTex"):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._instance._initialized = False
            # Inicializar atributos básicos
            cls._instance.app_name = app_name
            # Asegurarse de que el directorio de logs exista
            logs_dir = Path(__file__).parent / "logs"
            logs_dir.mkdir(exist_ok=True, parents=True)
            cls._instance.logs_dir = logs_dir
            
            # Inicializar el logger
            cls._instance._initialize_logger()
            
            cls._instance._initialized = True
        return cls._instance
    
    def _initialize_logger(self):
        """Inicializar el sistema de logging"""
        # Configurar el logger principal
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar propagación al logger raíz
        self.logger.propagate = False
        
        # Si ya tiene handlers, no los volvemos a agregar
        if self.logger.handlers:
            return
            
        # Formato para los logs
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(name)-15s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para archivo de logs principal
        log_file = self.logs_dir / f"{self.app_name.lower()}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers al logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Configurar excepción global
        sys.excepthook = self.handle_unhandled_exception
        
        # Log de inicio
        self.logger.info(f"=== Inicio de la aplicación {self.app_name} ===")
        self.logger.info(f"Versión de Python: {sys.version}")
        self.logger.info(f"Directorio de trabajo: {os.getcwd()}")
        if hasattr(os, 'uname'):
            self.logger.info(f"Sistema operativo: {os.name} {os.uname().version}")
        else:
            self.logger.info(f"Sistema operativo: {os.name}")
    
    def get_logger(self, name: Optional[str] = None):
        """Obtener el logger configurado o un logger para un módulo específico"""
        if name:
            return logging.getLogger(f"{self.app_name}.{name}")
        return self.logger
    
    def setup_module_logger(self, module_name: str, log_level: int = logging.DEBUG) -> logging.Logger:
        """Configurar un logger específico para un módulo"""
        logger = logging.getLogger(f"{self.app_name}.{module_name}")
        logger.setLevel(log_level)
        
        # Si ya tiene handlers, no los volvemos a agregar
        if logger.handlers:
            return logger
            
        # Formato específico para el módulo
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(name)-15s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para archivo específico del módulo
        log_file = self.logs_dir / f"{module_name.lower()}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Agregar handler al logger del módulo
        logger.addHandler(file_handler)
        
        return logger
    
    def log_success(self, message: str, module: Optional[str] = None, **kwargs):
        """Registrar un mensaje de éxito"""
        extra = self._prepare_extra(kwargs)
        logger = self.get_logger(module)
        logger.info(f"✅ {message}", extra=extra)
    
    def log_error(self, message: str, exc_info=None, module: Optional[str] = None, **kwargs):
        """Registrar un mensaje de error"""
        extra = self._prepare_extra(kwargs)
        logger = self.get_logger(module)
        logger.error(f"❌ {message}", exc_info=exc_info, extra=extra)
    
    def log_warning(self, message: str, module: Optional[str] = None, **kwargs):
        """Registrar un mensaje de advertencia"""
        extra = self._prepare_extra(kwargs)
        logger = self.get_logger(module)
        logger.warning(f"⚠️ {message}", extra=extra)
    
    def log_info(self, message: str, module: Optional[str] = None, **kwargs):
        """Registrar un mensaje informativo"""
        extra = self._prepare_extra(kwargs)
        logger = self.get_logger(module)
        logger.info(f"ℹ️ {message}", extra=extra)
    
    def log_debug(self, message: str, module: Optional[str] = None, **kwargs):
        """Registrar un mensaje de depuración"""
        extra = self._prepare_extra(kwargs)
        logger = self.get_logger(module)
        logger.debug(f"🐞 {message}", extra=extra)
    
    def log_exception(self, message: str, exc_info=None, module: Optional[str] = None, **kwargs):
        """Registrar una excepción con mensaje personalizado"""
        extra = self._prepare_extra(kwargs)
        logger = self.get_logger(module)
        logger.exception(f"❌ {message}", exc_info=exc_info, extra=extra)
    
    def handle_unhandled_exception(self, exc_type, exc_value, exc_traceback):
        """Manejar excepciones no capturadas"""
        # Ignorar KeyboardInterrupt para permitir una salida limpia
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        self.log_exception(
            "Excepción no manejada",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    def _prepare_extra(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preparar datos adicionales para el registro"""
        if not data:
            return {}
            
        # Convertir objetos a strings cuando sea necesario
        extra = {}
        for key, value in data.items():
            if not isinstance(value, (str, int, float, bool)) and value is not None:
                extra[key] = str(value)
            else:
                extra[key] = value
                
        return {'extra': extra}

# Inicializar el logger global
logger = AppLogger("KiwiTex")
app_logger = logger.get_logger("main")

# ============================================
# Fin del Sistema de Logs
# ============================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        # Obtener el directorio actual
        script_dir = os.path.dirname(os.path.abspath(__file__))

class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(50)
        self.setMinimumWidth(200)
        
        # Agregar efecto de sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

class ModernFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        
        # Agregar efecto de sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

class AnimatedProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(12)
        self.setMaximumHeight(12)

class LatexConverter(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, tex_file: str, output_dir: str):
        super().__init__()
        self.tex_file = tex_file
        self.output_dir = output_dir
        self.errors = []
        self.logger = logger.get_logger("converter")
        self.logger.info("Inicializando conversor LaTeX")

    def run(self):
        try:
            self.logger.info("Iniciando proceso de conversión")
            self.message.emit("Verificando instalación de MiKTeX...")
            self.progress.emit(10)
            
            if not self.check_miktex():
                self.logger.warning("MiKTeX no está instalado, procediendo con la instalación")
                self.message.emit("Instalando MiKTeX...")
                self.progress.emit(20)
                self.install_miktex()
                self.progress.emit(50)
                self.logger.info("Instalación de MiKTeX completada")
            else:
                self.logger.debug("MiKTeX ya está instalado")
                
            self.message.emit(f"Convirtiendo {Path(self.tex_file).name} a PDF...")
            self.logger.info(f"Iniciando conversión del archivo: {self.tex_file}")
            self.progress.emit(60)
            
            self.convert_to_pdf()
            
            self.progress.emit(100)
            self.message.emit("Proceso completado")
            self.logger.info("Conversión completada exitosamente")
            
        except Exception as e:
            error_msg = f"Error durante la conversión: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
        finally:
            self.finished.emit()
            self.logger.debug("Hilo de conversión finalizado")

    def check_miktex(self) -> bool:
        """Verificar si MiKTeX está instalado"""
        miktex_path = Path("C:\\Program Files\\MiKTeX\\miktex\\bin\\x64\\pdflatex.exe")
        exists = miktex_path.exists()
        self.logger.debug(f"Verificando instalación de MiKTeX en {miktex_path}: {'Encontrado' if exists else 'No encontrado'}")
        return exists

    def install_miktex(self) -> bool:
        """Instalar MiKTeX desde el instalador local"""
        try:
            self.logger.info("Iniciando instalación de MiKTeX")
            # Buscar el instalador en la carpeta requirements
            miktex_installer = Path(__file__).parent / "requirements" / "basic-miktex-24.1-x64.exe"
            if not miktex_installer.exists():
                error_msg = f"No se encontró el instalador de MiKTeX en: {miktex_installer}"
                self.logger.error(error_msg)
                raise FileNotFoundError(error_msg)
                
            self.logger.info(f"Ejecutando instalador: {miktex_installer}")
            
            # Ejecutar instalador con parámetros específicos
            result = subprocess.run([
                str(miktex_installer),
                "--shared",
                "--directory=C:\\Program Files\\MiKTeX",
                "--unattended"
            ], check=False, capture_output=True, text=True)
            
            if result.returncode != 0:
                error_msg = f"Error durante la instalación de MiKTeX: {result.stderr}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            self.logger.info("Instalación de MiKTeX completada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en install_miktex: {str(e)}", exc_info=True)
            raise

    def clean_generated_files(self, tex_file_path):
        """
        Elimina archivos generados durante la compilación, conservando solo .tex y .pdf
        """
        tex_file = Path(tex_file_path)
        directory = tex_file.parent
        base_name = tex_file.stem
        
        # Lista de extensiones a conservar
        keep_extensions = {'.tex', '.pdf'}
        
        # Eliminar archivos generados que no sean .tex o .pdf
        for file_path in directory.glob(f"{base_name}.*"):
            if file_path.suffix.lower() not in keep_extensions and file_path.is_file():
                try:
                    file_path.unlink()
                except:
                    pass
        
        # Eliminar el archivo .bat temporal si existe
        bat_file = directory / "compile_tex.bat"
        if bat_file.exists():
            try:
                bat_file.unlink()
            except:
                pass
        
        return True
            
    def convert_to_pdf(self):
        try:
            self.logger.info("Iniciando conversión a PDF")
            # Verificar que el archivo TEX existe
            tex_file = Path(self.tex_file)
            if not tex_file.exists():
                self.logger.error(f"El archivo {self.tex_file} no existe")
                self.error.emit(f"Error: El archivo {self.tex_file} no existe")
                return False
            
            # Crear la carpeta de salida si no existe
            output_dir = Path(self.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar el nombre del archivo PDF
            output_file = output_dir / f"{tex_file.stem}.pdf"
            
            # Ejecutar pdflatex
            self.message.emit(f"Ejecutando pdflatex en {tex_file.name}...")
            self.progress.emit(70)
            
            # Crear un archivo .bat temporal para ejecutar pdflatex
            bat_file = output_dir / "compile_tex.bat"
            with open(bat_file, 'w') as f:
                f.write(f'"C:\\Program Files\\MiKTeX\\miktex\\bin\\x64\\pdflatex.exe" -interaction=batchmode "{tex_file}"')
            
            # Ejecutar el archivo .bat
            subprocess.run(str(bat_file), cwd=output_dir, check=False)
            
            # Limpiar archivos generados
            self.clean_generated_files(tex_file)
            
            if output_file.exists():
                self.message.emit(f"PDF generado en: {output_file}")
                self.progress.emit(100)
                return True
            else:
                error_msg = "No se pudo generar el archivo PDF"
                self.logger.error(error_msg)
                self.error.emit(error_msg)
                return False
            
        except Exception as e:
            error_msg = f"Error durante la conversión a PDF: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
            return False

class KiwiTex(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Verificar privilegios de administrador
        if not is_admin():
            QMessageBox.warning(None, "Advertencia", 
                "La aplicación necesita permisos de administrador para funcionar correctamente.\n" +
                "Por favor, cierre la aplicación y ejecútela manualmente como administrador.")
            sys.exit(0)
        
        # Configurar logging
        self.logger = AppLogger("KiwiTex").get_logger()
        self.logger.info("=== Inicio de la aplicación ===")
        self.logger.info(f"Versión de Python: {sys.version}")
        self.logger.info(f"Directorio de trabajo: {os.getcwd()}")
        
        # Configuración básica de la ventana
        self.setWindowTitle("KiwiTex - Conversor TEX a PDF")
        self.setMinimumSize(800, 600)
        self.setMaximumSize(1200, 800)
        
        # Intentar usar el ícono si existe
        try:
            self.setWindowIcon(QIcon("kiwi.ico"))
        except Exception as e:
            self.logger.warning(f"Error al cargar el ícono: {str(e)}")
        
        # Configurar el estilo moderno
        self.setup_modern_style()
        
        # Inicializar UI
        self.init_ui()
        self.output_dir = None
        self.tex_file = None

    def setup_modern_style(self):
        """Configurar estilos minimalistas en tonos negros, grises y suaves"""
        self.setStyleSheet("""
            /* Estilo principal de la ventana */
            QMainWindow {
                background: #fafafa;
                border: none;
            }
            
            /* Contenedor principal */
            QWidget {
                background: transparent;
                color: #2c2c2c;
            }
            
            /* Etiquetas */
            QLabel {
                color: #2c2c2c;
                font-weight: 400;
                padding: 5px;
            }
            
            /* Título principal */
            QLabel#title {
                color: #1a1a1a;
                font-size: 32px;
                font-weight: 300;
                padding: 20px;
                border-bottom: 1px solid #e0e0e0;
                margin-bottom: 20px;
                letter-spacing: 1px;
            }
            
            /* Subtítulo */
            QLabel#subtitle {
                color: #666666;
                font-size: 14px;
                font-weight: 300;
                padding: 10px;
                margin-bottom: 15px;
                letter-spacing: 0.5px;
            }
            
            /* Etiqueta de estado */
            QLabel#status {
                color: #2c2c2c;
                font-size: 14px;
                font-weight: 400;
                padding: 20px;
                background: #ffffff;
                border: 1px solid #e8e8e8;
                border-radius: 6px;
                margin: 10px 0;
            }
            
            /* Botones principales */
            ModernButton {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                color: #2c2c2c;
                font-size: 14px;
                font-weight: 400;
                padding: 15px 25px;
                margin: 8px 0;
                min-height: 50px;
            }
            
            ModernButton:hover {
                background: #f5f5f5;
                border: 1px solid #999999;
                color: #1a1a1a;
            }
            
            ModernButton:pressed {
                background: #eeeeee;
                border: 1px solid #888888;
                color: #1a1a1a;
            }
            
            ModernButton:disabled {
                background: #f8f8f8;
                border: 1px solid #e0e0e0;
                color: #bdbdbd;
            }
            
            /* Barra de progreso */
            AnimatedProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                background: #f5f5f5;
                margin: 10px 0;
                text-align: center;
                color: #666666;
                font-size: 12px;
            }
            
            AnimatedProgressBar::chunk {
                background: #4a4a4a;
                border-radius: 2px;
            }
            
            /* Frames modernos */
            ModernFrame {
                background: #ffffff;
                border: 1px solid #e8e8e8;
                border-radius: 8px;
                padding: 20px;
                margin: 10px 0;
            }
            
            /* Barra de menú */
            QMenuBar {
                background: #ffffff;
                border-bottom: 1px solid #e8e8e8;
                padding: 5px;
            }
            
            QMenuBar::item {
                background: transparent;
                color: #2c2c2c;
                padding: 8px 16px;
                border-radius: 4px;
                margin: 2px;
                font-weight: 400;
            }
            
            QMenuBar::item:selected {
                background: #f0f0f0;
                color: #1a1a1a;
            }
            
            QMenuBar::item:pressed {
                background: #e8e8e8;
                color: #1a1a1a;
            }
            
            /* Menú desplegable */
            QMenu {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px;
                color: #2c2c2c;
            }
            
            QMenu::item {
                background: transparent;
                padding: 8px 16px;
                border-radius: 3px;
                margin: 1px;
            }
            
            QMenu::item:selected {
                background: #f0f0f0;
                color: #1a1a1a;
            }
            
            /* Barra de estado */
            QStatusBar {
                background: #ffffff;
                border-top: 1px solid #e8e8e8;
                color: #666666;
                padding: 5px;
                font-size: 12px;
            }
            
            /* Diálogos de mensajes */
            QMessageBox {
                background: #ffffff;
                color: #2c2c2c;
            }
            
            QMessageBox QPushButton {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                color: #2c2c2c;
                padding: 8px 16px;
                font-weight: 400;
                min-width: 80px;
            }
            
            QMessageBox QPushButton:hover {
                background: #f5f5f5;
                border: 1px solid #999999;
            }
            
            QMessageBox QPushButton:pressed {
                background: #eeeeee;
                border: 1px solid #888888;
            }
            
            /* Diálogo de archivos */
            QFileDialog {
                background: #ffffff;
                color: #2c2c2c;
            }
            
            QFileDialog QPushButton {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                color: #2c2c2c;
                padding: 6px 12px;
                font-weight: 400;
            }
            
            QFileDialog QPushButton:hover {
                background: #f5f5f5;
                border: 1px solid #999999;
            }
            
            /* Scrollbars minimalistas */
            QScrollBar:vertical {
                background: #f5f5f5;
                width: 12px;
                border: none;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background: #f5f5f5;
                height: 12px;
                border: none;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                border-radius: 6px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #a0a0a0;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* Tooltips minimalistas */
            QToolTip {
                background: #2c2c2c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
    # Cambios sugeridos para los botones (reemplaza en tu código):

    # En lugar de:
    # self.select_file_btn = ModernButton("📁 Seleccionar archivo TEX")
    # Usa:
    self.select_file_btn = ModernButton("Seleccionar archivo TEX")

    # En lugar de:
    # self.convert_btn = ModernButton("🚀 Convertir a PDF") 
    # Usa:
    self.convert_btn = ModernButton("Convertir a PDF")

    # En lugar de:
    # file_menu = menubar.addMenu('📁 Archivo')
    # Usa:
    file_menu = menubar.addMenu('Archivo')

    # En lugar de:
    # help_action = QAction('❓ Ayuda', self)
    # Usa:
    help_action = QAction('Ayuda', self)

    # En lugar de:
    # exit_action = QAction('🚪 Salir', self)
    # Usa:
    exit_action = QAction('Salir', self)

    # En los mensajes de estado, cambia:
    # self.status_label.setText("✅ Archivo seleccionado: {file_name}")
    # Por:
    self.status_label.setText(f"Archivo seleccionado: {file_name}")

    # self.status_label.setText("🔄 Iniciando conversión...")
    # Por:
    self.status_label.setText("Iniciando conversión...")

    # self.status_label.setText("✅ Conversión completada exitosamente!")
    # Por:
    self.status_label.setText("Conversión completada exitosamente!")

    # En show_error, cambia:
    # self.status_label.setText(f"❌ Error: {error_msg}")
    # Por:
    self.status_label.setText(f"Error: {error_msg}")

    # En show_help, cambia el título:
    # <h2>🥝 KiwiTex - Conversor TEX a PDF</h2>
    # Por:
    <h2>KiwiTex - Conversor TEX a PDF</h2>""")

    def init_ui(self):
        try:
            self.logger.info("Inicializando UI moderna")
            
            # Widget central con layout principal
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            main_layout.setSpacing(20)
            main_layout.setContentsMargins(30, 30, 30, 30)
            
            # Contenedor del header
            header_frame = ModernFrame()
            header_layout = QVBoxLayout(header_frame)
            
            # Título principal
            title = QLabel("KiwiTex")
            title.setObjectName("title")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(title)
            
            # Subtítulo
            subtitle = QLabel("Conversor profesional de TEX a PDF")
            subtitle.setObjectName("subtitle")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(subtitle)
            
            main_layout.addWidget(header_frame)
            
            # Espaciador
            main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
            
            # Contenedor principal de controles
            controls_frame = ModernFrame()
            controls_layout = QVBoxLayout(controls_frame)
            controls_layout.setSpacing(25)
            
            # Mensaje de estado
            self.status_label = QLabel("Listo para comenzar la conversión")
            self.status_label.setObjectName("status")
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_label.setWordWrap(True)
            controls_layout.addWidget(self.status_label)
            
            # Contenedor de botones
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(15)
            
            # Botón para seleccionar archivo
            self.select_file_btn = ModernButton("📁 Seleccionar archivo TEX")
            self.select_file_btn.clicked.connect(self.select_file)
            buttons_layout.addWidget(self.select_file_btn)
            
            # Botón de conversión
            self.convert_btn = ModernButton("🚀 Convertir a PDF")
            self.convert_btn.clicked.connect(self.start_conversion)
            self.convert_btn.setEnabled(False)
            buttons_layout.addWidget(self.convert_btn)
            
            controls_layout.addLayout(buttons_layout)
            
            # Espaciador
            controls_layout.addItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))
            
            # Barra de progreso
            progress_container = QVBoxLayout()
            progress_label = QLabel("Progreso de conversión:")
            progress_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            progress_container.addWidget(progress_label)
            
            self.progress_bar = AnimatedProgressBar()
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("Progreso: %p%")
            self.progress_bar.setValue(0)
            progress_container.addWidget(self.progress_bar)
            
            controls_layout.addLayout(progress_container)
            
            main_layout.addWidget(controls_frame)
            
            # Espaciador expansible
            main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
            
            # Configurar el menú
            self.setup_menu()
            
            # Status bar
            self.statusBar = self.statusBar()
            self.statusBar.showMessage("Aplicación iniciada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al inicializar UI: {str(e)}", exc_info=True)

    def setup_menu(self):
        """Configurar el menú de la aplicación"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu('📁 Archivo')
        
        # Acción de ayuda
        help_action = QAction('❓ Ayuda', self)
        help_action.triggered.connect(self.show_help)
        file_menu.addAction(help_action)
        
        # Acción de salir
        exit_action = QAction('🚪 Salir', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def select_file(self):
        """Seleccionar archivo TEX"""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Archivos TEX (*.tex);;Todos los archivos (*)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setViewMode(QFileDialog.Detail)
        
        if file_dialog.exec():
            self.tex_file = file_dialog.selectedFiles()[0]
            file_name = Path(self.tex_file).name
            
            # Actualizar estado
            self.status_label.setText(f"✅ Archivo seleccionado: {file_name}")
            
            # Configurar carpeta de salida automáticamente
            self.output_dir = str(Path(self.tex_file).parent)
            
            # Habilitar botón de conversión
            self.convert_btn.setEnabled(True)
            
            # Actualizar status bar
            self.statusBar.showMessage(f"Archivo listo: {file_name}")

    def start_conversion(self):
        """Iniciar el proceso de conversión"""
        if not self.tex_file:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione un archivo TEX primero")
            return
        
        # Deshabilitar botón durante la conversión
        self.convert_btn.setEnabled(False)
        self.select_file_btn.setEnabled(False)
        
        # Resetear progreso
        self.progress_bar.setValue(0)
        self.status_label.setText("🔄 Iniciando conversión...")
        self.statusBar.showMessage("Conversión en progreso...")
        
        # Crear y configurar el convertidor
        self.converter = LatexConverter(self.tex_file, self.output_dir)
        
        # Conectar señales
        self.converter.progress.connect(self.update_progress)
        self.converter.message.connect(self.update_status)
        self.converter.error.connect(self.show_error)
        self.converter.finished.connect(self.conversion_finished)
        
        # Iniciar conversión
        self.converter.start()

    def update_progress(self, value):
        """Actualizar barra de progreso"""
        self.progress_bar.setValue(value)

    def update_status(self, message):
        """Actualizar mensaje de estado"""
        self.status_label.setText(f"🔄 {message}")
        self.statusBar.showMessage(message)

    def show_error(self, error_msg):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "❌ Error", error_msg)
        self.status_label.setText(f"❌ Error: {error_msg}")
        self.statusBar.showMessage(f"Error: {error_msg}")
        self.logger.error(error_msg)

    def conversion_finished(self):
        """Finalizar conversión"""
        # Rehabilitar botones
        self.convert_btn.setEnabled(True)
        self.select_file_btn.setEnabled(True)
        
        # Actualizar estado
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ Conversión completada exitosamente!")
        self.statusBar.showMessage("Conversión completada")
        
        # Mostrar mensaje de éxito
        QMessageBox.information(self, "🎉 Éxito", 
            "La conversión se completó exitosamente!\n\n"
            f"El archivo PDF se guardó en:\n{self.output_dir}")

    def show_help(self):
        """Mostrar información de ayuda"""
        help_text = """
        <h2>🥝 KiwiTex - Conversor TEX a PDF</h2>
        
        <p><b>Descripción:</b></p>
        <p>Esta aplicación convierte archivos TEX a PDF utilizando MiKTeX.</p>
        
        <p><b>Instrucciones:</b></p>
        <ol>
            <li>Haga clic en "Seleccionar archivo TEX" para elegir su archivo</li>
            <li>Haga clic en "Convertir a PDF" para iniciar la conversión</li>
            <li>Espere a que se complete el proceso</li>
            <li>El archivo PDF se guardará en la misma carpeta que el archivo TEX</li>
        </ol>
        
        <p><b>Requisitos:</b></p>
        <ul>
            <li>Permisos de administrador</li>
            <li>MiKTeX (se instala automáticamente si no está presente)</li>
        </ul>
        
        <p><b>Soporte:</b></p>
        <p>Para obtener ayuda adicional, consulte la documentación o contacte al desarrollador.</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Ayuda - KiwiTex")
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Usar estilo Fusion para mejor compatibilidad
    
    window = KiwiTex()
    window.show()
    
    sys.exit(app.exec())