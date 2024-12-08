import os
import json

# Define the directories for kittens, males, and females
base_dirs = {
    "kittens": "public/cats/kittens",
    "males": "public/cats/males",
    "females": "public/cats/females",
}

# Function to create JSON data for each category
def create_json_data(base_path):
    data = []
    for cat_name in os.listdir(base_path):
        cat_folder = os.path.join(base_path, cat_name)
        
        if os.path.isdir(cat_folder):
            # Read "desc.txt" and "txt.txt"
            desc_file = os.path.join(cat_folder, "desc.txt")
            txt_file = os.path.join(cat_folder, "txt.txt")
            
            desc = open(desc_file, 'r').read() if os.path.exists(desc_file) else ""
            txt = open(txt_file, 'r').read() if os.path.exists(txt_file) else ""
            
            # Get image paths
            image_files = [
                os.path.join(cat_folder, f) 
                for f in os.listdir(cat_folder) 
                if f.endswith(('.jpg', '.jpeg', '.png'))
            ]
            
            if not image_files:
                continue  # Skip if no images
            
            # First image as "image", all as "images"
            image = image_files[0]
            images = image_files
            
            # Append the cat's data
            data.append({
                "name": cat_name,
                "desc": desc,
                "txt": txt,
                "image": image,
                "images": images,
            })
    return data

# Process each category and save JSON files
for category, path in base_dirs.items():
    json_data = create_json_data(path)
    
    # Save the JSON data to a file
    output_file = f"{category}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

print("JSON files have been created.")
