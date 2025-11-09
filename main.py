import os
import random
import concurrent.futures
from rembg import remove
from PIL import Image, ImageOps

def replace_background(input_path: str, background_path: str, output_path: str):
    """
    Replace the background of an image using U2-Net (via rembg).

    Args:
        input_path (str): Path to input image (with subject).
        background_path (str): Path to new background image.
        output_path (str): Path to save the final composite.

    Returns:
        Image.Image: Resulting image with replaced background.
    """
    # Load both images in RGBA mode to support transparency operations
    input_image = Image.open(input_path).convert("RGBA")
    background = Image.open(background_path).convert("RGBA")
    
    # Correct orientation based on EXIF data to prevent rotated output
    input_image = ImageOps.exif_transpose(input_image)
    background = ImageOps.exif_transpose(background)

    # Extract foreground by removing original background using AI model
    foreground = remove(input_image)
    # Resize background to exactly match input dimensions for proper compositing
    background = background.resize(input_image.size)
    # Layer foreground (subject) on top of new background
    result = Image.alpha_composite(background, foreground)
    # Convert final result to RGB since transparency is no longer needed
    result = result.convert("RGB")
    result.save(output_path)
    return result

def process_single_image(relative_path: str, input_dir: str, background_dir: str, output_dir: str, background_files: list):
    """
    Worker function to process a single image, using a relative path 
    to preserve directory structure.
    """
    try:
        # Reconstruct full input path from base directory and relative path
        input_path = os.path.join(input_dir, relative_path)
        # Preserve subdirectory structure in output by extracting parent directory from relative path
        output_dir_for_file = os.path.join(output_dir, os.path.dirname(relative_path))
        os.makedirs(output_dir_for_file, exist_ok=True)
        
        # Extract base filename without extension and force PNG output format
        base_name = os.path.splitext(os.path.basename(relative_path))[0]
        output_filename = base_name + ".png"
        output_path = os.path.join(output_dir_for_file, output_filename)

        # Randomly select one background from available pool
        random_background_file = random.choice(background_files)
        background_path = os.path.join(background_dir, random_background_file)

        print(f"Processing '{relative_path}' with background '{random_background_file}'...")

        # Perform the actual background replacement operation
        replace_background(input_path, background_path, output_path)

        return f"Success: '{relative_path}' -> '{os.path.relpath(output_path, output_dir)}'"

    except Exception as e:
        return f"Failed to process '{relative_path}'. Error: {e}"


def process_images_in_parallel(input_dir: str, background_dir: str, output_dir: str):
    """Orchestrates parallel image processing, recursively searching input_dir."""
    
    os.makedirs(output_dir, exist_ok=True)

    # Collect all valid background images from the background directory
    background_files = [f for f in os.listdir(background_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not background_files:
        print("Error: No image files found in the background directory.")
        return
        
    # Recursively scan input directory and build list of relative paths to preserve structure
    relative_input_paths = []
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')
    
    # Walk through all subdirectories to find image files
    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                full_path = os.path.join(root, filename)
                # Store relative path to maintain subdirectory hierarchy in output
                relative_path = os.path.relpath(full_path, input_dir)
                relative_input_paths.append(relative_path)
                
    if not relative_input_paths:
        print("Error: No image files found in the input directory or its subdirectories.")
        return

    # Limit worker count to avoid overwhelming system resources
    SAFE_WORKERS = 12
    print(f"Starting execution with {SAFE_WORKERS} worker processes...")
    
    # Execute image processing tasks in parallel using process pool
    with concurrent.futures.ProcessPoolExecutor(max_workers=SAFE_WORKERS) as executor:
        futures = []
        # Submit all processing tasks to the executor
        for relative_path in relative_input_paths:
            future = executor.submit(
                process_single_image,
                relative_path,
                input_dir,
                background_dir,
                output_dir,
                background_files
            )
            futures.append(future)

        # Display results as tasks complete (not necessarily in submission order)
        for future in concurrent.futures.as_completed(futures):
            print(future.result())


if __name__ == "__main__":
    # Define directory structure under base 'images' folder
    base_dir = "images"
    INPUT_DIR = os.path.join(base_dir, "inputs")
    BACKGROUND_DIR = os.path.join(base_dir, "backgrounds")
    OUTPUT_DIR = os.path.join(base_dir, "outputs")

    print("Starting PARALLEL image background replacement process...")
    # Process all images with random background assignment
    process_images_in_parallel(INPUT_DIR, BACKGROUND_DIR, OUTPUT_DIR)
    print("Parallel image processing complete.")