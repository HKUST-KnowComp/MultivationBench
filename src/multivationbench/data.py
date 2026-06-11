import base64
from io import BytesIO
import json
import logging
import os
import random
# from dotenv import load_dotenv

from PIL import Image
from typing import Tuple, Dict, List
from Datasets.StoryReasoning.story_reasoning.datasets.story_reasoning import StoryReasoningDataset
# from story_reasoning.story_reasoning.datasets.story_reasoning import StoryReasoningDataset
# from StoryReasoning.story_reasoning.datasets.story_reasoning import StoryReasoningDataset
from story_reasoning.models.story_reasoning.story_reasoning_util import StoryReasoningUtil



def load_ssid_data(sample_size):
    """
    Loads stories from SSID dataset from all splits (Train, Test, Valid).
    Each story contains multiple images with annotations.
    Constructs annotations with 'story_id', 'image_order', 'image_path' (placeholder), and 'text'.
    """
    stories = {}
    
    # Define the three splits to load
    splits = ['Test', 'Validation']
    
    for split in splits:
        json_file = f'Datasets/SSID/SSID_{split}.json'
        
        # Check if file exists before trying to load
        if not os.path.exists(json_file):
            logging.warning(f"SSID {split} file not found: {json_file}")
            continue
            
        # Load data
        try:
            with open(json_file, 'r') as f:
                data_json = f.read()
            logging.info(f"Read SSID {split} JSON file")
        except FileNotFoundError:
            logging.error(f"SSID_{split}.json not found")
            continue
        except Exception as e:
            logging.error(f"Error reading SSID_{split}.json: {str(e)}")
            continue

        # Parse JSON
        try:
            parsed_data = json.loads(data_json)
            if 'annotations' not in parsed_data:
                logging.error(f"JSON for {split} does not contain 'annotations' key")
                continue
            
            # Flatten annotations
            annotations = [item for sublist in parsed_data['annotations'] for item in sublist]
            logging.info(f"Parsed {len(annotations)} annotations from {split} split")
            
            # Group by story_id and create consistent annotation format
            split_story_count = 0
            for ann in annotations:
                try:
                    sid = ann['story_id']
                    
                    # Create story if it doesn't exist
                    if sid not in stories:
                        stories[sid] = []
                        split_story_count += 1
                    
                    # Create annotation dict following the same pattern as other datasets
                    formatted_ann = {
                        'story_id': sid,
                        'image_order': ann.get('image_order', 0),
                        'image_path': os.path.join("SSID", "SSID_Images", f"{ann.get('youtube_image_id', '')}.jpg"),
                        'text': ann.get('storytext', '').strip()
                    }
                    stories[sid].append(formatted_ann)
                    
                except KeyError as e:
                    logging.error(f"Missing key in annotation from {split}: {str(e)}")
                    continue
                except Exception as e:
                    logging.error(f"Error processing annotation from {split}: {str(e)}")
                    continue
            
            logging.info(f"Added {split_story_count} stories from {split} split")
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error for {split}: {str(e)}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error during parsing {split}: {str(e)}")
            continue
    
    # Sort each story by image_order
    for sid in stories:
        stories[sid].sort(key=lambda x: x['image_order'])
        logging.debug(f"Loaded {len(stories[sid])} annotations for story {sid}")
    
    logging.info(f"Total: Grouped into {len(stories)} stories from all splits")
    
    # Sample stories if requested
    if sample_size > 0:
        story_ids = sorted(stories.keys())
        sample_size = min(sample_size, len(story_ids))
        sampled_ids = random.sample(story_ids, sample_size) if story_ids else []
        logging.info(f"Sampled {len(sampled_ids)} story IDs from {len(story_ids)} total stories")
        
        # Return only sampled stories
        sampled_stories = {sid: stories[sid] for sid in sampled_ids}
        return sampled_stories, sampled_ids, sampled_ids
    else:
        # Return all stories
        story_ids = sorted(stories.keys())
        logging.info(f"Returning all {len(story_ids)} stories (no sampling)")
        return stories, story_ids, story_ids

# def load_ssid_data(sample_size=100):
#     """
#     Loads stories from SSID dataset from JSON file.
#     Each story contains multiple images with annotations.
#     Constructs annotations with 'story_id', 'image_order', 'image_path' (placeholder), and 'text'.
#     """
#     stories = {}

