#incomplete
from PIL import Image
import os

def captcha_solver(image_path):
    """Reads, displays, and deletes the captcha image."""
    try:
        img = Image.open(image_path)
        img.show()
        captcha_input = input("Enter captcha from image: ")
        img.close()

        os.remove(image_path)
        print(f"[Disposed] Deleted {image_path}")
        return captcha_input
    except Exception as e:
        print(f"[ERROR] Could not read captcha image: {e}")
        return None
