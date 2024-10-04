import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance
import io
import cairosvg  # For SVG support

# Global variables
transparency_level = 1.0  # Fully opaque (buttons window)
image_transparency_level = 1.0  # Fully opaque (image)
image_window_visible = True
image_original = None
image_display = None
angle = 0
scale = 1.0
offset_x = 512  # Center of the canvas
offset_y = 512
start_x = 0
start_y = 0
is_dragging = False

def increase_buttons_transparency():
    global transparency_level
    if transparency_level > 0.2:
        transparency_level -= 0.1
        buttons_window.attributes('-alpha', transparency_level)
    else:
        messagebox.showinfo("Info", "Minimum transparency level reached.")

def decrease_buttons_transparency():
    global transparency_level
    if transparency_level < 1.0:
        transparency_level += 0.1
        buttons_window.attributes('-alpha', transparency_level)
    else:
        messagebox.showinfo("Info", "Maximum opacity level reached.")

def increase_image_transparency():
    global image_transparency_level
    if image_transparency_level > 0.2:
        image_transparency_level -= 0.1
        draw_image()
    else:
        messagebox.showinfo("Info", "Minimum image transparency level reached.")

def decrease_image_transparency():
    global image_transparency_level
    if image_transparency_level < 1.0:
        image_transparency_level += 0.1
        draw_image()
    else:
        messagebox.showinfo("Info", "Maximum image opacity level reached.")

def load_image():
    global image_original, angle, scale, offset_x, offset_y, image_transparency_level
    filepath = filedialog.askopenfilename(title="Select an Image", filetypes=[
        ("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.svg")])
    if filepath:
        if filepath.lower().endswith('.svg'):
            try:
                # Convert SVG to PNG using cairosvg
                png_data = cairosvg.svg2png(url=filepath)
                image_original = Image.open(io.BytesIO(png_data)).convert("RGBA")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load SVG image:\n{e}")
                return
        else:
            image_original = Image.open(filepath).convert("RGBA")
        angle = 0
        scale = min(1024 / image_original.width, 1024 / image_original.height)
        offset_x = 512  # Reset position to center
        offset_y = 512
        image_transparency_level = 1.0  # Reset image transparency to fully opaque
        draw_image()
        if not image_window_visible:
            toggle_image_window()

def draw_image():
    global image_original, image_display, angle, scale, offset_x, offset_y, image_transparency_level
    if image_original is None:
        return
    # Apply transformations
    img = image_original.copy()
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    img = img.rotate(angle, expand=True)
    # Apply transparency
    if image_transparency_level < 1.0:
        alpha = img.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(image_transparency_level)
        img.putalpha(alpha)
    image_display = ImageTk.PhotoImage(img)
    canvas.delete("all")
    canvas.create_image(offset_x, offset_y, image=image_display)
    image_window.update_idletasks()

def on_mouse_down(event):
    global is_dragging, start_x, start_y
    is_dragging = True
    start_x = event.x_root
    start_y = event.y_root

def on_mouse_up(event):
    global is_dragging
    is_dragging = False

def on_mouse_move(event):
    global offset_x, offset_y, start_x, start_y, angle
    if is_dragging:
        dx = event.x_root - start_x
        dy = event.y_root - start_y
        if event.state & 0x0004:  # If Ctrl key is held down
            angle += dx * 0.1  # Reduced rotation sensitivity
            angle %= 360  # Keep angle within 0-360 degrees
        else:
            offset_x += dx
            offset_y += dy
        start_x = event.x_root
        start_y = event.y_root
        draw_image()

def on_mouse_wheel(event):
    global scale
    # Adjust zoom sensitivity
    if sys.platform.startswith('win'):
        delta = event.delta / 120  # Normalize delta to +/-1
    elif sys.platform == 'darwin':
        delta = event.delta
    else:
        delta = 0
        if event.num == 4:  # Scroll up
            delta = 1
        elif event.num == 5:  # Scroll down
            delta = -1
    scale_factor = 1.0 + delta * 0.05  # Reduced zoom sensitivity
    scale *= scale_factor
    # Limit scale
    scale = max(0.1, min(scale, 10.0))
    draw_image()

def on_right_click(event):
    global angle, scale, offset_x, offset_y, image_transparency_level
    angle = 0
    scale = min(1024 / image_original.width, 1024 / image_original.height)
    offset_x = 512  # Reset position to center
    offset_y = 512
    image_transparency_level = 1.0  # Reset image transparency
    draw_image()

