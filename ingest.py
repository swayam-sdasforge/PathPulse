import os
import random
from pathlib import Path
from datetime import datetime
import db

def parse_yaml(yaml_path):
    """Parses data.yaml to extract YOLO class names mapping."""
    import ast
    with open(yaml_path, 'r') as f:
        for line in f:
            if line.startswith("names:"):
                names_str = line.split("names:")[1].strip()
                return ast.literal_eval(names_str)
    return []

def main():
    base_dir = Path(r"P:\archive")
    yaml_path = base_dir / "images" / "data.yaml"
    
    if not yaml_path.exists():
        # Fallback to base_dir
        yaml_path = base_dir / "data.yaml"
        if not yaml_path.exists():
            print(f"Error: data.yaml not found in {base_dir}")
            return

    try:
        class_names = parse_yaml(yaml_path)
    except Exception as e:
        print(f"Error parsing YAML: {e}")
        return

    print(f"Loaded {len(class_names)} classes: {class_names}")

    # The labels are typically stored inside train/labels and val/labels
    # Wait, the structure we saw was train/labels, valid/labels, test/labels
    label_dirs = [
        base_dir / "images" / "train" / "labels",
        base_dir / "images" / "valid" / "labels",
        base_dir / "images" / "test" / "labels",
    ]

    total_inserted = 0
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    batch = []
    BATCH_SIZE = 500  # Optimize DB insertion without exceeding SQL limits

    for ldir in label_dirs:
        if not ldir.exists():
            continue
            
        txt_files = list(ldir.glob("*.txt"))
        print(f"\nProcessing {len(txt_files)} label files in {ldir.name}...")
        
        for i, txt_file in enumerate(txt_files):
            with open(txt_file, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                parts = line.strip().split()
                if not parts:
                    continue
                
                try:
                    class_id = int(parts[0])
                except ValueError:
                    continue
                    
                if class_id < len(class_names):
                    damage_type = class_names[class_id]
                else:
                    damage_type = f"Unknown_{class_id}"
                    
                # Generate random priority score
                priority_score = random.randint(1, 5)
                
                description = f"Mock data extracted from dataset image: {txt_file.stem}"
                location = "Mock Dataset Location"
                
                # We add to batch for bulk insertion
                batch.append((today_str, description, location, damage_type, priority_score))
                
                if len(batch) >= BATCH_SIZE:
                    db.insert_incidents_batch(batch)
                    total_inserted += len(batch)
                    batch.clear()
                    print(f"  -> Inserted {total_inserted} records so far...")
                    
    # Insert any remaining records
    if batch:
        db.insert_incidents_batch(batch)
        total_inserted += len(batch)
        batch.clear()

    print(f"\nDone! Successfully ingested {total_inserted} anomalies into Exasol.")

if __name__ == "__main__":
    main()
