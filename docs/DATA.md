# Data Access And Recovery

MulTivationBench contains 1,000 visual narratives, 4,023 visually grounded
character behaviors, and 16,092 multi-label evaluation questions.

## What Is Released

| File | Description |
| --- | --- |
| `data/multivationbench.json` | Release-safe benchmark source file |
| `data/moviebench_split.json` | MovieBench split metadata used by the download helper |
| `data/mappings/ssid_mapping.json` | Mapping from benchmark IDs to upstream SSID story IDs |
| `data/mappings/storyreasoning_mapping.json` | Mapping from benchmark IDs to upstream StoryReasoning story IDs and frames |
| `scripts/restore_ssid_content.py` | Reconstructs SSID story text and question contexts |
| `scripts/restore_storyreasoning_content.py` | Reconstructs StoryReasoning story text, image paths, and question contexts |
| `scripts/generate_gt_with_story.py` | Runs both restoration steps |
| `scripts/download_moviebench.sh` | Filters and downloads MovieBench/LSMDC source clips |

`data/multivationbench.json` preserves the MulTivationBench annotations but removes
source story content for SSID and StoryReasoning because those upstream datasets
include no-derivatives restrictions. The file keeps MovieBench story text,
question context, and image paths as currently packaged.

## JSON Structure

Each top-level item is one story:

```json
{
  "global_id": 1,
  "dataset": "ssid",
  "story_text": null,
  "questions": {
    "1_1": {
      "character": "...",
      "image_paths": ["..."],
      "question_stem": "...",
      "maslow_options": ["A: ..."],
      "maslow_answer": ["C"],
      "reiss_options": ["A: ..."],
      "reiss_answer": ["I"],
      "maslow_std_question": "...",
      "maslow_std_options": ["A: ..."],
      "maslow_std_answer": ["C"],
      "reiss_std_question": "...",
      "reiss_std_options": ["A: ..."],
      "reiss_std_answer": ["I"]
    }
  }
}
```

The practical motivation tasks use `maslow_options` / `maslow_answer` and
`reiss_options` / `reiss_answer`. The definition tasks use the corresponding
`*_std_question`, `*_std_options`, and `*_std_answer` fields.

## Restore SSID Content

Download the official SSID files from the upstream source, then arrange them as:

```text
Datasets/
  SSID/
    SSID_Train.json
    SSID_Test.json
    SSID_Validation.json
    SSID_Images/
      *.jpg
```

Run:

```bash
python scripts/restore_ssid_content.py \
  --input data/multivationbench.json \
  --mapping data/mappings/ssid_mapping.json \
  --output data/multivationbench.ssid_restored.json
```

## Restore StoryReasoning Content

The StoryReasoning restoration script first tries the upstream StoryReasoning
loader. If that is unavailable, it falls back to the local cache at
`result/final_dataset/stories.json` when present.

Run:

```bash
python scripts/restore_storyreasoning_content.py \
  --input data/multivationbench.json \
  --mapping data/mappings/storyreasoning_mapping.json \
  --output data/multivationbench.storyreasoning_restored.json
```

## Generate A Combined File

After the upstream dependencies are available locally, run:

```bash
python scripts/generate_gt_with_story.py \
  --input data/multivationbench.json \
  --output data/multivationbench_with_story.json
```

This restores SSID first, then StoryReasoning. MovieBench content is already
kept in `data/multivationbench.json`.

## MovieBench Notes

MovieBench source media is not fully automated in this package. The current
release provides:

- `data/moviebench_split.json`
- `scripts/download_moviebench.sh`
- MovieBench image paths with embedded timestamps

Users should obtain `movies_scenes.json` from the MovieBench release and place
it at:

```text
Datasets/movie/movies_scenes.json
```

Then use the MovieBench/LSMDC credentials required by the upstream source and
run the download helper. The downloaded clips can be used to recover frames from
the timestamps encoded in the image filenames.

## License And Use Restrictions

MulTivationBench derives from:

- MovieBench: CC BY 4.0
- StoryReasoning: CC BY-ND 4.0
- SSID: CC BY-NC-ND 4.0

This repository does not redistribute upstream images, videos, story texts, or
substantial upstream source materials. Users must obtain those files directly
from the original sources and comply with their licenses.

The SSID-derived portion is restricted to non-commercial academic research and
evaluation. Only the newly created MulTivationBench question-answer annotations
are intended to be modified or further derived under the authors' release terms.
This permission does not extend to upstream source content.
