import os
from PIL import Image

# Target minimum pixel size for the smallest image dimension
MIN_DIMENSION = 350
# Name of subdirectory where resized images will be stored
RESIZED_FOLDER_NAME = "resized_backgrounds" 

def resize_image_to_min_350(input_path: str, output_path: str):
    """
    Resizes an image so that its *smallest* dimension is exactly MIN_DIMENSION (350), 
    *only* if that smallest dimension is currently LARGER than MIN_DIMENSION.
    This effectively scales down large images to reduce memory consumption.
    """
    try:
        with Image.open(input_path) as img:
            width, height = img.size
            
            smallest_dim = min(width, height)

            if smallest_dim > MIN_DIMENSION:
                # Scale down images where smallest dimension exceeds threshold to reduce memory usage
                scale_factor = MIN_DIMENSION / smallest_dim
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Ensure RGB format for compatibility (RGBA not needed without transparency)
                if resized_img.mode == 'RGBA':
                    resized_img = resized_img.convert('RGB')
                    
                resized_img.save(output_path, quality=90)
                print(f"✅ Resized: {os.path.basename(input_path)} from ({width}x{height}) to ({new_width}x{new_height})")

            elif smallest_dim < MIN_DIMENSION:
                # Images smaller than minimum are copied as-is (no upscaling to preserve quality)
                img.save(output_path, quality=90)
                print(f"⚠️ Copied (Too Small): {os.path.basename(input_path)} ({width}x{height})")
                
            else:
                # Images already at exact minimum dimension are copied without modification
                img.save(output_path, quality=90)
                print(f"✔️ Copied (Exact Fit): {os.path.basename(input_path)} ({width}x{height})")


    except Exception as e:
        print(f"🛑 Failed to process {os.path.basename(input_path)}. Error: {e}")

def scan_and_resize_backgrounds(input_directory: str):
    """
    Scans the specified directory for images and resizes them, saving the 
    results to a new folder within the input directory.
    
    Args:
        input_directory (str): Path to the folder containing the images.
    """
    
    # Create output subdirectory within the input directory for resized images
    output_directory = os.path.join(input_directory, RESIZED_FOLDER_NAME)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"\nCreated output directory: {output_directory}")

    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')
    
    print(f"\nScanning directory '{input_directory}' for images to resize (min dimension: {MIN_DIMENSION}px)...")

    # Process each image file found in the directory
    for filename in os.listdir(input_directory):
        # Prevent processing the output folder if it's in the listing
        if filename == RESIZED_FOLDER_NAME:
            continue
            
        if filename.lower().endswith(IMAGE_EXTENSIONS):
            input_path = os.path.join(input_directory, filename)
            output_path = os.path.join(output_directory, filename)
            
            resize_image_to_min_350(input_path, output_path)
            
    print("\n✨ Batch resizing complete.")


if __name__ == "__main__":
    # Set target directory containing background images to resize
    BACKGROUND_DIR_PATH = "images/backgrounds" 
    
    # Validate directory exists before attempting to process
    if not os.path.isdir(BACKGROUND_DIR_PATH):
        print(f"❌ Error: Directory not found at path: {BACKGROUND_DIR_PATH}")
        print("Please set the 'BACKGROUND_DIR_PATH' variable to your correct background image folder.")
    else:
        scan_and_resize_backgrounds(BACKGROUND_DIR_PATH)