#     # Load data
#     try:
#         with open('SSID/SSID_Train.json', 'r') as f:
#             data_json = f.read()
#         logging.info(f"Read SSID JSON file")
#     except FileNotFoundError:
#         logging.error("SSID_Test.json not found")
#         raise
#     except Exception as e:
#         logging.error(f"Error reading SSID_Test.json: {str(e)}")
#         raise

#     # Parse JSON
#     try:
#         parsed_data = json.loads(data_json)
#         if 'annotations' not in parsed_data:
#             logging.error("JSON does not contain 'annotations' key")
#             raise KeyError("Expected 'annotations' key in JSON")
        
#         # Flatten annotations
#         annotations = [item for sublist in parsed_data['annotations'] for item in sublist]
#         logging.info(f"Parsed {len(annotations)} total annotations")
        
#         # Group by story_id and create consistent annotation format
#         for ann in annotations:
#             try:
#                 sid = ann['story_id']
                
#                 # Create story if it doesn't exist
#                 if sid not in stories:
#                     stories[sid] = []
                
#                 # Create annotation dict following the same pattern as other datasets
#                 formatted_ann = {
#                     'story_id': sid,
#                     'image_order': ann.get('image_order', 0),
                    
#                     'image_path': os.path.join("SSID", "SSID_Images", f"{ann.get('youtube_image_id', '')}.jpg"),  # Using youtube_image_id as image_path placeholder
#                     'text': ann.get('storytext', '').strip()
#                 }
#                 stories[sid].append(formatted_ann)
                
#             except KeyError as e:
#                 logging.error(f"Missing key in annotation: {str(e)}")
#                 continue
#             except Exception as e:
#                 logging.error(f"Error processing annotation: {str(e)}")
#                 continue
        
#         # Sort each story by image_order
#         for sid in stories:
#             stories[sid].sort(key=lambda x: x['image_order'])
#             logging.info(f"Loaded {len(stories[sid])} annotations for story {sid}")
                
#         logging.info(f"Grouped into {len(stories)} stories from {len(annotations)} annotations")
        
#     except json.JSONDecodeError as e:
#         logging.error(f"JSON parsing error: {str(e)}")
#         raise
#     except Exception as e:
#         logging.error(f"Unexpected error during parsing: {str(e)}")
#         raise

#     # Sample stories
#     story_ids = sorted(stories.keys())
#     sample_size = min(sample_size, len(story_ids))
#     sampled_ids = random.sample(story_ids, sample_size) if story_ids else []
#     logging.info(f"Sampled {len(sampled_ids)} story IDs")

#     return stories, story_ids, sampled_ids


# def load_storystream_data(sample_size=5):
#     # Load .env file (retained for compatibility with downstream tasks)
    

#     # Load data
#     try:
#         with open('the_land_story/val.jsonl', 'r') as f:
#             lines = f.readlines()
#         logging.info(f"Read {len(lines)} lines from the_land_story/val.jsonl")
#     except FileNotFoundError:
#         logging.error("the_land_story/val.jsonl not found")
#         raise
#     except Exception as e:
#         logging.error(f"Error reading the_land_story/val.jsonl: {str(e)}")
#         raise

#     # Parse JSONL
#     stories = {}
#     story_ids = []
#     try:
#         for line in lines:
#             try:
#                 data = json.loads(line.strip())
#                 if not all(k in data for k in ['id', 'images', 'captions', 'orders']):
#                     logging.error(f"Invalid JSON line format: missing required keys in {line[:100]}...")
#                     continue
#                 sid = data['id']
#                 images = data['images']
#                 captions = data['captions']
#                 orders = data['orders']

#                 # Validate lengths
#                 if not (len(images) == len(captions) == len(orders)):
#                     logging.warning(f"Inconsistent lengths in story {sid}: images={len(images)}, captions={len(captions)}, orders={len(orders)}")
#                     continue

