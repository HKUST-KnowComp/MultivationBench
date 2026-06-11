#!/bin/bash

# Authentication credentials
usernameMD=
passwordMD=
parallelDownloads=5  # Adjust based on your system

# Paths
json_folders="data/moviebench_split.json"  # Benchmark MovieBench split metadata
json_scenes="Datasets/movie/movies_scenes.json"  # MovieBench scene metadata from upstream
output_dir="Datasets/movie/videos"
mkdir -p "$output_dir"

# Step 1: Download annotations (optional, or use moviebench_split.json if it replaces them)
wget http://datasets.d2.mpi-inf.mpg.de/movieDescription/protected/lsmdc2016/LSMDC16_annos_training.csv --user="$usernameMD" --password="$passwordMD" -P "$output_dir"
wget http://datasets.d2.mpi-inf.mpg.de/movieDescription/protected/lsmdc2016/LSMDC16_annos_val.csv --user="$usernameMD" --password="$passwordMD" -P "$output_dir"
wget http://datasets.d2.mpi-inf.mpg.de/movieDescription/protected/lsmdc2016/LSMDC16_annos_test.csv --user="$usernameMD" --password="$passwordMD" -P "$output_dir"
wget http://datasets.d2.mpi-inf.mpg.de/movieDescription/protected/lsmdc2016/LSMDC16_annos_blindtest.csv --user="$usernameMD" --password="$passwordMD" -P "$output_dir"

# Step 2: Download the video download links file
wget http://datasets.d2.mpi-inf.mpg.de/movieDescription/protected/lsmdc2016/MPIIMD_downloadLinks.txt --user="$usernameMD" --password="$passwordMD" -P "$output_dir"
filesToDownloadMD="$output_dir/MPIIMD_downloadLinks.txt"

# Step 3: Filter video URLs based on JSONs
# Requires jq - install with `sudo apt-get install jq` or equivalent
filtered_links="$output_dir/filtered_downloadLinks.txt"
> "$filtered_links"  # Clear or create the filtered links file

# Read movies to keep from the folders JSON
movies=$(jq -r '.Test[]' "$json_folders")

# Read timestamps from the movies_scenes JSON
if [ -f "$json_scenes" ]; then
    for movie in $movies; do
        timestamps=$(jq -r ".\"$movie\"[] | .[]" "$json_scenes" 2>/dev/null)
        if [ -n "$timestamps" ]; then
            for timestamp in $timestamps; do
                grep "$timestamp" "$filesToDownloadMD" >> "$filtered_links"
            done
        else
            echo "Warning: No timestamps found for $movie in $json_scenes."
        fi
    done
else
    echo "Error: $json_scenes not found."
    exit 1
fi

# Step 4: Download only the filtered video clips
if [ -s "$filtered_links" ]; then
    cat "$filtered_links" | xargs -n 1 -P "$parallelDownloads" wget -c -q --user="$usernameMD" --password="$passwordMD" -P "$output_dir"
    echo "Download completed. Videos saved in $output_dir."
else
    echo "Error: No matching clips found in $filtered_links. Check JSONs or MPIIMD_downloadLinks.txt."
fi
