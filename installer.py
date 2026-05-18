import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def create_shortcut(target, shortcut_path, icon=None):
    ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target}"
'''
    if icon:
        ps_script += f'\n$Shortcut.IconLocation = "{icon}"'
    ps_script += '\n$Shortcut.Save()'
    
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)

def install():
    try:
        app_name = "Teleprompter"
        local_app_data = os.environ.get('LOCALAPPDATA')
        install_dir = os.path.join(local_app_data, 'Programs', app_name)
        
        if not os.path.exists(install_dir):
            os.makedirs(install_dir)
            
        exe_src = get_resource_path("Teleprompter.exe")
        icon_src = get_resource_path("icon.ico")
        
        exe_dest = os.path.join(install_dir, "Teleprompter.exe")
        icon_dest = os.path.join(install_dir, "icon.ico")
        
        shutil.copy2(exe_src, exe_dest)
        if os.path.exists(icon_src):
            shutil.copy2(icon_src, icon_dest)
        
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, f"{app_name}.lnk")
        
        create_shortcut(exe_dest, shortcut_path, icon_dest if os.path.exists(icon_dest) else exe_dest)
        
        # Start menu
        start_menu = os.path.join(os.environ.get('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        sm_shortcut_path = os.path.join(start_menu, f"{app_name}.lnk")
        create_shortcut(exe_dest, sm_shortcut_path, icon_dest if os.path.exists(icon_dest) else exe_dest)

        messagebox.showinfo("Success", f"{app_name} has been installed successfully!\\n\\nA shortcut has been created on your Desktop and Start Menu.")
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to install: {e}")

root = tk.Tk()
root.title("Teleprompter Setup")
root.geometry("400x180")
root.configure(bg="#0a0e1a")

try:
    root.iconbitmap(get_resource_path('icon.ico'))
except:
    pass

tk.Label(root, text="Teleprompter Installation", font=("Segoe UI", 16, "bold"), bg="#0a0e1a", fg="white").pack(pady=(20, 10))
tk.Label(root, text="Click below to install Teleprompter on your computer.", font=("Segoe UI", 10), bg="#0a0e1a", fg="#b0b8d0").pack()

tk.Button(root, text="Install Now", font=("Segoe UI", 11, "bold"), bg="#6e8efb", fg="white", bd=0, padx=20, pady=8, cursor="hand2", command=install).pack(pady=20)

# Center window
root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

root.mainloop()
