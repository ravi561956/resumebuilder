from PIL import Image

def resize_image(image_path, size):
    img = Image.open(image_path)
    img = img.convert("RGB")
    img.thumbnail(size, Image.Resampling.LANCZOS)
    img.save(image_path, optimize=True, quality=85)
