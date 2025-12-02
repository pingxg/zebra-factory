from PIL import Image, ImageDraw, ImageFont
import base64
import io

# Create a new image with white background
# Size: width 80, height 50 (scaled up for better quality, will resize in html)
width = 120
height = 80
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

# Draw ellipse
# Leave some padding
padding = 2
draw.ellipse([padding, padding, width-padding, height-padding], outline='black', width=3)

# Draw text
# Assuming default font availability, or try to load arial
try:
    font = ImageFont.truetype("arial.ttf", 20)
    font_bold = ImageFont.truetype("arialbd.ttf", 22)
    font_small = ImageFont.truetype("arial.ttf", 18)
except IOError:
    font = ImageFont.load_default()
    font_bold = font
    font_small = font

# Calculate text positions
# FI
text1 = "FI"
# 1428
text2 = "1428"
# EY
text3 = "EY"

# Helper to center text
def draw_centered_text(draw, text, font, y_pos):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x_pos = (width - text_width) / 2
    draw.text((x_pos, y_pos), text, fill="black", font=font)

# Adjust Y positions
draw_centered_text(draw, text1, font_small, 10)
draw_centered_text(draw, text2, font_bold, 28)
draw_centered_text(draw, text3, font_small, 50)

# Save to buffer
buffered = io.BytesIO()
image.save(buffered, format="PNG")
img_str = base64.b64encode(buffered.getvalue()).decode()

print(img_str)

