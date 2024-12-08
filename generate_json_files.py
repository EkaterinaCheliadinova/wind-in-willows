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



{"@context":"https:\/\/schema.org","@graph":
 [{"@type":"BreadcrumbList","@id":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/#breadcrumblist",
   "itemListElement":[{"@type":"ListItem","@id":"https:\/\/sassykoonz.com\/#listItem",
                       "position":1,"name":"Home","item":"https:\/\/sassykoonz.com\/",
                       "nextItem":{"@type":"ListItem",
                                   "@id":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/#listItem",
                                   "name":"Maine Coon Kittens | Maine Coon Kittens for Sale"}},
                                   {"@type":"ListItem",
                                    "@id":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/#listItem",
                                    "position":2,"name":"Maine Coon Kittens | Maine Coon Kittens for Sale",
                                    "previousItem":{
                                        "@type":"ListItem",
                                        "@id":"https:\/\/sassykoonz.com\/#listItem",
                                        "name":"Home"}}]},
    {"@type":"Organization",
     "@id":"https:\/\/sassykoonz.com\/#organization",
     "name":"Sassy Koonz Maine Coons",
     "description":"Maine Coon Cats and Kittens",
     "url":"https:\/\/sassykoonz.com\/",
     "telephone":"+19043358845",
     "logo":{"@type":
             "ImageObject",
             "url":"https:\/\/sassykoonz.com\/wp-content\/uploads\/2019\/08\/fullsizeoutput_2056.jpeg",
             "@id":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/#organizationLogo"},
             "image":{"@id":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/#organizationLogo"},
             "sameAs":["https:\/\/facebook.com\/sassykoonz","https:\/\/instagram.com\/sassykoonz",
                       "https:\/\/tiktok.com\/@sassykoonz","https:\/\/pinterest.com\/sassykoonz",
                       "https:\/\/www.youtube.com\/channel\/UCeSjppoJ0-NWYMY9dnz9LTQ"]},
                       {"@type":"WebPage","@id":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/#webpage",
                        "url":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/",
                        "name":"Maine Coon Kittens For Sale: Meet Your New Family Member",
                        "description":"Maine Coon Kittens For Sale. Raised in a home environment. Kittens are socialized, friendly and healthy. Stellar Health Guarantee",
                        "inLanguage":"en-US","isPartOf":{"@id":"https:\/\/sassykoonz.com\/#website"},
                        "breadcrumb":{"@id":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/#breadcrumblist"},
                        "image":{"@type":"ImageObject","url":"https:\/\/i0.wp.com\/sassykoonz.com\/wp-content\/uploads\/2024\/11\/Maine-Coon-Cattery-3.png?fit=2048%2C1152&ssl=1",
                                 "@id":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/#mainImage","width":2048,"height":1152,"caption":"maine coon cattery"},
                                 "primaryImageOfPage":{"@id":"https:\/\/sassykoonz.com\/maine-coon-kittens-for-sale\/#mainImage"},
                                 "datePublished":"2018-03-22T17:36:04-04:00","dateModified":"2024-11-25T14:29:28-05:00"},
                                 {"@type":"WebSite","@id":"https:\/\/sassykoonz.com\/#website","url":"https:\/\/sassykoonz.com\/",
                                  "name":"Sassy Koonz Maine Coon Cattery | Maine Coon Kittens",
                                  "description":"Maine Coon Cats and Kittens",
                                  "inLanguage":"en-US",
                                  "publisher":{"@id":"https:\/\/sassykoonz.com\/#organization"}}]}
		