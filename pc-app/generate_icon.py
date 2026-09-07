"""Generates redlight.ico from the brand mark - the same glowing red
dot with a bezel ring and specular highlight used on the logo sheet
and packaging. Run once (or after a brand tweak) to regenerate:

    python generate_icon.py
"""

from PIL import Image, ImageDraw, ImageFilter

ACCENT = (179, 39, 31)       # #b3271f
ACCENT_DARK = (122, 26, 21)  # #7a1a15
ACCENT_LIGHT = (217, 74, 63) # #d94a3f

SIZE = 1024  # supersampled, then downscaled for anti-aliased edges


def make_mark():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # Soft outer glow
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    r_glow = int(SIZE * 0.455)
    cx = cy = SIZE // 2
    gd.ellipse([cx - r_glow, cy - r_glow, cx + r_glow, cy + r_glow], fill=ACCENT + (36,))
    glow = glow.filter(ImageFilter.GaussianBlur(SIZE * 0.03))
    img = Image.alpha_composite(img, glow)

    # Main filled circle with a darker bezel ring
    main = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    md = ImageDraw.Draw(main)
    r_main = int(SIZE * 0.34)
    stroke = max(2, int(SIZE * 0.018))
    md.ellipse(
        [cx - r_main, cy - r_main, cx + r_main, cy + r_main],
        fill=ACCENT_LIGHT + (255,),
        outline=ACCENT_DARK + (255,),
        width=stroke,
    )
    img = Image.alpha_composite(img, main)

    # Specular highlight, upper-left
    hl = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hx, hy = int(SIZE * 0.41), int(SIZE * 0.385)
    hrx, hry = int(SIZE * 0.10), int(SIZE * 0.068)
    hd.ellipse([hx - hrx, hy - hry, hx + hrx, hy + hry], fill=(255, 255, 255, 90))
    hl = hl.filter(ImageFilter.GaussianBlur(SIZE * 0.012))
    img = Image.alpha_composite(img, hl)

    return img


if __name__ == "__main__":
    mark = make_mark()
    sizes = [256, 128, 64, 48, 32, 16]
    mark.save(
        "redlight.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
    )
    print("wrote redlight.ico")
