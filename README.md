# KiwiTex - Conversor de TEX a PDF

![KiwiTex Logo](kiwitexlogo.png)

## El Problema

Trabajar con archivos LaTeX tradicionalmente ha presentado varias dificultades para usuarios no técnicos:

- **Complejidad de instalación**: Configurar un entorno LaTeX funcional requiere instalar distribuciones pesadas como MiKTeX o TeX Live, lo que puede ser intimidante para usuarios sin experiencia técnica.
- **Proceso manual**: La conversión de archivos .tex a PDF generalmente requiere ejecutar comandos en la terminal o usar editores especializados.
- **Barrera técnica**: Muchas herramientas existentes asumen un conocimiento previo de los comandos de compilación de LaTeX.
- **Falta de retroalimentación**: Los errores de compilación a menudo son crípticos y difíciles de entender para principiantes.

## La Solución

KiwiTex es una aplicación de escritorio desarrollada en Python que simplifica radicalmente el proceso de conversión de archivos TEX a PDF, ofreciendo:

- **Interfaz gráfica intuitiva** que elimina la necesidad de usar la línea de comandos.
- **Instalación automática** de MiKTeX, manejando toda la configuración técnica por el usuario.
- **Proceso simplificado** de un solo clic para la conversión de archivos.
- **Retroalimentación clara** sobre el estado de la conversión y cualquier error que pueda surgir.
- **Sistema de logs detallado** para facilitar la solución de problemas.

## Características Principales

- **Interfaz gráfica intuitiva** desarrollada con PyQt5
- **Conversión de archivos TEX a PDF** con un solo clic
- **Instalación automática** de MiKTeX (si no está instalado)
- **Sistema de logs avanzado** con diferentes niveles de severidad
- **Barra de progreso** en tiempo real
- **Diseño moderno** con efectos visuales y sombras
- **Automatización completa** del proceso de compilación
- **Manejo de errores** con mensajes descriptivos

## Requisitos del Sistema

- **Sistema Operativo**: Windows 10/11
- **Python**: 3.11 o superior
- **Espacio en disco**: Mínimo 2GB libres
- **Privilegios de administrador** (requeridos para instalar MiKTeX)

## Instalación

### Opción 1: Ejecutar desde código fuente

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/kiwilax.git
   cd kiwilax
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación** (como administrador):
   ```bash
   python KiwiTex.py
   ```

### Opción 2: Usar el ejecutable

1. **Descargar** la última versión desde [Releases](https://github.com/tu-usuario/kiwi-lax/releases)
2. **Ejecutar** `KiwiTex.exe` como administrador

## Dependencias

- PyQt5 >= 5.15.10
- pywin32 >= 306
- Pillow >= 10.0.0

## Uso

1. **Iniciar la aplicación** con privilegios de administrador
2. **Seleccionar archivo** TEX a convertir
3. **Elegir carpeta** de destino para el PDF
4. **Hacer clic en "Convertir a PDF"**
5. **Esperar** a que se complete la conversión
6. **El archivo PDF** se guardará automáticamente

### Sistema de Logs

La aplicación genera registros detallados en la carpeta `logs/`:
- `kiwitex.log` - Log principal
- `main.log` - Log del módulo principal
- `converter.log` - Log del conversor LaTeX

## Estructura del Proyecto

```
kiwiLax/
├── KiwiTex.py           # Aplicación principal (todo en uno)
├── requirements.txt     # Dependencias del proyecto
├── kiwitexlogo.png      # Logo de la aplicación
├── kiwilax.manifest    # Configuración de privilegios
├── .gitignore          # Archivos ignorados por Git
├── build/              # Archivos temporales de compilación
├── dist/               # Ejecutables generados
└── logs/               # Archivos de registro
```

## Solución de Problemas

### Problemas Comunes

1. **Error de permisos**
   - Asegúrate de ejecutar como administrador
   - Verifica que tienes permisos de escritura en la carpeta de destino

2. **MiKTeX no se instala**
   - Verifica tu conexión a Internet
   - Descarga manualmente MiKTeX desde [miktex.org](https://miktex.org/)

3. **Archivo no encontrado**
   - Verifica que la ruta del archivo no contenga caracteres especiales
   - Asegúrate de que el archivo existe y no está siendo usado por otro programa

### Revisión de Logs

Los archivos de registro en la carpeta `logs/` contienen información detallada:
- Errores de compilación LaTeX
- Problemas de permisos
- Eventos del sistema

## 🛠️ Compilación a Ejecutable

Para crear un ejecutable independiente:

1. Instalar PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Generar el ejecutable:
   ```bash
   pyinstaller --onefile --windowed --icon=kiwitexlogo.ico --name KiwiTex KiwiTex.py
   ```

3. El ejecutable estará en `dist/KiwiTex.exe`

### Opciones de compilación adicionales:
- `--noconsole`: Oculta la consola en segundo plano
- `--add-data "kiwitexlogo.png;."`: Incluye archivos adicionales
- `--clean`: Limpia archivos temporales de compilaciones anteriores

## Limitaciones Conocidas

- Solo compatible con Windows
- Requiere privilegios de administrador para instalar MiKTeX
- El tamaño del ejecutable puede ser grande debido a las dependencias

## Licencia

Este proyecto está bajo la [Licencia MIT](LICENSE).

## Contribuciones

Las contribuciones son bienvenidas. Por favor, lee las [pautas de contribución](CONTRIBUTING.md) antes de enviar un pull request.

## Reconocimientos

- [PyQt5](https://pypi.org/project/PyQt5/) - Para la interfaz gráfica
- [MiKTeX](https://miktex.org/) - Distribución de LaTeX
- [PyInstaller](https://www.pyinstaller.org/) - Para crear ejecutables

---

<div align="center">
  Hecho con ❤️ por el equipo de MiCasa
</div>
"# KiwiLax" 
