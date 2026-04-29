import colorsys
from PIL import Image, ImageDraw, ImageFont
import math
import re

# --- Default settings ---
STEP = 2
CELL_SIZE = 30
PADDING = 2
COLUMNS = 24
BG_COLOR = (255, 255, 255)

HEX_RE = re.compile(r'^#?([0-9a-fA-F]{6})$')

# --- Conversion utilities ---
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

    text_color = contrast_text_color(base_rgb)
    text_size = get_text_size(draw, text, font, cell_size)
    text_x = padding + 8
    text_y = (header_height - text_size[1]) // 2
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

# --- Console interface ---
def prompt_int(prompt, default, min_val=None, max_val=None):
    while True:
        s = input(f"{prompt} [{default}]: ").strip()
        if not s:
            return default
        try:
            v = int(s)
        except ValueError:
            print("Enter an integer.")
            continue
        if min_val is not None and v < min_val:
            print(f"Must be >= {min_val}.")
            continue
        if max_val is not None and v > max_val:
            print(f"Must be <= {max_val}.")
            continue
        return v

def main():
    print("=== Outfit Palette (console) ===")
    user_hex = input('Enter HEX color (e.g. #4a3f2b): ').strip()
    try:
        _ = hex_to_rgb(user_hex)
    except ValueError as e:
        print('Error:', e)
        return

    step = prompt_int("Hue step (degrees)", STEP, 1, 360)
    cell_size = prompt_int("Cell size (px)", CELL_SIZE, 4, 500)
    padding = prompt_int("Padding between cells (px)", PADDING, 0, 100)
    columns = prompt_int("Number of columns", COLUMNS, 1, 200)

    # Show base color in console (with RGB)
    base_rgb = hex_to_rgb(user_hex)
    print(f"Input color: #{user_hex.lstrip('#').upper()}  RGB{base_rgb}")

    colors = generate_colors_from_base(user_hex, step=step)
    img = make_grid_image(colors, user_hex, columns=columns, cell_size=cell_size, padding=padding, bg=BG_COLOR)

    out_name_default = 'hue_grid_from_' + user_hex.lstrip('#') + '.png'
    out_name = input(f"Filename to save [{out_name_default}]: ").strip() or out_name_default
    try:
        img.save(out_name)
        print(f'Saved {len(colors)} colors to file "{out_name}"')
    except Exception as e:
        print("Error saving file:", e)

if __name__ == '__main__':
    main()