def toggle_image_window():
    global image_window_visible
    if image_window_visible:
        image_window.withdraw()
        image_window_visible = False
        btn_hide_show_image.config(text="Show Image")
    else:
        image_window.deiconify()
        image_window_visible = True
        btn_hide_show_image.config(text="Hide Image")

def on_close():
    root.destroy()
    sys.exit(0)

# New rotation functions
def rotate_image(degrees):
    global angle
    angle = degrees % 360
    draw_image()

# Create the buttons window
root = tk.Tk()
root.title("Controls")
# Remove the fixed position to allow moving the window freely
# root.geometry("+0+0")  # Commented out to let the window manager decide position
root.attributes('-topmost', True)
root.protocol("WM_DELETE_WINDOW", on_close)

# Create a frame to organize buttons
btn_frame = tk.Frame(root)
btn_frame.pack(padx=10, pady=10)

# Buttons for controlling buttons window transparency
btn_increase_buttons_transparency = tk.Button(btn_frame, text="Increase Buttons Transparency", command=increase_buttons_transparency)
btn_increase_buttons_transparency.grid(row=0, column=0, pady=5, sticky='ew')

btn_decrease_buttons_transparency = tk.Button(btn_frame, text="Decrease Buttons Transparency", command=decrease_buttons_transparency)
btn_decrease_buttons_transparency.grid(row=0, column=1, pady=5, sticky='ew')

# Buttons for controlling image transparency
btn_increase_image_transparency = tk.Button(btn_frame, text="Increase Image Transparency", command=increase_image_transparency)
btn_increase_image_transparency.grid(row=1, column=0, pady=5, sticky='ew')

btn_decrease_image_transparency = tk.Button(btn_frame, text="Decrease Image Transparency", command=decrease_image_transparency)
btn_decrease_image_transparency.grid(row=1, column=1, pady=5, sticky='ew')

# Buttons for rotating the image
rotation_angles = [45, 90, 135, 180, 360]
btn_rotate_list = []
for idx, angle_value in enumerate(rotation_angles):
    btn_rotate = tk.Button(btn_frame, text=f"Rotate {angle_value}°", command=lambda a=angle_value: rotate_image(a))
    btn_rotate.grid(row=2 + idx // 2, column=idx % 2, pady=5, sticky='ew')
    btn_rotate_list.append(btn_rotate)

# Other control buttons
btn_load_image = tk.Button(btn_frame, text="Load Image", command=load_image)
btn_load_image.grid(row=2 + len(rotation_angles) // 2, column=0, pady=5, sticky='ew')

btn_hide_show_image = tk.Button(btn_frame, text="Hide Image", command=toggle_image_window)
btn_hide_show_image.grid(row=2 + len(rotation_angles) // 2, column=1, pady=5, sticky='ew')

# Configure grid weights for equal button sizes
for i in range(2):
    btn_frame.columnconfigure(i, weight=1)

# Set the transparency of the buttons window
root.attributes('-alpha', transparency_level)

# Create the image window
image_window = tk.Toplevel(root)
image_window.title("Image Window")
image_window.geometry("1024x1024")
# Remove window decorations
image_window.overrideredirect(True)
# Set window to be transparent using magenta
image_window.attributes('-transparentcolor', 'grey')

# Center the window on the screen
screen_width = image_window.winfo_screenwidth()
screen_height = image_window.winfo_screenheight()
x = (screen_width // 2) - (1024 // 2)
y = (screen_height // 2) - (1024 // 2)
image_window.geometry(f"+{x}+{y}")
image_window.attributes('-topmost', True)
image_window.protocol("WM_DELETE_WINDOW", on_close)

# Create the canvas with magenta background
canvas = tk.Canvas(image_window, width=1024, height=1024, bg='grey', highlightthickness=0, borderwidth=0)
canvas.pack()

# Bind mouse events
canvas.bind("<ButtonPress-1>", on_mouse_down)
canvas.bind("<ButtonRelease-1>", on_mouse_up)
canvas.bind("<B1-Motion>", on_mouse_move)
# Mouse wheel binding (platform-dependent)
if sys.platform.startswith('win'):
    canvas.bind("<MouseWheel>", on_mouse_wheel)
elif sys.platform == 'darwin':
    canvas.bind("<MouseWheel>", on_mouse_wheel)
else:
    canvas.bind("<Button-4>", lambda event: on_mouse_wheel(event))
    canvas.bind("<Button-5>", lambda event: on_mouse_wheel(event))
canvas.bind("<Button-3>", on_right_click)

# Run the application
buttons_window = root  # For clarity
root.mainloop()
