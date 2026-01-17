# ImageOptimizer

Un programa para comprimir y redimensionar imágenes de forma masiva, con opción de convertir a WebP solo si es más eficiente, manteniendo la proporción y pudiendo elegir la carpeta de salida.

## Características

- Redimensiona imágenes manteniendo proporción.
- Convierte a WebP si resulta más liviano (opcional).
- Vista previa de la imagen seleccionada.
- Eliminación de imágenes de la lista antes de procesar.
- Barra de progreso que muestra el avance de la optimización.
- Configuración de tamaño máximo en píxeles.
- Soporta JPG, PNG y WebP.
- Interfaz gráfica simple y clara con Tkinter.

## Uso

1. Ejecutar el programa:
    ```bash
    python main.py
    ```
2. Seleccionar las imágenes a optimizar.
3. Elegir la carpeta de salida.
4. Configurar opciones:
    - Tamaño máximo (px) [opcional]
    - Convertir a WebP si pesa menos [check opcional]
5. Presionar **Optimizar imágenes**.
6. Esperar a que finalice la barra de progreso.

## Requisitos

- Python 3.12+
- Librerías:
    ```bash
    pip install -r requirements.txt
    ```

## Estructura del proyecto

```tree
image-optimizer/
├── core/
│   └── optimizer.py
├── ui/
│   └── app.py
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```