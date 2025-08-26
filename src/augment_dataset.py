import os
import json
import time
import re
import argparse
from openai import OpenAI
from tqdm import tqdm

# --- CONFIGURATION ---

# Point the client to your local Ollama server
# This is the "magic" that makes it use your local model
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',  # required, but the value can be anything
)

# Define the source, destination, and model to use
SOURCE_FILE = "data/validated_dataset.jsonl"
DESTINATION_FILE = "data/augmented_dataset.jsonl"
MODEL_TO_USE = "llama3:8b" # Or "phi3:mini", etc.
VARIATIONS_PER_ENTRY = 4 # How many messy versions to create for each clean one

def get_meta_prompt():
    """
    Returns the master prompt template used to guide the LLM.
    This is where we tell the AI how to behave.
    """
    return f"""
You are a data augmentation specialist for a machine learning project. Your task is to create realistic, varied, and sometimes "messy" user prompts based on a perfect, "textbook" example.

Your goal is to generate {VARIATIONS_PER_ENTRY} alternative prompts for the provided CadQuery script. These alternative prompts must correspond to the EXACT same output code.

The variations should include a mix of the following styles:
1.  **Casual Synonyms & Slang:** Use words like "thingy," "block," "slab," "cutout" instead of formal terms.
2.  **Typos & Grammatical Errors:** Introduce common spelling mistakes (e.g., "cilinder," "filit") and imperfect grammar.
3.  **Missing Punctuation & Connectors:** Write prompts like a user might type into a search bar, omitting words like "a," "the," "with," "and."
4.  **Conversational Fillers:** Add phrases like "Hey, can you make me a...", "I was wondering if...", "Okay so I need... thanks."

Here is an example of the desired output:

---
**EXAMPLE INPUT:**
{{
  "instruction": "Create a thin rectangular plate",
  "input": "Make a flat plate 50mm by 30mm with 2mm thickness",
  "output": "import cadquery as cq\\n\\nresult = cq.Workplane(\\"XY\\").box(50, 30, 2)"
}}

**EXAMPLE DESIRED OUTPUT:**
[
  "a 50 by 30 slab, make it 2mm high",
  "hey can u generate a flat plate for me 50mm x 30mm but only 2mm thick?",
  "plate 50 30 2",
  "Make flat plat 50mm by 30mm with 2mm thicknes"
]
---

Now, generate {VARIATIONS_PER_ENTRY} variations for the following data point. Please provide your response ONLY as a valid JSON list of strings, with no other text before or after it.

**DATA POINT TO AUGMENT:**
{{
  "instruction": "{{instruction}}",
  "input": "{{input}}",
  "output": "{{output}}"
}}
"""

def generate_variations(data_point: dict) -> list[str]:
    """Calls the local LLM API to generate prompt variations."""
    prompt_template = get_meta_prompt()
    
    full_prompt = prompt_template.format(
        instruction=data_point['instruction'],
        input=data_point['input'],
        output=data_point['output']
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL_TO_USE,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.8, # Encourage creativity
        )
        
        response_text = response.choices[0].message.content
        
        # A robust way to find the JSON list inside the LLM's response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if not json_match:
            print(f"\nWarning: Could not find a JSON list in the LLM response: {response_text}")
            return []
            
        variations = json.loads(json_match.group(0))
        
        if isinstance(variations, list) and all(isinstance(i, str) for i in variations):
            return variations
        else:
            print(f"\nWarning: LLM returned unexpected format: {response_text}")
            return []
            
    except Exception as e:
        print(f"\nAn API or JSON parsing error occurred: {e}")
        return []

def main(limit: int):
    """
    Main function to run the augmentation process.
    """
    print("Starting dataset augmentation...")
    print(f"Source: {SOURCE_FILE}")
    print(f"Destination: {DESTINATION_FILE}")
    print(f"Model: {MODEL_TO_USE}")

    try:
        with open(SOURCE_FILE, 'r') as f_in:
            lines = f_in.readlines()
    except FileNotFoundError:
        print(f"Error: Source file not found at {SOURCE_FILE}")
        return

    lines_to_process = lines if limit == -1 else lines[:limit]

    with open(DESTINATION_FILE, 'w') as f_out:
        for line in tqdm(lines_to_process, desc="Augmenting Dataset"):
            try:
                clean_data = json.loads(line)
                
                # 1. Write the original, clean data point to the new file
                f_out.write(json.dumps(clean_data) + '\n')
                
                # 2. Generate and write the messy variations
                variations = generate_variations(clean_data)
                for messy_input in variations:
                    augmented_data = {
                        "instruction": clean_data["instruction"],
                        "input": messy_input,
                        "output": clean_data["output"]
                    }
                    f_out.write(json.dumps(augmented_data) + '\n')
                
                # Be a good citizen to your local server
                time.sleep(0.5)

            except json.JSONDecodeError:
                print(f"\nWarning: Skipping malformed JSON line: {line.strip()}")
                continue
    
    print(f"\nAugmentation complete. Output saved to {DESTINATION_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Augment a dataset using a local LLM.")
    parser.add_argument(
        "-l", "--limit", 
        type=int, 
        default=-1, 
        help="Limit the number of lines to process for testing. Default is -1 (all lines)."
    )
    args = parser.parse_args()
    
    main(args.limit)