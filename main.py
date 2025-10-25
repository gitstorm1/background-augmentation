from rembg import remove
from PIL import Image

def replace_background(input_path: str, background_path: str, output_path="images/output.png"):
    """
    Replace the background of an image using U²-Net (via rembg).

    Args:
        input_path (str): Path to input image (with subject).
        background_path (str): Path to new background image.
        output_path (str): Path to save the final composite.

    Returns:
        Image.Image: Resulting image with replaced background.
    """
    # Load images
    input_image = Image.open(input_path).convert("RGBA")
    background = Image.open(background_path).convert("RGBA")

    # Remove background using U²-Net
    foreground = remove(input_image)

    # Resize background to match input
    background = background.resize(input_image.size)

    # Composite foreground over new background
    result = Image.alpha_composite(background, foreground)

    # Save and return
    result.save(output_path)
    return result

replace_background("images/i.jpg", "images/b.jpg")