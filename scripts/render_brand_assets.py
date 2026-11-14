from pathlib import Path
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCALE = 16
SIZE = 64 * SCALE


def point(value: float) -> int:
    return round(value * SCALE)


canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)

draw.ellipse(
    (point(4), point(4), point(60), point(60)),
    fill="#0b0c09",
    outline="#f39c12",
    width=point(3),
)
draw.arc(
    (point(16), point(16), point(48), point(48)),
    start=48,
    end=312,
    fill="#f4f4ef",
    width=point(7),
)
draw.ellipse(
    (point(43), point(29), point(49), point(35)),
    fill="#f39c12",
)

master = canvas.resize((512, 512), Image.Resampling.LANCZOS)
master.save(ROOT / "favicon.png", optimize=True)
master.save(ROOT / "brand-mark.png", optimize=True)
master.save(
    ROOT / "favicon.ico",
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)

print("Rendered favicon.png, favicon.ico, and brand-mark.png")
