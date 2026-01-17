import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import os
from collections import OrderedDict
import queue
import time
import webbrowser

from core.optimizer import optimize_images


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ImageOptimizer v1.2 - by MiceMark")
        self.root.geometry("900x600")
        self.root.minsize(900, 600)

        # =========================
        # AGREGAR INFORMACIÓN DE LICENCIA AL TÍTULO
        # =========================
        try:
            # Importar el LicenseManager
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
            from license_manager import LicenseManager
            
            license_mgr = LicenseManager()
            license_info = license_mgr.get_license_info()
            
            if license_info["is_activated"]:
                license_text = "LICENCIA ACTIVADA"
            else:
                days_left = license_info["days_remaining"]
                if days_left == -1:
                    license_text = "LICENCIA"
                else:
                    license_text = f"PRUEBA ({days_left} días restantes)"
            
            self.root.title(f"ImageOptimizer v1.2 - by MiceMark - {license_text}")
        except Exception as e:
            print(f"Error cargando información de licencia: {e}")

        self.images = []
        self.image_cache = OrderedDict()
        self.cache_limit = 10
        self.output_dir = ""
        self.preview_queue = queue.Queue()
        self.last_preview_time = 0
        self.preview_delay = 0.1

        # =========================
        # CONTENEDOR PRINCIPAL
        # =========================
        main = tk.Frame(root, padx=20, pady=20)
        main.pack(fill="both", expand=True)

        # Configurar 3 columnas
        main.columnconfigure(0, weight=1)  # Columna 1: Imágenes seleccionadas
        main.columnconfigure(1, weight=1)  # Columna 2: Vista previa (fija)
        main.columnconfigure(2, weight=1)  # Columna 3: Opciones y Salida
        main.rowconfigure(1, weight=1)     # Fila principal para contenido

        # =========================
        # FILA SUPERIOR: BOTÓN AGREGAR Y CONTADOR
        # =========================
        top_frame = tk.Frame(main)
        top_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 15))

        tk.Button(
            top_frame,
            text="Agregar imágenes",
            width=25,
            command=self.add_images
        ).pack(side="left", padx=(0, 15))

        self.images_count_label = tk.Label(
            top_frame,
            text="No hay imágenes seleccionadas",
            fg="gray"
        )
        self.images_count_label.pack(side="left")

        # =========================
        # COLUMNA 1: IMÁGENES SELECCIONADAS
        # =========================
        left_box = tk.LabelFrame(main, text="Imágenes seleccionadas", padx=10, pady=10)
        left_box.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_box.columnconfigure(0, weight=1)
        left_box.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(left_box, selectmode="extended")
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.bind("<ButtonRelease-1>", self.on_listbox_click)

        # Botones de gestión
        buttons_frame = tk.Frame(left_box)
        buttons_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(5, 0))
        
        tk.Button(
            buttons_frame,
            text="Eliminar selección",
            command=self.remove_selected
        ).pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        tk.Button(
            buttons_frame,
            text="Limpiar todas",
            command=self.clear_all_images
        ).pack(side="left", fill="x", expand=True, padx=(2, 0))

        # =========================
        # COLUMNA 2: VISTA PREVIA (CONTENEDOR FIJO)
        # =========================
        middle_box = tk.LabelFrame(main, text="Vista previa", padx=10, pady=10)
        middle_box.grid(row=1, column=1, sticky="nsew", padx=10)
        middle_box.columnconfigure(0, weight=1)
        middle_box.rowconfigure(0, weight=1)

        # Contenedor FIXED para preview (NO cambia de tamaño)
        self.preview_width = 350
        self.preview_height = 350
        
        self.preview_frame = tk.Frame(
            middle_box, 
            width=self.preview_width, 
            height=self.preview_height,
            bg="white"
        )
        self.preview_frame.pack_propagate(False)  # IMPORTANTE: Mantiene tamaño fijo
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.preview_label = tk.Label(
            self.preview_frame,
            text="No hay imagen seleccionada",
            fg="gray",
            anchor="center",
            bg="white"
        )
        self.preview_label.pack(expand=True, fill="both")

        # =========================
        # COLUMNA 3: OPCIONES Y SALIDA
        # =========================
        right_box = tk.Frame(main)
        right_box.grid(row=1, column=2, sticky="nsew", padx=(10, 0))
        right_box.columnconfigure(0, weight=1)
        right_box.rowconfigure(0, weight=1)  # Opciones
        right_box.rowconfigure(1, weight=1)  # Salida

        # ---- Opciones
        options = tk.LabelFrame(right_box, text="Opciones", padx=10, pady=10)
        options.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        options.columnconfigure(0, weight=1)

        tk.Label(options, text="Tamaño máximo (px)").pack(anchor="w", pady=(0, 5))

        vcmd = (self.root.register(self.validate_px), "%P")
        self.max_px = tk.Entry(
            options,
            width=15,
            validate="key",
            validatecommand=vcmd
        )
        self.max_px.insert(0, "1400")
        self.max_px.pack(anchor="w", fill="x", pady=(0, 15))

        self.webp_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options,
            text="Convertir a WEBP",
            variable=self.webp_var
        ).pack(anchor="w")

        # ---- Salida
        output = tk.LabelFrame(right_box, text="Salida", padx=10, pady=10)
        output.grid(row=1, column=0, sticky="nsew")
        output.columnconfigure(0, weight=1)

        tk.Button(
            output,
            text="Seleccionar carpeta",
            command=self.select_output
        ).pack(fill="x", pady=(0, 10))

        self.output_label = tk.Label(
            output,
            text="No seleccionada",
            fg="gray",
            wraplength=250
        )
        self.output_label.pack(anchor="w")

        # =========================
        # FILA INFERIOR: PROGRESO, ESTADÍSTICAS Y BOTÓN
        # =========================
        bottom_frame = tk.Frame(main)
        bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(20, 0))

        # Barra de progreso
        self.progress = ttk.Progressbar(bottom_frame, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 8))

        # Etiquetas de estado
        status_frame = tk.Frame(bottom_frame)
        status_frame.pack(fill="x")
        
        self.status_label = tk.Label(status_frame, text="")
        self.status_label.pack(side="left")
        
        self.stats_label = tk.Label(
            status_frame,
            text="",
            font=("", 10)
        )
        self.stats_label.pack(side="right")

        # Botón optimizar
        tk.Button(
            bottom_frame,
            text="Optimizar imágenes",
            width=25,
            command=self.start_process
        ).pack(pady=(10, 15))

        # =========================
        # APOYO AL DESARROLLO
        # =========================
        donacion_frame = tk.Frame(bottom_frame)
        donacion_frame.pack()
        
        tk.Label(
            donacion_frame,
            text="¿Te sirvió este programa?",
            fg="#5a5a5a",
            font=("", 9)
        ).pack(side="left")
        
        tk.Label(
            donacion_frame,
            text=" • ",
            fg="#cccccc"
        ).pack(side="left")
        
        link_label = tk.Label(
            donacion_frame,
            text="Apoya el desarrollo con una donación",
            fg="#e74c3c",
            cursor="hand2",
            font=("", 9)
        )
        link_label.pack(side="left")
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://link.micemark.com.ar/donar"))
        
        def on_enter(e):
            link_label.config(fg="#c0392b", font=("", 9, "underline"))
            
        def on_leave(e):
            link_label.config(fg="#e74c3c", font=("", 9))
            
        link_label.bind("<Enter>", on_enter)
        link_label.bind("<Leave>", on_leave)
        
        tk.Label(
            bottom_frame,
            text="¡Gracias por usar ImageOptimizer!",
            fg="#888888",
            font=("", 8)
        ).pack(pady=(5, 0))

        # =========================
        # MENÚ DIRECTO "ACERCA DE" (1 CLICK)
        # =========================
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # Menú directo (no submenú)
        menubar.add_command(label="Acerca de / Licencia", command=self.show_about_dialog)

        # Iniciar procesador de previews
        self.process_preview_queue()

    # =========================
    # MÉTODOS (se mantienen IGUALES)
    # =========================
    def process_preview_queue(self):
        try:
            while True:
                img_path = self.preview_queue.get_nowait()
                self.show_preview_sync(img_path)
        except queue.Empty:
            pass
        self.root.after(50, self.process_preview_queue)

    def get_cached_image(self, img_path):
        if img_path in self.image_cache:
            img = self.image_cache.pop(img_path)
            self.image_cache[img_path] = img
            return img
        try:
            img = Image.open(img_path)
            img.load()
            if len(self.image_cache) >= self.cache_limit:
                self.image_cache.popitem(last=False)
            self.image_cache[img_path] = img
            return img
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            return None

    def clear_image_cache(self):
        self.image_cache.clear()

    def validate_px(self, value):
        if value == "":
            return True
        return value.isdigit() and int(value) >= 1

    def update_images_count(self):
        count = len(self.images)
        if count == 0:
            self.images_count_label.config(text="No hay imágenes seleccionadas", fg="gray")
        else:
            total_size = sum(os.path.getsize(f) for f in self.images)
            total_mb = total_size / (1024 * 1024)
            if count == 1:
                text = f"1 imagen seleccionada ({total_mb:.1f} MB)"
            else:
                text = f"{count} imágenes seleccionadas ({total_mb:.1f} MB)"
            self.images_count_label.config(text=text, fg="black")

    def add_images(self):
        files = filedialog.askopenfilenames(
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp")]
        )
        if not files:
            return
        for f in files:
            if f not in self.images:
                self.images.append(f)
                self.listbox.insert("end", os.path.basename(f))
        self.update_images_count()
        if not self.listbox.curselection() and self.images:
            self.listbox.selection_set(0)
            self.show_preview_async(self.images[0])

    def on_listbox_select(self, event=None):
        current_time = time.time()
        if current_time - self.last_preview_time < self.preview_delay:
            return
        selections = self.listbox.curselection()
        if selections:
            last_index = selections[-1]
            if last_index < len(self.images):
                self.show_preview_async(self.images[last_index])
                self.last_preview_time = current_time

    def on_listbox_click(self, event=None):
        self.root.after(10, self.on_listbox_select)

    def show_preview_async(self, img_path):
        self.preview_queue.put(img_path)

    def show_preview_sync(self, img_path):
        try:
            img = self.get_cached_image(img_path)
            if img is None:
                self.preview_label.config(image="", text="Error cargando imagen")
                return
            
            # ESCALAR proporcional al contenedor FIJO
            frame_width = self.preview_width
            frame_height = self.preview_height

            img_ratio = img.width / img.height
            frame_ratio = frame_width / frame_height

            if img_ratio > frame_ratio:
                new_width = frame_width
                new_height = int(frame_width / img_ratio)
            else:
                new_height = frame_height
                new_width = int(frame_height * img_ratio)

            # Redimensionar
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            self.root.after(0, lambda: self.update_preview_ui(resized_img))
            
        except Exception as e:
            print(f"Error en preview: {e}")
            self.root.after(0, lambda: self.preview_label.config(
                image="", text="Error en vista previa"
            ))

    def update_preview_ui(self, img):
        try:
            self.preview_img = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.preview_img, text="")
        except Exception as e:
            self.preview_label.config(image="", text="Error actualizando vista")

    def remove_selected(self):
        selections = self.listbox.curselection()
        if not selections:
            return
        if len(selections) == 1:
            msg = "¿Estás seguro de eliminar la imagen seleccionada?"
        else:
            msg = f"¿Estás seguro de eliminar las {len(selections)} imágenes seleccionadas?"
        if not messagebox.askyesno("Confirmar", msg):
            return
        for index in sorted(selections, reverse=True):
            if index < len(self.images):
                img_path = self.images[index]
                if img_path in self.image_cache:
                    del self.image_cache[img_path]
                self.listbox.delete(index)
                del self.images[index]
        if not self.listbox.curselection():
            self.preview_label.config(image="", text="No hay imagen seleccionada")
            self.preview_label.image = None
        self.update_images_count()
        if self.images:
            new_index = min(selections[0], len(self.images) - 1)
            if new_index >= 0:
                self.listbox.selection_set(new_index)
                self.show_preview_async(self.images[new_index])

    def clear_all_images(self):
        if not self.images:
            return
        if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar todas las imágenes?"):
            self.images.clear()
            self.listbox.delete(0, tk.END)
            self.clear_image_cache()
            self.preview_label.config(image="", text="No hay imagen seleccionada")
            self.preview_label.image = None
            self.update_images_count()

    def select_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir = folder
            self.output_label.config(text=folder, fg="black")

    def format_bytes(self, bytes_num):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_num < 1024.0:
                return f"{bytes_num:.2f} {unit}"
            bytes_num /= 1024.0
        return f"{bytes_num:.2f} TB"

    def optimize_single_image(self, img_path, output_dir, max_px, convert_webp):
        from PIL import Image
        import os
        original_size = os.path.getsize(img_path)
        try:
            img = Image.open(img_path)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            if max_px:
                img.thumbnail((max_px, max_px), Image.LANCZOS)
            name, ext = os.path.splitext(os.path.basename(img_path))
            ext = ext.lower()
            optimized_size = original_size
            if convert_webp:
                webp_path = os.path.join(output_dir, f"{name}.webp")
                img.save(webp_path, "WEBP", quality=80, method=6, optimize=True)
                webp_size = os.path.getsize(webp_path)
                if webp_size < original_size:
                    return original_size, webp_size
                else:
                    os.remove(webp_path)
            output_path = os.path.join(output_dir, f"{name}{ext}")
            if ext in ['.jpg', '.jpeg']:
                img.save(output_path, 'JPEG', quality=80, optimize=True)
            elif ext == '.png':
                img.save(output_path, 'PNG', optimize=True)
            else:
                img.save(output_path, optimize=True)
            optimized_size = os.path.getsize(output_path)
        except Exception as e:
            print(f"Error procesando {img_path}: {e}")
            return original_size, original_size
        return original_size, optimized_size

    def start_process(self):
        if not self.images:
            messagebox.showerror("Error", "No hay imágenes seleccionadas")
            return
        if not self.output_dir:
            messagebox.showerror("Error", "No seleccionaste carpeta de salida")
            return
        self.stats_label.config(text="")
        thread = threading.Thread(target=self.process_images_with_stats)
        thread.start()

    def process_images_with_stats(self):
        value = self.max_px.get().strip()
        max_px = int(value) if value else None
        total = len(self.images)
        self.progress["maximum"] = total
        self.progress["value"] = 0
        
        def update_ui(status, progress_value=None):
            self.status_label.config(text=status)
            if progress_value is not None:
                self.progress["value"] = progress_value
            self.root.update_idletasks()
        
        self.root.after(0, lambda: update_ui("Iniciando procesamiento...", 0))
        try:
            total_original = 0
            total_optimized = 0
            for i, img_path in enumerate(self.images, 1):
                self.root.after(0, lambda idx=i: update_ui(
                    f"Procesando {idx} de {total}...", idx
                ))
                original, optimized = self.optimize_single_image(
                    img_path, 
                    self.output_dir,
                    max_px,
                    self.webp_var.get()
                )
                total_original += original
                total_optimized += optimized
            
            def show_final_stats():
                self.progress["value"] = total
                self.status_label.config(text="Proceso finalizado")
                if total_original > 0 and total_optimized > 0:
                    saved = total_original - total_optimized
                    percent_saved = (saved / total_original) * 100
                    if saved > 0:
                        stats_text = (
                            f"Ahorro: {percent_saved:.1f}% | "
                            f"Original: {self.format_bytes(total_original)} → "
                            f"Optimizado: {self.format_bytes(total_optimized)}"
                        )
                        color = "green"
                    else:
                        stats_text = (
                            f"Sin ahorro | "
                            f"Tamaño original: {self.format_bytes(total_original)} | "
                            f"Tamaño optimizado: {self.format_bytes(total_optimized)}"
                        )
                        color = "orange"
                    self.stats_label.config(text=stats_text, fg=color)
                else:
                    self.stats_label.config(
                        text="No se pudieron calcular estadísticas", 
                        fg="red"
                    )
            self.root.after(0, show_final_stats)
        except Exception as e:
            def show_error():
                self.status_label.config(text=f"Error: {str(e)}")
                self.stats_label.config(
                    text="Error durante el procesamiento", 
                    fg="red"
                )
            self.root.after(0, show_error)

    def show_about_dialog(self):
        """Muestra diálogo de información de licencia"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
        from license_manager import LicenseManager
        
        license_mgr = LicenseManager()
        license_info = license_mgr.get_license_info()
        
        # Crear ventana de diálogo
        about_window = tk.Toplevel(self.root)
        about_window.title("Acerca de - ImageOptimizer Pro")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        
        # Centrar la ventana
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Contenido
        frame = tk.Frame(about_window, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        # Título
        title = tk.Label(
            frame, 
            text="ImageOptimizer Pro", 
            font=("", 16, "")
        )
        title.pack(pady=(0, 10))
        
        # Versión
        version = tk.Label(
            frame, 
            text="Versión 1.1 • Desarrollado por MiceMark",
            font=("", 10)
        )
        version.pack(pady=(0, 0))
        
        # Separador
        separator = tk.Frame(frame, height=1, bg="#e0e0e0")
        separator.pack(fill="x", pady=20)
        
        # Información de licencia
        if license_info["is_activated"]:
            status_text = "LICENCIA PERMANENTE ACTIVADA"
            status_color = "green"
            # Mostrar clave enmascarada
            if license_info["license_key"]:
                key_parts = license_info["license_key"].split("-")
                if len(key_parts) >= 5:
                    masked_key = f"{key_parts[0]}-{key_parts[1]}-...-{key_parts[-1]}"
                else:
                    masked_key = license_info["license_key"][:8] + "..."
            else:
                masked_key = ""
        else:
            days_left = license_info["days_remaining"]
            if days_left == -1:
                status_text = "LICENCIA ACTIVADA"
                status_color = "green"
                masked_key = ""
            else:
                status_text = f"VERSIÓN DE PRUEBA ({days_left} días restantes)"
                status_color = "#FF9900"
                masked_key = ""
        
        status = tk.Label(
            frame, 
            text=status_text, 
            fg=status_color,
            font=("", 11, "bold")
        )
        status.pack(pady=(0, 10))
        
        if masked_key:
            key_label = tk.Label(
                frame, 
                text=f"Clave: {masked_key}",
                font=("Courier", 10)
            )
            key_label.pack(pady=(0, 10))
        
        # ID de máquina
        machine_label = tk.Label(
            frame, 
            text=f"ID Máquina: {license_info['machine_id']}",
            fg="gray",
            font=("", 9)
        )
        machine_label.pack(pady=(10, 20))
        
        # Botones
        buttons_frame = tk.Frame(frame)
        buttons_frame.pack(pady=20)
        
        if not license_info["is_activated"]:
            # Botón Comprar (ABRE URL)
            buy_btn = tk.Button(
                buttons_frame,
                text="Comprar Licencia",
                command=lambda: self.show_buy_info(license_info['machine_id']),
                width=25
            )
            buy_btn.pack(side="left", padx=5)
            
            # Botón Activar
            activate_btn = tk.Button(
                buttons_frame,
                text="Activar Licencia",
                command=lambda: self.activate_license(about_window, license_mgr),
                width=25
            )
            activate_btn.pack(side="left", padx=5)
        
        # NOTA: Se quitó el botón "Cerrar" - se cierra con la X de la ventana
    
    def show_buy_info(self, machine_id):
        """Abre URL para comprar"""
        import webbrowser
        
        # TU URL DE COMPRA - CÁMBIALA POR LA TUYA
        compra_url = "https://micemark.com.ar/comprar-image-optimizer"
        
        webbrowser.open(compra_url)
    
    def activate_license(self, parent_window, license_mgr):
        """Diálogo para activar licencia"""
        from tkinter import simpledialog
        
        license_key = simpledialog.askstring(
            "Activar Licencia",
            "Ingresa tu clave de licencia:\n\n" +
            "Formato: IMGOPT-XXXX-XXXX-XXXX-XXXX-XXXX\n",
            parent=parent_window,
            initialvalue="IMGOPT-"
        )
        
        if license_key and license_key.strip():
            if license_mgr.activate_license(license_key.strip()):
                messagebox.showinfo(
                    "¡Licencia Activada!",
                    "¡Felicidades!\n\n"
                    "Tu licencia permanente ha sido activada.\n"
                    "Reinicia la aplicación para ver los cambios.\n\n"
                    "Gracias por tu apoyo. ¡Disfrútalo!"
                )
                parent_window.destroy()
                # Actualizar título después de activar
                self.root.title(f"ImageOptimizer v1.2 - by MiceMark - LICENCIA ACTIVADA")
            else:
                messagebox.showerror(
                    "Clave Inválida",
                    "La clave ingresada no es válida.\n\n"
                    "Verifica:\n"
                    "1. El formato: IMGOPT-XXXX-XXXX-XXXX-XXXX-XXXX\n"
                    "2. Que no haya errores de tipeo\n"
                    "3. Contacta a micemark@gmail.com si tienes problemas"
                )

def start():
    root = tk.Tk()
    App(root)
    root.mainloop()