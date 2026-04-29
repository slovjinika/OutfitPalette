import colorsys
from PIL import Image, ImageDraw, ImageFont, ImageTk
import math
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- Defaults ---
STEP = 2
CELL_SIZE = 30
PADDING = 2
COLUMNS = 24
BG_COLOR = (255, 255, 255)
HEX_RE = re.compile(r'^#?([0-9a-fA-F]{6})$')

# --- Color utilities (unchanged logic) ---
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

def get_text_size(draw, text, font, cell_size):
    try:
        return draw.textsize(text, font=font)
    except AttributeError:
        try:
            return font.getsize(text)
        except AttributeError:
            return (len(text) * (cell_size // 2), cell_size)

def make_three_column_image(colors_lists, base_hexes, columns, cell_size, padding, bg):
    max_len = max(len(lst) for lst in colors_lists)
    rows = math.ceil(max_len / columns)
    header_height = cell_size + 2*padding
    col_width = columns * cell_size + (columns + 1) * padding
    width = 3 * col_width + 4 * padding
    height = header_height + rows * cell_size + (rows + 1) * padding

    img = Image.new('RGB', (width, height), bg)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", int(cell_size * 0.6))
    except Exception:
        font = ImageFont.load_default()

    labels = ['Hair', 'Eyes', 'Skin']
    for col_idx in range(3):
        x_offset = padding + col_idx * (col_width + padding)
        base_rgb = hex_to_rgb(base_hexes[col_idx])
        header_rect = [x_offset, padding, x_offset + col_width - padding, padding + header_height - padding]
        draw.rectangle(header_rect, fill=base_rgb)

        text = '#' + base_hexes[col_idx].lstrip('#').upper()
        text_color = contrast_text_color(base_rgb)
        text_size = get_text_size(draw, text, font, cell_size)
        text_x = x_offset + 8
        text_y = padding + (header_height - text_size[1]) // 2
        draw.text((text_x, text_y), text, fill=text_color, font=font)

        label_text = labels[col_idx]
        label_width_est = len(label_text) * (cell_size // 2)
        label_x = x_offset + col_width - padding - label_width_est - 6
        label_y = text_y
        draw.text((label_x, label_y), label_text, fill=text_color, font=font)

        lst = colors_lists[col_idx]
        for idx, color in enumerate(lst):
            r = idx % columns
            row = idx // columns
            x0 = x_offset + padding + r * (cell_size + padding)
            y0 = header_height + padding + row * (cell_size + padding)
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            draw.rectangle([x0, y0, x1, y1], fill=color)

    return img

# --- GUI ---
class PaletteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Palette for Hair, Eyes, Skin")
        self.resizable(True, True)

        frm = ttk.Frame(self, padding=8)
        frm.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Inputs
        self.hair_var = tk.StringVar(value="#464531")
        self.eyes_var = tk.StringVar(value="#4e3b31")
        self.skin_var = tk.StringVar(value="#cfb2a4")
        self.step_var = tk.IntVar(value=STEP)
        self.cell_var = tk.IntVar(value=CELL_SIZE)
        self.pad_var = tk.IntVar(value=PADDING)
        self.cols_var = tk.IntVar(value=8)

        left = ttk.Frame(frm)
        left.grid(row=0, column=0, sticky="nw")
        ttk.Label(left, text="Hair HEX:").grid(row=0, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.hair_var, width=12).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(left, text="Eyes HEX:").grid(row=1, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.eyes_var, width=12).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(left, text="Skin HEX:").grid(row=2, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.skin_var, width=12).grid(row=2, column=1, sticky="w", padx=4)

        ttk.Label(left, text="Hue step:").grid(row=3, column=0, sticky="w")
        ttk.Spinbox(left, from_=1, to=360, textvariable=self.step_var, width=6).grid(row=3, column=1, sticky="w", padx=4)
        ttk.Label(left, text="Cell size:").grid(row=4, column=0, sticky="w")
        ttk.Spinbox(left, from_=4, to=500, textvariable=self.cell_var, width=6).grid(row=4, column=1, sticky="w", padx=4)
        ttk.Label(left, text="Padding:").grid(row=5, column=0, sticky="w")
        ttk.Spinbox(left, from_=0, to=100, textvariable=self.pad_var, width=6).grid(row=5, column=1, sticky="w", padx=4)
        ttk.Label(left, text="Columns:").grid(row=6, column=0, sticky="w")
        ttk.Spinbox(left, from_=1, to=200, textvariable=self.cols_var, width=6).grid(row=6, column=1, sticky="w", padx=4)

        btn_frame = ttk.Frame(left)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(8,0))
        ttk.Button(btn_frame, text="Generate Preview", command=self.generate_preview).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="Save Image...", command=self.save_image).grid(row=0, column=1, padx=4)

        # Canvas preview
        self.preview_lbl = ttk.Label(frm)
        self.preview_lbl.grid(row=0, column=1, padx=12, sticky="nsew")
        frm.columnconfigure(1, weight=1)

        self._last_image = None
        self.generate_preview()

    def generate_preview(self):
        hair = self.hair_var.get().strip() or "#464531"
        eyes = self.eyes_var.get().strip() or "#4e3b31"
        skin = self.skin_var.get().strip() or "#cfb2a4"
        try:
            _ = hex_to_rgb(hair); _ = hex_to_rgb(eyes); _ = hex_to_rgb(skin)
        except ValueError as e:
            messagebox.showerror("HEX error", str(e))
            return

        step = max(1, int(self.step_var.get()))
        cell = max(4, int(self.cell_var.get()))
        pad = max(0, int(self.pad_var.get()))
        cols = max(1, int(self.cols_var.get()))

        lists = [
            generate_colors_from_base(hair, step=step),
            generate_colors_from_base(eyes, step=step),
            generate_colors_from_base(skin, step=step),
        ]
        img = make_three_column_image(lists, [hair, eyes, skin],
                                      columns=cols, cell_size=cell, padding=pad, bg=BG_COLOR)
        # Resize preview to fit label if too big
        max_preview = 900
        w, h = img.size
        scale = min(1.0, max_preview / max(w, h))
        if scale < 1.0:
            img_preview = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
        else:
            img_preview = img
        self._last_image = img  # keep full-size for saving
        tk_im = ImageTk.PhotoImage(img_preview)
        self.preview_lbl.configure(image=tk_im)
        self.preview_lbl.image = tk_im

    def save_image(self):
        if self._last_image is None:
            messagebox.showinfo("No image", "Generate preview first.")
            return
        fn = filedialog.asksaveasfilename(defaultextension=".png",
                                          filetypes=[("PNG image","*.png"),("All files","*.*")],
                                          initialfile="hair_eyes_skin_palette.png")
        if not fn:
            return
        try:
            self._last_image.save(fn)
            messagebox.showinfo("Saved", f"Saved image: {fn}")
        except Exception as e:
            messagebox.showerror("Save error", str(e))

if __name__ == "__main__":
    app = PaletteApp()
    app.mainloop()