#                 # # Create short stories from pairs of consecutive images
#                 # for i in range(len(images) - 1):  # n-1 short stories for n images
#                 #     sub_sid = f"{sid}_{i}"  # Unique ID for each short story (e.g., 531_0, 531_1)
#                 #     stories[sub_sid] = [
#                 #         {
#                 #             'youtube_image_id': images[i],
#                 #             'image_order': 0,
#                 #             'storytext': captions[i]
#                 #         },
#                 #         {
#                 #             'youtube_image_id': images[i+1],
#                 #             'image_order': 1,
#                 #             'storytext': captions[i+1]
#                 #         }
#                 #     ]
#                 #     story_ids.append(sub_sid)
#                 logging.info(f"Created {len(images)-1} short stories for story ID {sid}")
#             except json.JSONDecodeError as e:
#                 logging.error(f"JSON parsing error in line: {line[:100]}... - {str(e)}")
#                 continue
#             except Exception as e:
#                 logging.error(f"Error processing line: {line[:100]}... - {str(e)}")
#                 continue
#         logging.info(f"Grouped into {len(stories)} short stories from {len(lines)} full stories")
#     except Exception as e:
#         logging.error(f"Unexpected error during parsing: {str(e)}")
#         raise

#     # Sample up to sample_size full stories' worth of short stories
#     full_story_ids = sorted(set(sid.split('_')[0] for sid in story_ids))  # Extract original IDs (e.g., 531)
#     sample_size = min(sample_size, len(full_story_ids))
#     sampled_full_ids = random.sample(full_story_ids, sample_size) if full_story_ids else []
#     sampled_ids = [sid for sid in story_ids if sid.split('_')[0] in sampled_full_ids]
#     sampled_ids = sorted(sampled_ids)[:sample_size * 30]  # Rough cap assuming max 30 short stories per full story
#     logging.info(f"Sampled {len(sampled_ids)} short story IDs from {len(sampled_full_ids)} full stories")

#     return stories, story_ids, sampled_ids

def load_storystream_data(sample_size=5):
    """
    Loads stories from StoryStream dataset from JSONL file.
    Each line represents a full story with images, captions, and orders.
    Constructs annotations with 'story_id', 'image_order', 'image_path' (placeholder), and 'text'.
    """
    stories = {}

    # Load data
    try:
        with open('the_land_story/val.jsonl', 'r') as f:
            lines = f.readlines()
        logging.info(f"Read {len(lines)} lines from the_land_story/val.jsonl")
    except FileNotFoundError:
        logging.error("the_land_story/val.jsonl not found")
        raise
    except Exception as e:
        logging.error(f"Error reading the_land_story/val.jsonl: {str(e)}")
        raise

    # Parse JSONL
    try:
        for line in lines:
            try:
                data = json.loads(line.strip())
                if not all(k in data for k in ['id', 'images', 'captions', 'orders']):
                    logging.error(f"Invalid JSON line format: missing required keys in {line[:100]}...")
                    continue
                
                sid = data['id']
                images = data['images']
                captions = data['captions']
                orders = data['orders']

                # Validate lengths
                if not (len(images) == len(captions) == len(orders)):
                    logging.warning(f"Inconsistent lengths in story {sid}: images={len(images)}, captions={len(captions)}, orders={len(orders)}")
                    continue

                # Create story with all images
                stories[sid] = []
                for i in range(len(images)):
                    # Create annotation dict following the same pattern as other datasets
                    ann = {
                        'story_id': sid,
                        'image_order': orders[i] if i < len(orders) else i + 1,
                        'image_path': images[i],  # Using youtube_image_id as image_path placeholder
                        'text': captions[i].strip()
                    }
                    stories[sid].append(ann)

                logging.info(f"Loaded {len(stories[sid])} annotations for story {sid}")
                
            except json.JSONDecodeError as e:
                logging.error(f"JSON parsing error in line: {line[:100]}... - {str(e)}")
                continue
            except Exception as e:
                logging.error(f"Error processing line: {line[:100]}... - {str(e)}")
                continue
                
        logging.info(f"Grouped into {len(stories)} stories from {len(lines)} lines")
    except Exception as e:
        logging.error(f"Unexpected error during parsing: {str(e)}")
        raise

    # Sample stories
    story_ids = sorted(stories.keys())
    sample_size = min(sample_size, len(story_ids))
    sampled_ids = random.sample(story_ids, sample_size) if story_ids else []
    logging.info(f"Sampled {len(sampled_ids)} story IDs")

    return stories, story_ids, sampled_ids



