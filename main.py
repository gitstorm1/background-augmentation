import os
import random
import concurrent.futures
from rembg import remove
from PIL import Image, ImageOps

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
    
    input_image = ImageOps.exif_transpose(input_image)
    background = ImageOps.exif_transpose(background)

    # Remove background using U²-Net
    # The 'remove' function returns an Image with transparency (RGBA)
    foreground = remove(input_image)

    # Resize background to match input image size
    # This ensures the composite operation works correctly without cropping the background
    background = background.resize(input_image.size)

    # Composite foreground over new background
    # background is the bottom layer, foreground is the top layer
    result = Image.alpha_composite(background, foreground)
    
    result = result.convert("RGB")

    # Save and return
    result.save(output_path)
    return result

def process_single_image(filename: str, input_dir: str, background_dir: str, output_dir: str, background_files: list):
    """Worker function to process a single image, suitable for a ProcessPoolExecutor."""
    try:
        # Construct paths
        input_path = os.path.join(input_dir, filename)
        
        # Determine output path, forcing .png extension for safety
        base_name = os.path.splitext(filename)[0]
        output_filename = base_name + ".png"
        output_path = os.path.join(output_dir, output_filename)

        # Select a random background
        random_background_file = random.choice(background_files)
        background_path = os.path.join(background_dir, random_background_file)

        print(f"🔄 Processing '{filename}' with background '{random_background_file}'...")

        # Run the core replacement function
        replace_background(input_path, background_path, output_path)

        return f"✅ Success: '{filename}'"

    except Exception as e:
        return f"🛑 Failed to process '{filename}'. Error: {e}"


def process_images_in_parallel(input_dir: str, background_dir: str, output_dir: str):
    """Orchestrates parallel image processing."""
    
    os.makedirs(output_dir, exist_ok=True)

    # Get lists of files
    background_files = [f for f in os.listdir(background_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    input_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not background_files or not input_files:
        print("❌ Error: Check input and background directories.")
        return

    # Use a ProcessPoolExecutor to distribute work across CPU cores
    # max_workers=None uses the number of cores on the machine
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        
        # Prepare arguments for the worker function
        futures = []
        for filename in input_files:
            # Submitting the task to the pool
            future = executor.submit(
                process_single_image,
                filename,
                input_dir,
                background_dir,
                output_dir,
                background_files
            )
            futures.append(future)

        # Collect results as they complete (in the order they complete)
        for future in concurrent.futures.as_completed(futures):
            print(future.result())

# --- Main Execution Block ---

if __name__ == "__main__":
    base_dir = "images"
    INPUT_DIR = os.path.join(base_dir, "inputs")
    BACKGROUND_DIR = os.path.join(base_dir, "backgrounds")
    OUTPUT_DIR = os.path.join(base_dir, "outputs")

    print("🖼️ Starting PARALLEL image background replacement process...")
    process_images_in_parallel(INPUT_DIR, BACKGROUND_DIR, OUTPUT_DIR)
    print("✨ Parallel image processing complete.")