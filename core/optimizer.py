import os
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def optimize_images(
    files,
    output_dir,
    max_px=None,
    quality=80,
    convert_webp=True
):
    """
    Optimiza imágenes y retorna estadísticas.
    
    Returns:
        tuple: (total_original_size, total_optimized_size, processed_count)
    """
    total_original = 0
    total_optimized = 0
    processed_count = 0
    
    for file_path in files:
        original_size = os.path.getsize(file_path)
        total_original += original_size
        
        name, ext = os.path.splitext(os.path.basename(file_path))
        ext = ext.lower()

        img = Image.open(file_path)

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        # =========================
        # RESIZE MANTENIENDO PROPORCIÓN
        # =========================
        if max_px:
            img.thumbnail((max_px, max_px), Image.LANCZOS)

        # =========================
        # OPCIÓN WEBP
        # =========================
        if convert_webp:
            webp_path = os.path.join(output_dir, f"{name}.webp")
            img.save(
                webp_path,
                "WEBP",
                quality=quality,
                method=6,
                optimize=True
            )

            webp_size = os.path.getsize(webp_path)

            if webp_size < original_size:
                total_optimized += webp_size
                processed_count += 1
                continue
            else:
                os.remove(webp_path)

        # =========================
        # GUARDAR EN FORMATO ORIGINAL
        # =========================
        output_path = os.path.join(output_dir, f"{name}{ext}")
        img.save(
            output_path,
            quality=quality,
            optimize=True
        )
        
        optimized_size = os.path.getsize(output_path)
        total_optimized += optimized_size
        processed_count += 1
    
    return total_original, total_optimized, processed_count


def optimize_image_batch(
    files,
    output_dir,
    max_px=None,
    quality=80,
    convert_webp=True
):
    """
    Versión alternativa para procesar todas las imágenes y retornar estadísticas.
    Optimiza memoria manteniendo solo una imagen en memoria a la vez.
    """
    return optimize_images(files, output_dir, max_px, quality, convert_webp)