def load_storysalon_data(photo_folder, text_folder, sample_size=100):
    """
    Loads stories from two main folders: 'photo' and 'text', each containing subfolders with the same IDs as names.
    Each subfolder represents a story. The 'photo' subfolder contains series of .jpg files, and the 'text' subfolder
    contains series of text files (assuming .txt extension). Files are paired and sorted by numeric prefix in filenames.
    Constructs annotations with 'story_id', 'image_order', 'image_path', and 'text'.
    """
    stories = {}

    # Get subfolders from photo_folder (assume same in text_folder)
    try:
        subfolders = [d for d in os.listdir(photo_folder) if os.path.isdir(os.path.join(photo_folder, d))]
        if len(subfolders) <= 100:
            logging.warning(f"Expected 100 subfolders in {photo_folder}, found {len(subfolders)}")
        else:
            logging.info(f"Found {len(subfolders)} subfolders in {photo_folder}")
    except FileNotFoundError:
        logging.error(f"Folder not found: {photo_folder}")
        raise
    except Exception as e:
        logging.error(f"Error reading folder {photo_folder}: {str(e)}")
        raise

    for sid in subfolders:
        stories[sid] = []
        photo_path = os.path.join(photo_folder, sid)
        text_path = os.path.join(text_folder, sid)

        # Check if corresponding text subfolder exists
        if not os.path.isdir(text_path):
            logging.warning(f"Missing text subfolder for story {sid}")
            continue

        try:
            # Get and sort .jpg files in photo
            jpg_files = [f for f in os.listdir(photo_path) if f.lower().endswith('.jpg')]
            jpg_files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else float('inf'))

            # Get and sort .txt files in text (assuming .txt; adjust if different)
            txt_files = [f for f in os.listdir(text_path) if f.lower().endswith('.txt')]
            txt_files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else float('inf'))

            # Ensure matching number of files
            if len(jpg_files) != len(txt_files):
                logging.warning(f"Mismatch in file counts for story {sid}: {len(jpg_files)} jpgs vs {len(txt_files)} txts")
                continue

            for idx, (jpg, txt) in enumerate(zip(jpg_files, txt_files), start=1):
                jpg_full_path = os.path.join(photo_path, jpg)
                txt_full_path = os.path.join(text_path, txt)

                # Read text content
                with open(txt_full_path, 'r', encoding='utf-8') as f:
                    text_content = f.read().strip()

                # Create annotation dict
                ann = {
                    'story_id': sid,
                    'image_order': idx,
                    'image_path': jpg_full_path,
                    'text': text_content
                }
                stories[sid].append(ann)

            logging.info(f"Loaded {len(stories[sid])} annotations for story {sid}")
        except Exception as e:
            logging.error(f"Error loading story {sid}: {str(e)}")
            continue

    logging.info(f"Grouped into {len(stories)} stories")

    story_ids = sorted(stories.keys())
    sample_size = min(sample_size, len(story_ids))
    sampled_ids = random.sample(story_ids, sample_size) if story_ids else []
    logging.info(f"Sampled {len(sampled_ids)} story IDs")

    return stories, story_ids, sampled_ids

import os
import json
import logging
from typing import Tuple, Dict, List

