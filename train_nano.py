from ultralytics import YOLO
from pathlib import Path

def main():
    yaml_path = Path(r"P:\archive\balanced_subset\data.yaml")
    
    if not yaml_path.exists():
        print(f"Error: Could not find {yaml_path}. Did you run balance_data.py first?")
        return

    print("Initializing YOLOv8 Nano model...")
    model = YOLO("yolov8n.pt")  # Load lightweight pre-trained model

    print(f"Starting micro-training for 15 epochs on {yaml_path}...")
    
    # Train the model
    # We use small epochs and default settings to ensure a fast run for the hackathon
    results = model.train(
        data=str(yaml_path),
        epochs=15,
        imgsz=640,
        batch=16,
        name="pathpulse_nano",
        exist_ok=True
    )

    print("\n✅ Training complete! Weights saved to runs/detect/pathpulse_nano/weights/best.pt")

if __name__ == "__main__":
    main()
