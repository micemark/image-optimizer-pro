import sys,os,tkinter as tk
from tkinter import messagebox,simpledialog
sys.path.append(os.path.join(os.path.dirname(__file__),'core'))
def check_license():
 try:
  from license_manager import LicenseManager
  license_mgr=LicenseManager()
 except Exception as e:
  print(f"Error cargando LicenseManager: {e}")
  return False
 license_info=license_mgr.get_license_info()
 if license_info["is_activated"]:return True
 if license_mgr.is_trial_expired():
  root=tk.Tk();root.withdraw()
  while True:
   response=messagebox.askyesno("Licencia Requerida - ImageOptimizer Pro","Tu licencia de prueba ha expirado.\n\nPara continuar usando ImageOptimizer Pro,\nnecesitas adquirir una licencia permanente.\n\nID de tu máquina: "+license_info['machine_id']+"\n\n¿Quieres activar una licencia ahora?")
   if not response:
    messagebox.showinfo("Programa finalizado","Gracias por probar ImageOptimizer Pro.")
    root.quit();root.destroy();return False
   license_key=simpledialog.askstring("Activar Licencia","Ingresa tu clave de licencia:\n\nFormato: IMGOPT-XXXX-XXXX-XXXX-XXXX-XXXX\n\nSi no tienes una clave, visita:\nhttps://micemark.com.ar/comprar-image-optimizer",parent=root,initialvalue="IMGOPT-")
   if not license_key or not license_key.strip():continue
   if license_mgr.activate_license(license_key.strip()):
    messagebox.showinfo("¡Licencia Activada!","¡Felicidades! Licencia activada correctamente.\n\nReinicia la aplicación para aplicar los cambios.\n\n¡Gracias por tu apoyo!")
    root.quit();root.destroy();return True
   else:
    messagebox.showerror("Clave Inválida","La clave ingresada no es válida.\n\nVerifica:\n- Formato correcto\n- Sin errores de tipeo\n- Escribe a contacto@micemark.com.ar")
    try_again=messagebox.askyesno("Intentar de nuevo","¿Quieres intentar con otra clave?")
    if not try_again:root.quit();root.destroy();return False
 days_left=license_info["days_remaining"]
 if 0<days_left<=3:
  root=tk.Tk();root.withdraw()
  messagebox.showinfo(f"ImageOptimizer Pro - {days_left} días restantes",f"¡Hola! Te quedan {days_left} días de prueba.\n\nSi ImageOptimizer Pro te está siendo útil,\nconsidera adquirir la licencia permanente.\n\nEscribe a contacto@micemark.com.ar")
  root.quit();root.destroy()
 if not license_mgr.is_trial_expired():license_mgr.save_run_data()
 return True
from ui.app import start
if __name__=="__main__":
 if not check_license():sys.exit(1)
 start()