import sys
import os
from quantag import QImageCompressor
from PIL import Image

def save_png(array, path):
    img = Image.fromarray(array.astype("uint8"))
    img.save(path, format="PNG")

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_qimage.py <image_file>")
        sys.exit(1)

    img_path = sys.argv[1]
    if not os.path.isfile(img_path):
        print(f"Error: File not found: {img_path}")
        sys.exit(1)

    compressor = QImageCompressor(energy_threshold=0.95)
    result = compressor.compress(img_path)

    print("=== Quantum-Inspired Image Compression ===")
    print(f"Input file: {img_path}")
    print(f"Shape: {result['original'].shape}")
    print(f"Number of components kept (k): {result['k']}")
    print(f"Mean Squared Error (MSE): {result['mse']:.4f}")

    # Save outputs as PNGs
    base, _ = os.path.splitext(img_path)
    save_png(result["reconstructed"], base + "_reconstructed.png")
    save_png(result["compressed"], base + "_compressed.png")

    print("Saved images:")
    print(f" - {base}_reconstructed.png")
    print(f" - {base}_compressed.png")

if __name__ == "__main__":
    main()

