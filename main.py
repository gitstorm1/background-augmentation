import os
import random
from rembg import remove
from PIL import Image

# --- Existing Function ---

def replace_background(input_path: str, background_path: str, output_path: str):
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
    # The 'remove' function returns an Image with transparency (RGBA)
    foreground = remove(input_image)

    # Resize background to match input image size
    # This ensures the composite operation works correctly without cropping the background
    background = background.resize(input_image.size)

    # Composite foreground over new background
    # background is the bottom layer, foreground is the top layer
    result = Image.alpha_composite(background, foreground)

    # Save and return
    result.save(output_path)
    return result

# --- New Modular Function ---

def process_images_with_random_backgrounds(input_dir: str, background_dir: str, output_dir: str):
    """
    Processes all images in the input directory, replacing the background
    of each with a randomly selected image from the background directory.

    Args:
        input_dir (str): Directory containing the foreground images.
        background_dir (str): Directory containing the background images.
        output_dir (str): Directory to save the resulting images.
    """
    # 1. Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 2. Get list of all available backgrounds
    # Filtering for common image extensions is good practice
    background_files = [f for f in os.listdir(background_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not background_files:
        print(f"❌ Error: No image files found in the background directory: {background_dir}")
        return

    # 3. Get list of all input images
    input_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not input_files:
        print(f"❌ Error: No image files found in the input directory: {input_dir}")
        return

    # 4. Loop through each input image
    for filename in input_files:
        try:
            # Construct paths
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            # Select a random background
            random_background_file = random.choice(background_files)
            background_path = os.path.join(background_dir, random_background_file)

            print(f"🔄 Processing '{filename}' with background '{random_background_file}'...")

            # Run the core replacement function
            replace_background(input_path, background_path, output_path)

            print(f"✅ Saved result to '{output_path}'")

        except Exception as e:
            print(f"🛑 Failed to process '{filename}'. Error: {e}")

# --- Main Execution Block ---

if __name__ == "__main__":
    # Define directories based on the provided structure
    base_dir = "images"
    INPUT_DIR = os.path.join(base_dir, "inputs")
    BACKGROUND_DIR = os.path.join(base_dir, "backgrounds")
    OUTPUT_DIR = os.path.join(base_dir, "outputs")

    print("🖼️ Starting image background replacement process...")
    process_images_with_random_backgrounds(INPUT_DIR, BACKGROUND_DIR, OUTPUT_DIR)
    print("✨ Image processing complete.")