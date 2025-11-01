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
    
    # Apply EXIF rotation correction to both images
    input_image = ImageOps.exif_transpose(input_image)
    background = ImageOps.exif_transpose(background)

    # Remove background using U²-Net
    # 'foreground' will have the size of the corrected 'input_image'
    foreground = remove(input_image)

    # Resize background to match input image size
    background = background.resize(input_image.size)

    # Composite foreground over new background
    result = Image.alpha_composite(background, foreground)
    
    # Convert to RGB before saving (as the new background removed transparency need)
    result = result.convert("RGB")

    # Save and return
    result.save(output_path)
    return result

def process_single_image(relative_path: str, input_dir: str, background_dir: str, output_dir: str, background_files: list):
    """
    Worker function to process a single image, now using a relative path 
    to preserve directory structure.
    """
    try:
        # 1. Calculate Full Paths
        input_path = os.path.join(input_dir, relative_path)
        
        # Determine the target output directory and ensure it exists
        # relative_path includes the full subdirectory path, e.g., 'sub1/image.jpg'
        output_dir_for_file = os.path.join(output_dir, os.path.dirname(relative_path))
        os.makedirs(output_dir_for_file, exist_ok=True)
        
        # 2. Determine Output Path (with forced .png extension)
        base_name = os.path.splitext(os.path.basename(relative_path))[0]
        output_filename = base_name + ".png"
        output_path = os.path.join(output_dir_for_file, output_filename)

        # 3. Select Random Background
        random_background_file = random.choice(background_files)
        background_path = os.path.join(background_dir, random_background_file)

        print(f"🔄 Processing '{relative_path}' with background '{random_background_file}'...")

        # 4. Run Core Replacement
        replace_background(input_path, background_path, output_path)

        return f"✅ Success: '{relative_path}' -> '{os.path.relpath(output_path, output_dir)}'"

    except Exception as e:
        return f"🛑 Failed to process '{relative_path}'. Error: {e}"


def process_images_in_parallel(input_dir: str, background_dir: str, output_dir: str):
    """Orchestrates parallel image processing, recursively searching input_dir."""
    
    os.makedirs(output_dir, exist_ok=True)

    # 1. Get list of all available backgrounds
    background_files = [f for f in os.listdir(background_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not background_files:
        print("❌ Error: No image files found in the background directory.")
        return
        
    # 2. Recursively find all input image paths
    # We store paths relative to input_dir to recreate the structure later
    relative_input_paths = []
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')
    
    # os.walk traverses the input directory and its subdirectories
    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                # Calculate the path relative to the input_dir
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, input_dir)
                relative_input_paths.append(relative_path)
                
    if not relative_input_paths:
        print("❌ Error: No image files found in the input directory or its subdirectories.")
        return

    # 3. Parallel Execution Setup
    # Use a cautious number of workers to prevent system hang
    SAFE_WORKERS = 4 
    print(f"Starting execution with {SAFE_WORKERS} worker processes...")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=SAFE_WORKERS) as executor:
        
        futures = []
        for relative_path in relative_input_paths:
            # Submitting the relative path, which holds the directory structure information
            future = executor.submit(
                process_single_image,
                relative_path, # Path including subdirectories, e.g., 'sub/img.jpg'
                input_dir,
                background_dir,
                output_dir,
                background_files
            )
            futures.append(future)

        # Collect results as they complete
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