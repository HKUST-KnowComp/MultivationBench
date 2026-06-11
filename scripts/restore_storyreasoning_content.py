import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_DIR = REPO_ROOT / "data"
DEFAULT_INPUT_JSON = DATA_DIR / "multivationbench.json"
DEFAULT_MAPPING_JSON = DATA_DIR / "mappings" / "storyreasoning_mapping.json"
DEFAULT_OUTPUT_JSON = DATA_DIR / "multivationbench.storyreasoning_restored.json"
STORYREASONING_IMAGE_DIR = REPO_ROOT / "Datasets" / "storyreasoning_images"
LOCAL_FALLBACK_JSON = REPO_ROOT / "result" / "final_dataset" / "stories.json"


def parse_storyreasoning_path(image_path):
    name = Path(image_path).name
    story_id, image_number_part = name.split("_image_")
    image_number = int(Path(image_number_part).stem)
    return story_id, image_number


def load_storyreasoning_from_hf(needed_story_ids):
    repo = REPO_ROOT.resolve()
    sys.path.insert(0, str(repo))
    sys.path.insert(0, str(repo / "Datasets" / "StoryReasoning"))

    from Datasets.StoryReasoning.story_reasoning.datasets.story_reasoning import (
        StoryReasoningDataset,
    )
    from story_reasoning.models.story_reasoning.story_reasoning_util import (
        StoryReasoningUtil,
    )

    dataset = list(StoryReasoningDataset(hf_repo="daniel3303/StoryReasoning", split="train"))
    dataset += list(StoryReasoningDataset(hf_repo="daniel3303/StoryReasoning", split="test"))

    stories = {}
    STORYREASONING_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    for sample in dataset:
        story_id = str(sample.get("story_id"))
        if story_id not in needed_story_ids:
            continue

        parsed_story = StoryReasoningUtil.parse_story(sample.get("story", ""))
        text_by_number = {
            image.image_number: StoryReasoningUtil.strip_story_tags(image.text).strip()
            for image in parsed_story.images
        }

        frames = {}
        for image_number, image in enumerate(sample.get("images", []), start=1):
            image_path = STORYREASONING_IMAGE_DIR / f"{story_id}_image_{image_number}.jpg"
            if not image_path.exists():
                image.save(image_path, format="JPEG")
            frames[image_number] = {
                "image_path": Path("Datasets")
                / "storyreasoning_images"
                / f"{story_id}_image_{image_number}.jpg",
                "text": text_by_number.get(image_number, ""),
            }

        stories[story_id] = frames

    missing = needed_story_ids - set(stories)
    if missing:
        raise KeyError(f"Missing StoryReasoning story IDs from upstream dataset: {sorted(missing)}")

    return stories


def load_storyreasoning_from_local_fallback(needed_story_ids):
    if not LOCAL_FALLBACK_JSON.exists():
        raise FileNotFoundError(f"Local fallback not found: {LOCAL_FALLBACK_JSON}")

    with LOCAL_FALLBACK_JSON.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    stories = {}
    for bucket in data["storyreasoning"].values():
        for story_id, story in bucket.items():
            story_id = str(story_id)
            if story_id not in needed_story_ids:
                continue

            frames = {}
            for item in story.get("original_story", []):
                _, image_number = parse_storyreasoning_path(item["image_path"])
                local_image_path = REPO_ROOT / item["image_path"]
                if not local_image_path.exists():
                    raise FileNotFoundError(f"Missing StoryReasoning image: {local_image_path}")
                frames[image_number] = {
                    "image_path": Path(item["image_path"]),
                    "text": item["text"],
                }
            stories[story_id] = frames

    missing = needed_story_ids - set(stories)
    if missing:
        raise KeyError(f"Missing StoryReasoning story IDs from local fallback: {sorted(missing)}")

    return stories


def load_storyreasoning_source(needed_story_ids):
    try:
        return load_storyreasoning_from_hf(needed_story_ids), "huggingface"
    except Exception:
        return load_storyreasoning_from_local_fallback(needed_story_ids), "local_fallback"


