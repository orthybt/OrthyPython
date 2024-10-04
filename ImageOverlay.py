import sys
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import io
import cairosvg  # For SVG support
import math

class ImageOverlayApp:
    def __init__(self, root):
        # Initialize the main window and set attributes
        self.root = root
        self.root.title("Controls")
        self.transparency_level = 1.0  # Fully opaque (buttons window)
        self.image_transparency_level = 1.0  # Fully opaque (image)
        self.image_window_visible = True
        self.image_original = None
        self.image_display = None
        self.angle = 0
        self.scale = 1.0  # Initial zoom level
        self.scale_log = 0  # Logarithmic scale factor
        self.offset_x = 512  # Center of the canvas
        self.offset_y = 512
        self.start_x = 0
        self.start_y = 0
        self.is_dragging = False
        self.is_flipped_horizontally = False  # Flip flags
        self.is_flipped_vertically = False
        self.rotation_point = None  # Custom rotation point
        self.is_rotation_point_mode = False  # Rotation point selection mode

        # Setup main window (buttons window)
        self.setup_buttons_window()

        # Setup image window
        self.setup_image_window()

        # Initialize transparency button
        self.update_transparency_button()

    def setup_buttons_window(self):
        # Remove the fixed position to allow moving the window freely
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create a frame to organize buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Buttons for controlling buttons window transparency
        btn_increase_buttons_transparency = tk.Button(
            btn_frame, text="Increase Buttons Transparency", command=self.increase_buttons_transparency)
        btn_increase_buttons_transparency.grid(row=0, column=0, pady=5, sticky='ew')

        btn_decrease_buttons_transparency = tk.Button(
            btn_frame, text="Decrease Buttons Transparency", command=self.decrease_buttons_transparency)
        btn_decrease_buttons_transparency.grid(row=0, column=1, pady=5, sticky='ew')

        # Toggle transparency button
        self.btn_toggle_transparency = tk.Button(
            btn_frame, text="Set Transparency to Min", command=self.toggle_transparency)
        self.btn_toggle_transparency.grid(row=1, column=0, columnspan=2, pady=5, sticky='ew')

        # Other control buttons
        load_hide_row = 2

        btn_load_image = tk.Button(
            btn_frame, text="Load Image", command=self.load_image)
        btn_load_image.grid(row=load_hide_row, column=0, pady=5, sticky='ew')

        self.btn_hide_show_image = tk.Button(
            btn_frame, text="Hide Image", command=self.toggle_image_window)
        self.btn_hide_show_image.grid(row=load_hide_row, column=1, pady=5, sticky='ew')

        # Flip buttons
        flip_row = load_hide_row + 1

        btn_flip_horizontal = tk.Button(
            btn_frame, text="Flip Horizontal", command=self.flip_image_horizontal)
        btn_flip_horizontal.grid(row=flip_row, column=0, pady=5, sticky='ew')

        btn_flip_vertical = tk.Button(
            btn_frame, text="Flip Vertical", command=self.flip_image_vertical)
        btn_flip_vertical.grid(row=flip_row, column=1, pady=5, sticky='ew')

        # Set Rotation Point button
        set_rotation_point_row = flip_row + 1

        self.btn_set_rotation_point = tk.Button(
            btn_frame, text="Set Rotation Point", command=self.toggle_rotation_point_mode)
        self.btn_set_rotation_point.grid(row=set_rotation_point_row, column=0, columnspan=2, pady=5, sticky='ew')

        # Zoom Level buttons
        zoom_buttons_row = set_rotation_point_row + 1

        btn_zoom_in = tk.Button(
            btn_frame, text="+", command=self.zoom_in)
        btn_zoom_in.grid(row=zoom_buttons_row, column=0, pady=5, sticky='ew')

        btn_zoom_out = tk.Button(
            btn_frame, text="-", command=self.zoom_out)
        btn_zoom_out.grid(row=zoom_buttons_row, column=1, pady=5, sticky='ew')

        # Configure grid weights for equal button sizes
        for i in range(2):
            btn_frame.columnconfigure(i, weight=1)

        # Calculate total number of rows
        total_rows = zoom_buttons_row + 1  # Adjust based on the last row used

        # Configure row weights
        for i in range(total_rows):
            btn_frame.rowconfigure(i, weight=1)

        # Set the transparency of the buttons window
        self.root.attributes('-alpha', self.transparency_level)

    def setup_image_window(self):
        self.image_window = tk.Toplevel(self.root)
        self.image_window.title("Image Window")
        self.image_window.geometry("1600x1024")
        # Remove window decorations
        self.image_window.overrideredirect(True)
        # Set window to be transparent using grey
        self.image_window.attributes('-transparentcolor', 'grey')

        # Center the window on the screen
        screen_width = self.image_window.winfo_screenwidth()
        screen_height = self.image_window.winfo_screenheight()
        x = (screen_width // 2) - (1600 // 2)
        y = (screen_height // 2) - (1024 // 2)
        self.image_window.geometry(f"+{x}+{y}")
        self.image_window.attributes('-topmost', True)
        self.image_window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create the canvas with grey background
        self.canvas = tk.Canvas(self.image_window, width=1600, height=1024,
                                bg='grey', highlightthickness=0, borderwidth=0)
        self.canvas.pack()

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_click)
        if sys.platform.startswith('win'):
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        elif sys.platform == 'darwin':
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        else:
            self.canvas.bind("<Button-4>", lambda event: self.on_mouse_wheel(event))
            self.canvas.bind("<Button-5>", lambda event: self.on_mouse_wheel(event))
        self.canvas.bind("<Button-3>", self.on_right_click)

    def increase_buttons_transparency(self):
        if self.transparency_level > 0.2:
            self.transparency_level -= 0.1
            self.root.attributes('-alpha', self.transparency_level)
        else:
            pass  # Minimum transparency level reached.

    def decrease_buttons_transparency(self):
        if self.transparency_level < 1.0:
            self.transparency_level += 0.1
            self.root.attributes('-alpha', self.transparency_level)
        else:
            pass  # Maximum opacity level reached.

    def toggle_transparency(self):
        if self.image_transparency_level > 0.2:
            self.image_transparency_level = 0.2
            self.btn_toggle_transparency.config(text="Set Transparency to Max")
        else:
            self.image_transparency_level = 1.0
            self.btn_toggle_transparency.config(text="Set Transparency to Min")
        self.draw_image()

    def load_image(self):
        filepath = filedialog.askopenfilename(title="Select an Image", filetypes=[
            ("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.svg")])
        if filepath:
            if filepath.lower().endswith('.svg'):
                try:
                    # Convert SVG to PNG using cairosvg
                    png_data = cairosvg.svg2png(url=filepath)
                    self.image_original = Image.open(
                        io.BytesIO(png_data)).convert("RGBA")
                except Exception as e:
                    return
            else:
                self.image_original = Image.open(filepath).convert("RGBA")
            self.angle = 0
            self.scale = 1.0  # Reset scale
            self.scale_log = 0
            self.offset_x = 512  # Reset position to center
            self.offset_y = 512

            # Reset image transparency to fully opaque
            self.image_transparency_level = 1.0
            self.btn_toggle_transparency.config(text="Set Transparency to Min")

            # Reset flip flags
            self.is_flipped_horizontally = False
            self.is_flipped_vertically = False

            # Reset rotation point
            self.rotation_point = None
            self.is_rotation_point_mode = False
            self.btn_set_rotation_point.config(text="Set Rotation Point")

            self.draw_image()

            if not self.image_window_visible:
                self.toggle_image_window()

    def draw_image(self):
        if self.image_original is None:
            return
        # Apply transformations
        img = self.image_original.copy()

        # Apply transparency first
        if self.image_transparency_level < 1.0:
            # Adjust the alpha channel directly
            alpha = img.getchannel('A')
            alpha = alpha.point(lambda p: int(p * self.image_transparency_level))
            img.putalpha(alpha)

        # Resize
        img = img.resize((int(img.width * self.scale), int(img.height * self.scale)),
                         Image.LANCZOS)

        # Apply flips if necessary
        if self.is_flipped_horizontally:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if self.is_flipped_vertically:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)

        # Rotate around the custom rotation point if set
        if self.rotation_point:
            # Corrected calculation of rotation center
            rotation_center = (
                self.rotation_point[0] - (self.offset_x - img.width / 2),
                self.rotation_point[1] - (self.offset_y - img.height / 2)
            )
            img = img.rotate(self.angle, expand=True, center=rotation_center)
        else:
            img = img.rotate(self.angle, expand=True)

        self.image_display = ImageTk.PhotoImage(img)
        self.canvas.delete("all")

        # Draw the image at the offset position
        self.canvas.create_image(
            self.offset_x, self.offset_y, image=self.image_display)

        # Optionally, draw a marker at the rotation point
        if self.rotation_point:
            # Reduced dot size by 25%
            radius = 1.5
            self.canvas.create_oval(
                self.rotation_point[0]-radius, self.rotation_point[1]-radius,
                self.rotation_point[0]+radius, self.rotation_point[1]+radius,
                fill='red', outline='')

        self.image_window.update_idletasks()

    def on_canvas_click(self, event):
        if self.is_rotation_point_mode:
            # Set the rotation point
            self.rotation_point = (event.x, event.y)
            self.is_rotation_point_mode = False
            self.btn_set_rotation_point.config(text="Set Rotation Point")
            self.draw_image()

    def on_mouse_down(self, event):
        if not self.is_rotation_point_mode:
            self.is_dragging = True
            self.start_x = event.x_root
            self.start_y = event.y_root

    def on_mouse_up(self, event):
        self.is_dragging = False

    def on_mouse_move(self, event):
        if self.is_dragging:
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y
            if event.state & 0x0004:  # If Ctrl key is held down
                self.angle += dx * 0.1  # Reduced rotation sensitivity
                self.angle %= 360  # Keep angle within 0-360 degrees
            else:
                self.offset_x += dx
                self.offset_y += dy
            self.start_x = event.x_root
            self.start_y = event.y_root
            self.draw_image()

    def on_mouse_wheel(self, event):
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

        old_scale = self.scale
        self.scale_log += delta * 0.05  # Reduce sensitivity
        self.scale = pow(2, self.scale_log)
        # Limit scale
        self.scale = max(0.1, min(self.scale, 10.0))
        self.scale_log = math.log2(self.scale)  # Recalculate after clamping

        self.draw_image()

    def zoom_in(self):
        self.scale += 0.05
        self.scale = min(self.scale, 10.0)
        self.scale_log = math.log2(self.scale)
        self.draw_image()

    def zoom_out(self):
        self.scale -= 0.05
        self.scale = max(self.scale, 0.1)
        self.scale_log = math.log2(self.scale)
        self.draw_image()

    def on_right_click(self, event=None):
        self.angle = 0
        self.scale = 1.0  # Reset scale to default zoom level
        self.scale_log = 0
        self.offset_x = 512  # Reset position to center
        self.offset_y = 512

        self.image_transparency_level = 1.0  # Reset image transparency
        self.btn_toggle_transparency.config(text="Set Transparency to Min")

        # Reset flip flags
        self.is_flipped_horizontally = False
        self.is_flipped_vertically = False

        # Reset rotation point
        self.rotation_point = None
        self.is_rotation_point_mode = False
        self.btn_set_rotation_point.config(text="Set Rotation Point")

        self.draw_image()

    def flip_image_horizontal(self):
        self.is_flipped_horizontally = not self.is_flipped_horizontally
        self.draw_image()

    def flip_image_vertical(self):
        self.is_flipped_vertically = not self.is_flipped_vertically
        self.draw_image()

    def toggle_rotation_point_mode(self):
        if not self.is_rotation_point_mode:
            self.is_rotation_point_mode = True
            self.btn_set_rotation_point.config(text="Cancel Set Rotation Point")
            # No popup window
        else:
            self.is_rotation_point_mode = False
            self.btn_set_rotation_point.config(text="Set Rotation Point")
            self.rotation_point = None  # Reset rotation point
            self.draw_image()

    def toggle_image_window(self):
        if self.image_window_visible:
            self.image_window.withdraw()
            self.image_window_visible = False
            self.btn_hide_show_image.config(text="Show Image")
        else:
            self.image_window.deiconify()
            self.image_window_visible = True
            self.btn_hide_show_image.config(text="Hide Image")

    def update_transparency_button(self):
        # Update the button text based on the current transparency level
        if self.image_transparency_level <= 0.2:
            self.btn_toggle_transparency.config(text="Set Transparency to Max")
        else:
            self.btn_toggle_transparency.config(text="Set Transparency to Min")

    def on_close(self):
        self.root.destroy()
        sys.exit(0)

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOverlayApp(root)
    root.mainloop()
