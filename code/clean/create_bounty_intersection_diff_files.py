"""
Purpose:
- Create three different files that capture the intersection and differences in the two different sets of collected bounty data.

Inputs:
- None.
- Data is read via constants defined below.

Outputs:
- `bounties_in_blur_and_non_blur.txt`: cleaned text file where each line contains the following
    - bounty_number (str): Unique identifier for the bounty which are common in the blurred and the non-blurred data.
- `bounties_in_w_blur_not_in_wo_blur.txt`: cleaned text file where each line contains the following
    - bounty_number (str): Unique identifier for the bounty which are present in the blurred data but not in the non-blurred data.
- `bounties_in_wo_blur_not_in_w_blur.txt`: cleaned text file where each line contains the following:
    - bounty_number (str): Unique identifier for the bounty which are not present in the blurred data but in the non-blurred data.

Author:
- Shalmoli Ghosh
"""

import os

# Constants
BOUNTIES_WO_BLUR_DIR = "../../data/bounties/"
BOUNTIES_W_BLUR_DIR = "../../data/bounties_with_blur"
OUT_DIR = "../../data/intermediate"

# Ensure the current directory is where the script is located so relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Get files, which have the bounty number in the filename
files = [file for file in os.listdir(BOUNTIES_WO_BLUR_DIR) if file.endswith(".json")]
files_blurred = [
    file for file in os.listdir(BOUNTIES_W_BLUR_DIR) if file.endswith(".json")
]

# Get intersection and difference in the two different sets of files
common_bounties = list(set(files) & set(files_blurred))
bounties_in_w_blur_not_in_wo_blur = list(set(files_blurred).difference(set(files)))
bounties_in_wo_blur_not_in_w_blur = list(set(files).difference(set(files_blurred)))

# Convert elements to integers, extracting the numbers from the filenames
# File form example: bounty_1234.json
common_bounties = [
    int(bounty.replace("bounty_", "").replace(".json", ""))
    for bounty in common_bounties
]
bounties_in_w_blur_not_in_wo_blur = [
    int(bounty.replace("bounty_", "").replace(".json", ""))
    for bounty in bounties_in_w_blur_not_in_wo_blur
]
bounties_in_wo_blur_not_in_w_blur = [
    int(bounty.replace("bounty_", "").replace(".json", ""))
    for bounty in bounties_in_wo_blur_not_in_w_blur
]

# Create output files and save the results
out_fp_common_bounties = os.path.join(OUT_DIR, "bounties_in_blur_and_non_blur.txt")
out_fp_bounties_in_w_blur_not_in_wo_blur = os.path.join(
    OUT_DIR, "bounties_in_w_blur_not_in_wo_blur.txt"
)
out_fp_bounties_in_wo_blur_not_in_w_blur = os.path.join(
    OUT_DIR, "bounties_in_wo_blur_not_in_w_blur.txt"
)
with open(out_fp_common_bounties, "w") as f:
    for bounty_number in sorted(common_bounties):
        f.write(f"{bounty_number}\n")

with open(out_fp_bounties_in_w_blur_not_in_wo_blur, "w") as f:
    for bounty_number in sorted(bounties_in_w_blur_not_in_wo_blur):
        f.write(f"{bounty_number}\n")

with open(out_fp_bounties_in_wo_blur_not_in_w_blur, "w") as f:
    for bounty_number in sorted(bounties_in_wo_blur_not_in_w_blur):
        f.write(f"{bounty_number}\n")

print(f"Common bounties: {len(common_bounties)}")
print(f"Bounties in w_blur not in wo_blur: {len(bounties_in_w_blur_not_in_wo_blur)}")
print(f"Bounties in wo_blur not in w_blur: {len(bounties_in_wo_blur_not_in_w_blur)}")
print("Files created successfully!")
