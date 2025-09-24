import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Set up device configuration
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model
tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
model = AutoModelForCausalLM.from_pretrained("google/gemma-2b", device_map="auto")

# Generate poem
input_text = """Write a creative poem following these rules:
- Topic: artificial intelligence and technology
- Style: modern, thoughtful, and metaphorical
- Length: 4-6 lines
- Must be original and poetic
Here's the poem:"""

inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

outputs = model.generate(
    **inputs,
    max_length=200,  # Increased for longer output
    temperature=0.7,  # Slightly reduced for more focused output
    top_p=0.9,  # Added nucleus sampling
    do_sample=True,
    num_beams=4,  # Added beam search for better coherence
    no_repeat_ngram_size=2,  # Avoid repetition
    pad_token_id=tokenizer.eos_token_id
)

decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

# Extract just the poem part (after "Here's the poem:")
if "Here's the poem:" in decoded_output:
    poem = decoded_output.split("Here's the poem:")[1].strip()
    # Remove any trailing text that might appear after the poem
    poem = poem.split("\n\n")[0].strip()
else:
    poem = decoded_output

print("\nGenerated Poem:")
print(poem)