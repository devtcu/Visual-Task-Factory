"""Deterministic contact image for records that need several complete visuals."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def make_overview(paths, target):
    opened = [Image.open(p).convert("RGB") for p in paths]
    gap = 44
    width = max(im.width for im in opened)
    canvas = Image.new("RGB", (width, sum(im.height + gap for im in opened)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=24)
    y = 0
    for i, im in enumerate(opened, 1):
        draw.text((12, y + 8), f"Image {i}", font=font, fill="black")
        canvas.paste(im, (0, y + gap)); y += gap + im.height
        im.close()
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG")
