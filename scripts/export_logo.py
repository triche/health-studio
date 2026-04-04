"""Convert SVG logo to PNG and ICO assets."""
import cairosvg
from PIL import Image

# Ensure public dir exists
import os
os.makedirs("frontend/public", exist_ok=True)

# SVG -> PNG at 512px
cairosvg.svg2png(url="assets/logo.svg", write_to="frontend/public/logo.png", output_width=512, output_height=512)
print("Created frontend/public/logo.png (512x512)")

# Favicon sizes
for size in [16, 32, 48]:
    cairosvg.svg2png(url="assets/logo.svg", write_to=f"/tmp/favicon_{size}.png", output_width=size, output_height=size)

# Create ICO with multiple sizes
imgs = []
for size in [16, 32, 48]:
    img = Image.open(f"/tmp/favicon_{size}.png")
    imgs.append(img)
imgs[0].save("frontend/public/favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)], append_images=imgs[1:])
print("Created frontend/public/favicon.ico")

# 192px PNG for PWA/mobile
cairosvg.svg2png(url="assets/logo.svg", write_to="frontend/public/logo-192.png", output_width=192, output_height=192)
print("Created frontend/public/logo-192.png (192x192)")