def load_moviebench_data(image_folder: str, annotation_folder: str, movie_scene_file: str, sample_size: int = 100) -> Tuple[Dict[str, List[Dict]], List[str], List[str]]:
    """
    Loads MovieBench data from image and annotation folders, and a movie_scene.json file.
    Images are stored in image_folder with names like '1004_Juno_00.00.32.849-00.00.35.458.jpg'.
    Annotations are JSON files in annotation_folder/MovieID with matching names.
    movie_scene.json defines scenes (treated as stories) with movie IDs and image lists.
    Constructs annotations with 'story_id', 'image_order', 'image_path', and 'text' (from 'Plot' in JSON).
    
    Args:
        image_folder (str): Path to folder containing .jpg files.
        annotation_folder (str): Path to folder containing annotation JSON files in subfolders.
        movie_scene_file (str): Path to movie_scene.json file.
        sample_size (int): Number of stories (scenes) to sample.
    
    Returns:
        Tuple containing:
        - stories: Dict mapping story_id to list of annotation dicts.
        - story_ids: List of all story IDs.
        - sampled_ids: List of sampled story IDs.
    """
    stories = {}

    # Load movie_scene.json
    try:
        with open(movie_scene_file, 'r', encoding='utf-8') as f:
            movie_scenes = json.load(f)
        logging.info(f"Loaded movie_scene.json with {len(movie_scenes)} movies")
    except FileNotFoundError:
        logging.error(f"Movie scene file not found: {movie_scene_file}")
        raise
    except Exception as e:
        logging.error(f"Error reading movie_scene file {movie_scene_file}: {str(e)}")
        raise

    # Process each movie and its scenes
    for movie_id_name, scenes in movie_scenes.items():
        # Extract movie ID and name (e.g., '1037_The_Curious_Case_Of_Benjamin_Button' -> '1037', 'The_Curious_Case_Of_Benjamin_Button')
        try:
            movie_id = movie_id_name.split('_', 1)[0]
            movie_name = movie_id_name[len(movie_id) + 1:]
        except IndexError:
            logging.warning(f"Invalid movie ID format: {movie_id_name}")
            continue

        annotation_subfolder = os.path.join(annotation_folder, movie_id_name)
        if not os.path.isdir(annotation_subfolder):
            logging.warning(f"Missing annotation subfolder for movie {movie_id_name}")
            continue

        for scene_name, image_list in scenes.items():
            # Use movie_id_name and scene_name as story_id (e.g., '1037_The_Curious_Case_Of_Benjamin_Button_Sence_1')
            story_id = f"{movie_id_name}_{scene_name.replace(' ', '_')}"
            stories[story_id] = []

            try:
                for idx, image_name in enumerate(image_list, start=1):
                    # Construct image and annotation paths
                    image_path = os.path.join(image_folder, f"{image_name}.jpg")
                    annotation_path = os.path.join(annotation_subfolder, f"{image_name}.json")

                    # Verify image exists
                    if not os.path.isfile(image_path):
                        logging.warning(f"Image not found for {image_name} in story {story_id}")
                        continue

                    # Load annotation JSON
                    try:
                        with open(annotation_path, 'r', encoding='utf-8') as f:
                            annotation = json.load(f)
                        plot_text = annotation.get('Plot', '')
                        if not plot_text:
                            logging.warning(f"No 'Plot' field in annotation for {image_name}")
                            plot_text = ''
                    except FileNotFoundError:
                        logging.warning(f"Annotation JSON not found for {image_name}")
                        continue
                    except Exception as e:
                        logging.error(f"Error reading annotation {annotation_path}: {str(e)}")
                        continue

                    # Create annotation dict
                    ann = {
                        'story_id': story_id,
                        'image_order': idx,
                        'image_path': image_path,
                        'text': plot_text.strip()
                    }
                    stories[story_id].append(ann)

                if stories[story_id]:
                    logging.info(f"Loaded {len(stories[story_id])} annotations for story {story_id}")
                else:
                    del stories[story_id]  # Remove empty story
                    logging.warning(f"No valid annotations loaded for story {story_id}")
            except Exception as e:
                logging.error(f"Error processing story {story_id}: {str(e)}")
                continue

    logging.info(f"Grouped into {len(stories)} stories")

    # Sample stories
    story_ids = sorted(stories.keys())
    sample_size = min(sample_size, len(story_ids))
    sampled_ids = random.sample(story_ids, sample_size) if story_ids else []
    logging.info(f"Sampled {len(sampled_ids)} story IDs")

    return stories, story_ids, sampled_ids




# def load_storyreasoning_data(hf_repo: str = "daniel3303/StoryReasoning", split: str = "train", sample_size: int = 100) -> Tuple[Dict[str, List[Dict]], List[str], List[str]]:
#     """
#     Loads StoryReasoning dataset from a Hugging Face repository.
#     Each story contains story_id, frame_count, story (text with tags), images, and chain_of_thought.
#     Constructs annotations with 'story_id', 'image_order', 'image_path' (or image data), and 'text' (stripped story text).
#     Randomly samples a specified number of stories.

#     Args:
#         hf_repo (str): Hugging Face repository name (default: "daniel3303/StoryReasoning").
#         split (str): Dataset split to load (default: "train").
#         sample_size (int): Number of stories to randomly sample (default: 100).

#     Returns:
#         Tuple containing:
#         - stories: Dict mapping story_id to list of annotation dicts.
#         - story_ids: List of all story IDs.
#         - sampled_ids: List of randomly sampled story IDs.
#     """
#     stories = {}
#     print("hi")

