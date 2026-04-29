import colorsys
import re
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk, ImageFont

# --- Default configuration ---
DEFAULT_STEP = 2
DEFAULT_CELL = 30
DEFAULT_PADDING = 2
DEFAULT_COLUMNS = 24
BG_COLOR = (255, 255, 255)

HEX_RE = re.compile(r'^#?([0-9a-fA-F]{6})$')

# --- Conversion and generation functions ---
def hex_to_rgb(hex_str):
    m = HEX_RE.match(hex_str.strip())
    if not m:
        raise ValueError('Invalid HEX format; expected RRGGBB or #RRGGBB')
    s = m.group(1)
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(r, g, b):
    rn, gn, bn = r/255.0, g/255.0, b/255.0
    h, l, s = colorsys.rgb_to_hls(rn, gn, bn)
    return (h * 360.0, s * 100.0, l * 100.0)

def hsl_to_rgb_int(h, s_percent, l_percent):
    h_n = (h % 360) / 360.0
    l_n = l_percent / 100.0
    s_n = s_percent / 100.0
    r, g, b = colorsys.hls_to_rgb(h_n, l_n, s_n)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))

def contrast_text_color(rgb):
    r, g, b = rgb
    yiq = (r*299 + g*587 + b*114) / 1000
    return (0,0,0) if yiq > 128 else (255,255,255)

def generate_colors_from_base(hex_color, step):
    base_rgb = hex_to_rgb(hex_color)
    base_h, base_s, base_l = rgb_to_hsl(*base_rgb)
    colors = []
    for h in range(0, 361, step):
        new_h = (base_h + h) % 360
        colors.append(hsl_to_rgb_int(new_h, base_s, base_l))
    return colors

def make_grid_image(colors, base_hex, columns, cell_size, padding, bg):
    total = len(colors)
    rows = math.ceil(total / columns)
    header_height = cell_size + 2*padding
    width = columns * cell_size + (columns + 1) * padding
    height = header_height + rows * cell_size + (rows + 1) * padding

    img = Image.new('RGB', (width, height), bg)
    draw = ImageDraw.Draw(img)

    base_rgb = hex_to_rgb(base_hex)
    header_rect = [0 + padding, 0 + padding, width - padding, header_height - padding]
    draw.rectangle(header_rect, fill=base_rgb)

    text = '#' + base_hex.lstrip('#').upper()
    try:
        font = ImageFont.truetype("arial.ttf", int(cell_size * 0.6))
    except Exception:
        font = ImageFont.load_default()

    # vertically center text inside header
    text_color = contrast_text_color(base_rgb)
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0,0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    else:
        text_w, text_h = font.getsize(text)

    text_x = padding + 8
    text_y = (header_height - text_h) // 2
    draw.text((text_x, text_y), text, fill=text_color, font=font)

    for idx, color in enumerate(colors):
        col = idx % columns
        row = idx // columns
        x0 = padding + col * (cell_size + padding)
        y0 = header_height + padding + row * (cell_size + padding)
        x1 = x0 + cell_size
        y1 = y0 + cell_size
        draw.rectangle([x0, y0, x1, y1], fill=color)

    return img

# --- GUI ---
class App:
    def __init__(self, root):
        self.root = root
        root.title("Outfit Palette")

        frm = ttk.Frame(root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        # Input fields
        ttk.Label(frm, text="HEX:").grid(row=0, column=0, sticky="w")
        self.hex_var = tk.StringVar(value="#4a3f22")
        self.hex_entry = ttk.Entry(frm, textvariable=self.hex_var, width=12)
        self.hex_entry.grid(row=0, column=1, sticky="w")

        ttk.Label(frm, text="Step (deg):").grid(row=1, column=0, sticky="w")
        self.step_var = tk.IntVar(value=DEFAULT_STEP)
        ttk.Entry(frm, textvariable=self.step_var, width=6).grid(row=1, column=1, sticky="w")

        ttk.Label(frm, text="Cell size:").grid(row=2, column=0, sticky="w")
        self.cell_var = tk.IntVar(value=DEFAULT_CELL)
        ttk.Entry(frm, textvariable=self.cell_var, width=6).grid(row=2, column=1, sticky="w")

        ttk.Label(frm, text="Padding:").grid(row=3, column=0, sticky="w")
        self.pad_var = tk.IntVar(value=DEFAULT_PADDING)
        ttk.Entry(frm, textvariable=self.pad_var, width=6).grid(row=3, column=1, sticky="w")

        ttk.Label(frm, text="Columns:").grid(row=4, column=0, sticky="w")
        self.col_var = tk.IntVar(value=DEFAULT_COLUMNS)
        ttk.Entry(frm, textvariable=self.col_var, width=6).grid(row=4, column=1, sticky="w")

        # Buttons
        btn_preview = ttk.Button(frm, text="Preview", command=self.preview)
        btn_preview.grid(row=5, column=0, pady=6)
        btn_save = ttk.Button(frm, text="Save PNG...", command=self.save_png)
        btn_save.grid(row=5, column=1, pady=6)

        # Canvas for preview
        self.preview_canvas = tk.Canvas(root, width=800, height=400, bg="#ffffff")
        self.preview_canvas.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        self.tk_image = None  # reference to PhotoImage

        # Initial preview
        self.preview()

    def preview(self):
        hex_text = self.hex_var.get().strip()
        try:
            _ = hex_to_rgb(hex_text)
        except Exception as e:
            messagebox.showerror("Error", f"Invalid HEX: {e}")
            return

        step = max(1, int(self.step_var.get()))
        cell = max(4, int(self.cell_var.get()))
        pad = max(0, int(self.pad_var.get()))
        cols = max(1, int(self.col_var.get()))

        colors = generate_colors_from_base(hex_text, step)
        img = make_grid_image(colors, hex_text, cols, cell, pad, BG_COLOR)

        # Scale image for canvas if too large
        canvas_w = max(200, self.preview_canvas.winfo_width())
        canvas_h = max(100, self.preview_canvas.winfo_height())
        img_w, img_h = img.size
        scale = min(canvas_w / img_w, canvas_h / img_h, 1.0)
        if scale < 1.0:
            new_size = (int(img_w * scale), int(img_h * scale))
            display_img = img.resize(new_size, Image.LANCZOS)
        else:
            display_img = img

        self.tk_image = ImageTk.PhotoImage(display_img)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(10, 10, anchor="nw", image=self.tk_image)

    def save_png(self):
        hex_text = self.hex_var.get().strip()
        try:
            _ = hex_to_rgb(hex_text)
        except Exception as e:
            messagebox.showerror("Error", f"Invalid HEX: {e}")
            return

        step = max(1, int(self.step_var.get()))
        cell = max(4, int(self.cell_var.get()))
        pad = max(0, int(self.pad_var.get()))
        cols = max(1, int(self.col_var.get()))

        colors = generate_colors_from_base(hex_text, step)
        img = make_grid_image(colors, hex_text, cols, cell, pad, BG_COLOR)

        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files","*.png")],
                                                 initialfile=f"hue_grid_{hex_text.lstrip('#')}.png")
        if not file_path:
            return
        try:
            img.save(file_path)
            messagebox.showinfo("Saved", f"File saved as:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
