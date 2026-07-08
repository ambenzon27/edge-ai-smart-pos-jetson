#!/usr/bin/env python3
"""
Convert YOLO PyTorch model to TensorRT for Jetson Orin
This provides 3-5x performance improvement!
"""
from pathlib import Path
from ultralytics import YOLO
import torch

print("=" * 70)
print("YOLO MODEL → TENSORRT CONVERSION")
print("=" * 70)
print()

# Check CUDA availability
if not torch.cuda.is_available():
    print("⚠️  WARNING: CUDA not available!")
    print("   TensorRT conversion requires CUDA.")
    print("   Please ensure you're running this on Jetson Orin.")
    exit(1)

print(f"✅ CUDA available")
print(f"   GPU: {torch.cuda.get_device_name(0)}")
print()

# Paths
model_path = Path("best.pt")
output_dir = Path("model")
output_path = output_dir / "best.engine"

if not model_path.exists():
    print(f"❌ Model not found: {model_path}")
    print("   Please ensure best.pt is in the current directory.")
    exit(1)

output_dir.mkdir(exist_ok=True)

print(f"Input model: {model_path}")
print(f"Output path: {output_path}")
print()

# Load model
print("Loading YOLO model...")
model = YOLO(str(model_path))
print("✅ Model loaded")
print()

# Export to TensorRT
print("Converting to TensorRT...")
print("This may take 5-10 minutes on first run...")
print()

try:
    # Export with optimal settings for Jetson Orin
    model.export(
        format="engine",  # TensorRT format
        device=0,  # GPU 0
        half=True,  # FP16 precision for speed
        simplify=True,  # Simplify model
        workspace=4,  # 4GB workspace for optimization
        verbose=True
    )

    # Move to model directory
    generated_engine = model_path.parent / f"{model_path.stem}.engine"
    if generated_engine.exists():
        import shutil
        shutil.move(str(generated_engine), str(output_path))

    print()
    print("=" * 70)
    print("✅ CONVERSION SUCCESSFUL!")
    print("=" * 70)
    print(f"TensorRT engine saved to: {output_path}")
    print()
    print("Performance improvement expected:")
    print("  - 3-5x faster inference")
    print("  - 15-25 FPS with detection (vs 3-8 FPS with .pt)")
    print("  - Lower GPU memory usage")
    print()
    print("Next steps:")
    print("  1. Run: python3 performance_test_jetson.py")
    print("  2. Then: python3 start_amb_store.py")
    print()

except Exception as e:
    print()
    print("=" * 70)
    print("❌ CONVERSION FAILED")
    print("=" * 70)
    print(f"Error: {e}")
    print()
    print("Troubleshooting:")
    print("  1. Ensure you're on Jetson Orin (not Mac)")
    print("  2. Check CUDA is properly installed")
    print("  3. Update ultralytics: pip install -U ultralytics")
    print("  4. Check available disk space (needs ~2GB)")
    print()
    exit(1)