#     # Load the dataset
#     try:
#         dataset = StoryReasoningDataset(hf_repo=hf_repo, split=split)
#         logging.info(f"Loaded {split} split of StoryReasoning dataset with {len(dataset)} samples")
#     except Exception as e:
#         logging.error(f"Error loading dataset from {hf_repo} (split: {split}): {str(e)}")
#         raise

#     # Process each sample in the dataset
#     for sample in dataset:
#         try:
#             story_id = sample.get('story_id')
#             if not story_id:
#                 logging.warning(f"Sample missing story_id: {sample}")
#                 continue

#             stories[story_id] = []
#             images = sample.get('images', [])
#             frame_count = sample.get('frame_count', len(images))
#             story_text = sample.get('story', '')

#             # Ensure images and frame_count are consistent
#             if len(images) != frame_count:
#                 logging.warning(f"Mismatch in frame_count ({frame_count}) and images ({len(images)}) for story {story_id}")
#                 continue

#             # Create annotations for each image
#             for idx, image in enumerate(images, start=1):
#                 # Convert PIL Image to Base64 string
#                 try:
#                     buffered = BytesIO()
#                     image.save(buffered, format="JPEG")
#                     image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
#                 except Exception as e:
#                     logging.warning(f"Failed to encode image {idx} for story {story_id}: {str(e)}")
#                     continue


#                 story = StoryReasoningUtil.parse_story(story_text)

#                 # Find the StoryImage corresponding to the current idx (image_order)
#                 image_text = ""
#                 for image in story.images:
#                     if image.image_number == idx:
#                         # Extract the plain text for this specific image, stripping tags
#                         image_text = StoryReasoningUtil.strip_story_tags(image.text)
#                         break
#                 ann = {
#                     'story_id': story_id,
#                     'image_order': idx,
#                     'image_path': image_data,  # Placeholder since images are loaded directly
#                     'text': image_text  # Strip tags,
#                 }
#                 stories[story_id].append(ann)

#             if stories[story_id]:
#                 logging.info(f"Loaded {len(stories[story_id])} annotations for story {story_id}")
#             else:
#                 del stories[story_id]
#                 logging.warning(f"No valid annotations loaded for story {story_id}")
#         except Exception as e:
#             logging.error(f"Error processing story {story_id}: {str(e)}")
#             continue

#     logging.info(f"Grouped into {len(stories)} stories")

#     # Randomly sample stories
#     story_ids = sorted(stories.keys())
#     sample_size = min(sample_size, len(story_ids))
#     sampled_ids = random.sample(story_ids, sample_size) if story_ids else []
#     logging.info(f"Randomly sampled {len(sampled_ids)} story IDs")

#     # # Export all stories as JSON
#     # with open("all_storyreasoning_stories.json", "w", encoding="utf-8") as f:
#     #     json.dump(stories, f, ensure_ascii=False, indent=2)
#     # logging.info(f"Exported {len(stories)} stories to all_storyreasoning_stories.json")

#     return stories, story_ids, sampled_ids