def build_story_text(source_frames, source_image_numbers, benchmark_image_orders, text_overrides):
    story_text = []
    for image_order, source_image_number in zip(benchmark_image_orders, source_image_numbers):
        frame = source_frames[source_image_number]
        text = text_overrides.get(str(source_image_number), frame["text"])
        story_text.append(
            {
                "image_order": image_order,
                "text": text,
                "image_path": frame["image_path"].as_posix(),
            }
        )
    return story_text


def rebuild_story_context(benchmark_story_text, upstream_story_text, image_paths, context_format):
    benchmark_lookup = {item["image_path"]: item for item in benchmark_story_text}
    upstream_lookup = {item["image_path"]: item for item in upstream_story_text}
    ordered_paths = sorted(
        image_paths,
        key=lambda image_path: benchmark_lookup[image_path]["image_order"],
    )

    included_positions = context_format.get("included_positions", [])
    text_sources = context_format.get("text_sources", [])
    prefix = context_format.get("prefix", "")
    separators = context_format.get("separators", [])
    suffix = context_format.get("suffix", "")

    if not included_positions:
        return prefix + suffix

    selected_texts = []
    for pos, source_name in zip(included_positions, text_sources):
        image_path = ordered_paths[pos]
        lookup = benchmark_lookup if source_name == "benchmark" else upstream_lookup
        selected_texts.append(lookup[image_path]["text"])

    rebuilt = prefix + selected_texts[0]
    for separator, text in zip(separators, selected_texts[1:]):
        rebuilt += separator + text
    if len(selected_texts) > 1 and len(separators) < len(selected_texts) - 1:
        for text in selected_texts[len(separators) + 1 :]:
            rebuilt += " " + text
    rebuilt += suffix
    return rebuilt


def restore_storyreasoning_content(input_json, mapping_json, output_json):
    with input_json.open("r", encoding="utf-8") as handle:
        benchmark = json.load(handle)
    with mapping_json.open("r", encoding="utf-8") as handle:
        mapping = json.load(handle)

    needed_story_ids = {
        str(info["source_story_id"])
        for info in mapping.values()
        if info.get("dataset") == "storyreasoning"
    }
    source_stories, source_name = load_storyreasoning_source(needed_story_ids)

    restored = 0
    for story in benchmark:
        if story.get("dataset") != "storyreasoning":
            continue

        global_id = str(story["global_id"])
        story_mapping = mapping[global_id]
        source_story_id = str(story_mapping["source_story_id"])
        source_frames = source_stories[source_story_id]
        source_image_numbers = story_mapping["source_image_numbers"]
        benchmark_image_orders = story_mapping["benchmark_image_orders"]

        upstream_story_text = build_story_text(
            source_frames,
            source_image_numbers,
            benchmark_image_orders,
            {},
        )
        story["story_text"] = build_story_text(
            source_frames,
            source_image_numbers,
            benchmark_image_orders,
            story_mapping.get("text_overrides", {}),
        )

        context_formats = story_mapping.get("question_context_format", {})
        for question_id, question in story.get("questions", {}).items():
            question["story_context"] = rebuild_story_context(
                story["story_text"],
                upstream_story_text,
                question.get("image_paths", []),
                context_formats.get(question_id, {}),
            )

        restored += 1

    output_json.write_text(
        json.dumps(benchmark, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"StoryReasoning source: {source_name}")
    print(f"Restored StoryReasoning stories: {restored}")
    print(f"Saved output: {output_json}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Restore StoryReasoning story_text and story_context into the benchmark JSON."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_JSON,
        help="Benchmark JSON to update. Default: data/multivationbench.json",
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=DEFAULT_MAPPING_JSON,
        help="StoryReasoning mapping JSON. Default: data/mappings/storyreasoning_mapping.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Output JSON path.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    restore_storyreasoning_content(args.input, args.mapping, args.output)
