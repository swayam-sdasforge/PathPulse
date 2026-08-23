import os
import shutil
import random
from pathlib import Path

def parse_yaml(yaml_path):
    import ast
    with open(yaml_path, 'r') as f:
        for line in f:
            if line.startswith("names:"):
                names_str = line.split("names:")[1].strip()
                return ast.literal_eval(names_str)
    return []

def write_yaml(yaml_path, class_names):
    yaml_content = f"""train: ../train/images
val: ../valid/images
test: ../test/images

nc: {len(class_names)}
names: {class_names}
"""
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

def get_classes_in_file(label_path):
    classes = set()
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                classes.add(int(parts[0]))
    return classes

def main():
    base_dir = Path(r"P:\archive")
    source_dir = base_dir / "images"
    target_dir = base_dir / "balanced_subset"
    
    yaml_path = source_dir / "data.yaml"
    class_names = parse_yaml(yaml_path)
    
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)
    
    write_yaml(target_dir / "data.yaml", class_names)
    
    # Target maximum bounding boxes/images per class
    # To keep the training extremely fast for the hackathon (minutes), 
    # we'll use a small limit (e.g. 100 images per class)
    TARGET_PER_CLASS = 100
    
    splits = ['train', 'valid', 'test']
    
    for split in splits:
        print(f"Balancing {split} split...")
        src_images_dir = source_dir / split / "images"
        src_labels_dir = source_dir / split / "labels"
        
        tgt_images_dir = target_dir / split / "images"
        tgt_labels_dir = target_dir / split / "labels"
        
        tgt_images_dir.mkdir(parents=True, exist_ok=True)
        tgt_labels_dir.mkdir(parents=True, exist_ok=True)
        
        if not src_labels_dir.exists():
            continue
            
        label_files = list(src_labels_dir.glob("*.txt"))
        random.shuffle(label_files) # Shuffle to get random samples
        
        class_counts = {i: 0 for i in range(len(class_names))}
        
        copied_count = 0
        for label_path in label_files:
            classes_in_img = get_classes_in_file(label_path)
            if not classes_in_img:
                continue
                
            # If all classes in this image have already reached the target count, skip it
            # Unless we are severely lacking in something (to optimize speed, we aggressively downsample)
            if all(class_counts.get(c, 0) >= TARGET_PER_CLASS for c in classes_in_img):
                continue
                
            # Accept this image
            for c in classes_in_img:
                if c in class_counts:
                    class_counts[c] += 1
                    
            # Copy label
            shutil.copy(label_path, tgt_labels_dir / label_path.name)
            
            # Copy corresponding image
            image_name_jpg = label_path.stem + ".jpg"
            image_name_png = label_path.stem + ".png"
            
            if (src_images_dir / image_name_jpg).exists():
                shutil.copy(src_images_dir / image_name_jpg, tgt_images_dir / image_name_jpg)
            elif (src_images_dir / image_name_png).exists():
                shutil.copy(src_images_dir / image_name_png, tgt_images_dir / image_name_png)
                
            copied_count += 1
            
        print(f"  -> Copied {copied_count} images for {split}.")
        print(f"  -> Class counts: {class_counts}")

    print(f"\nSubset creation complete! Saved to {target_dir}")

if __name__ == "__main__":
    main()