def load_storyreasoning_data(hf_repo: str = "daniel3303/StoryReasoning", split: str = "train", download_dir: str = "./Datasets/storyreasoning_images", sample_size: int = 100, range: Tuple[int, int] = (1, 5)) -> Tuple[Dict[str, List[Dict]], List[str], List[str]]:
    """
    Loads StoryReasoning dataset from a Hugging Face repository.
    Each story contains story_id, frame_count, story (text with tags), images, and chain_of_thought.
    Downloads images to a local folder and stores their file paths.
    Limits images to those with image_order in the specified range (inclusive).
    Constructs annotations with 'story_id', 'image_order', 'image_path' (local file path), and 'text' (per-image stripped text).
    Randomly samples a specified number of stories.

    Args:
        hf_repo (str): Hugging Face repository name (default: "daniel3303/StoryReasoning").
        split (str): Dataset split to load (default: "train").
        download_dir (str): Directory to save downloaded images (default: "./storyreasoning_images").
        sample_size (int): Number of stories to randomly sample (default: 100).
        range (Tuple[int, int]): Tuple of (min, max) image_order to include (default: (1, 5)).

    Returns:
        Tuple containing:
        - stories: Dict mapping story_id to list of annotation dicts.
        - story_ids: List of all story IDs.
        - sampled_ids: List of randomly sampled story IDs.
    """
    stories = {}

    # Validate range parameter
    if not (isinstance(range, tuple) and len(range) == 2 and range[0] <= range[1]):
        logging.error(f"Invalid range parameter: {range}. Must be a tuple of (min, max) with min <= max.")
        raise ValueError("Invalid range parameter")

    min_idx, max_idx = range
    logging.info(f"Limiting images to image_order range: {min_idx} to {max_idx}")

    # Create download directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)
    logging.info(f"Using download directory: {download_dir}")

    # Load the dataset
    try:
        # Load both train and test splits and merge
        train_dataset = StoryReasoningDataset(hf_repo=hf_repo, split="train")
        test_dataset = StoryReasoningDataset(hf_repo=hf_repo, split="test")
        dataset = list(train_dataset) + list(test_dataset)
        logging.info(f"Loaded {split} split of StoryReasoning dataset with {len(dataset)} samples")
    except Exception as e:
        logging.error(f"Error loading dataset from {hf_repo} (split: {split}): {str(e)}")
        raise

    # Process each sample in the dataset
    for sample in dataset:
        try:
            story_id = sample.get('story_id')
            if not story_id:
                logging.warning(f"Sample missing story_id: {sample}")
                continue

            stories[story_id] = []
            images = sample.get('images', [])
            frame_count = sample.get('frame_count', len(images))
            story_text = sample.get('story', '')

            # Ensure images and frame_count are consistent
            if len(images) != frame_count:
                logging.warning(f"Mismatch in frame_count ({frame_count}) and images ({len(images)}) for story {story_id}")
                continue

            # Parse story text to extract per-image text
            try:
                parsed_story = StoryReasoningUtil.parse_story(story_text)
            except Exception as e:
                if "Can't find model 'en_core_web_sm'" in str(e):
                    logging.error(f"SpaCy model 'en_core_web_sm' not found. Please install it using: python -m spacy download en_core_web_sm")
                    raise
                logging.warning(f"Failed to parse story text for story {story_id}: {str(e)}")
                continue

            # Create annotations for each image within the specified range
            for idx, image in enumerate(images, start=1):
                if idx < min_idx or idx > max_idx:
                    continue  # Skip images outside the specified range

                # Save image to local folder
                image_filename = f"{story_id}_image_{idx}.jpg"
                image_path = os.path.join(download_dir, image_filename)
                try:
                    if isinstance(image, Image.Image):
                        image.save(image_path, format="JPEG")
                    else:
                        logging.warning(f"Image {idx} in story {story_id} is not a PIL Image, skipping")
                        continue
                except Exception as e:
                    logging.warning(f"Failed to save image {idx} for story {story_id} to {image_path}: {str(e)}")
                    continue

                # Find the StoryImage corresponding to the current idx (image_order)
                image_text = ""
                for story_image in parsed_story.images:
                    if story_image.image_number == idx:
                        image_text = StoryReasoningUtil.strip_story_tags(story_image.text).strip()
                        break

                ann = {
                    'story_id': story_id,
                    'image_order': idx,
                    'image_path': image_path,
                    'text': image_text
                }
                stories[story_id].append(ann)

            if stories[story_id]:
                logging.info(f"Loaded {len(stories[story_id])} annotations for story {story_id}")
            else:
                del stories[story_id]
                logging.warning(f"No valid annotations loaded for story {story_id}")
        except Exception as e:
            logging.error(f"Error processing story {story_id}: {str(e)}")
            continue

    logging.info(f"Grouped into {len(stories)} stories")

    # Randomly sample stories
    story_ids = sorted(stories.keys())
    sample_size = min(sample_size, len(story_ids))
    sampled_ids = random.sample(story_ids, sample_size) if story_ids else []
    logging.info(f"Randomly sampled {len(sampled_ids)} story IDs")

    # # Export all stories as JSON
    # try:
    #     with open("all_storyreasoning_stories.json", "w", encoding="utf-8") as f:
    #         json.dump(stories, f, ensure_ascii=False, indent=2)
    #     logging.info(f"Exported {len(stories)} stories to all_storyreasoning_stories.json")
    # except Exception as e:
    #     logging.error(f"Error exporting stories to JSON: {str(e)}")

    return stories, story_ids, sampled_ids

# if __name__ == "__main__":
#     stories, story_ids, sampled_ids = load_storyreasoning_data(sample_size=10, range=(1, 7))
#     print(f"Total stories loaded: {len(stories)}")
#     if sampled_ids:
#         print(stories[sampled_ids[0]])

def main():
    """Data analysis function to print dataset statistics"""
    
    print("=" * 60)
    print("DATASET ANALYSIS REPORT")
    print("=" * 60)
    # photo_folder = 'movie/images'
    # text_folder = 'Moviebench'
    # annotation = 'movie/movies_scenes.json'
    # stories, story_ids, sampled_ids = load_moviebench_data(photo_folder, text_folder,annotation, max_tests)
    
    # Analyze each dataset
    datasets = [
        ("SSID", lambda: load_ssid_data(sample_size=100)),
        ("StoryStream", lambda: load_storystream_data(sample_size=5)),
        ("StorySalon", lambda: load_storysalon_data(
            photo_folder='StorySalon/Image_inpainted/Bloom', 
            text_folder='StorySalon/text/Caption/Bloom', 
            sample_size=100
        )),
        ("MovieBench", 
         lambda: load_moviebench_data(
            image_folder='movie/images',
            annotation_folder='Moviebench', 
            movie_scene_file='movie/movies_scenes.json',
            sample_size=100
        )),
        ("StoryReasoning", lambda: load_storyreasoning_data(sample_size=100, range=(1, 50)))
    ]
    
    for dataset_name, loader_func in datasets:
        print(f"\n{dataset_name.upper()} DATASET")
        print("-" * 40)
        
        try:
            stories, story_ids, sampled_ids = loader_func()
            
            # Calculate statistics
            total_stories = len(stories)
            total_images = sum(len(annotations) for annotations in stories.values())
            avg_images_per_story = total_images / total_stories if total_stories > 0 else 0
            
            # Image count distribution
            image_counts = [len(annotations) for annotations in stories.values()]
            min_images = min(image_counts) if image_counts else 0
            max_images = max(image_counts) if image_counts else 0
            
            print(f"Total Stories: {total_stories}")
            print(f"Total Images: {total_images}")
            print(f"Average Images per Story: {avg_images_per_story:.2f}")
            print(f"Min Images per Story: {min_images}")
            print(f"Max Images per Story: {max_images}")
            print(f"Sampled Stories: {len(sampled_ids)}")
            print("-" * 40)
            print(f"Sample first story: {json.dumps(stories[sampled_ids[0]], indent=2)}")

            
            # # Print image count distribution
            # if image_counts:
            #     count_distribution = {}
            #     for count in image_counts:
            #         count_distribution[count] = count_distribution.get(count, 0) + 1
                
            #     print("Image Count Distribution:")
            #     for count in sorted(count_distribution.keys()):
            #         print(f"  {count} images: {count_distribution[count]} stories")
            
                    
        except Exception as e:
            print(f"ERROR loading {dataset_name}: {str(e)}")
            continue
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)


def quick_stats():
    """Quick statistics function for StoryReasoning dataset only"""
    print("QUICK STATS - StoryReasoning Dataset")
    print("-" * 40)
    
    try:
        stories, story_ids, sampled_ids = load_storyreasoning_data(sample_size=100, range=(1, 7))
        
        total_stories = len(stories)
        total_images = sum(len(annotations) for annotations in stories.values())
        avg_images_per_story = total_images / total_stories if total_stories > 0 else 0
        
        print(f"Total Stories: {total_stories}")
        print(f"Total Images: {total_images}")
        print(f"Average Images per Story: {avg_images_per_story:.2f}")
        
        # Show distribution
        image_counts = [len(annotations) for annotations in stories.values()]
        if image_counts:
            count_distribution = {}
            for count in image_counts:
                count_distribution[count] = count_distribution.get(count, 0) + 1
            
            print("\nImage Count Distribution:")
            for count in sorted(count_distribution.keys()):
                percentage = (count_distribution[count] / total_stories) * 100
                print(f"  {count} images: {count_distribution[count]} stories ({percentage:.1f}%)")
                
    except Exception as e:
        print(f"ERROR: {str(e)}")


if __name__ == "__main__":
    # Run the full analysis
    main()
    
    # Or run quick stats only
    # quick_stats()