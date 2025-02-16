# -*- coding: utf-8 -*-
"""
Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1kv5VQT8_c4Ufh2yHYcnL5aT9rsvtS1d4
"""

# Importing the necessary libraries

import torch
from IPython.display import display
from diffusers import DiffusionPipeline
from transformers import pipeline
import streamlit as st
from PIL import Image
import openai
import torch._dynamo
torch._dynamo.config.suppress_errors = True


#Loading the Stable Diffusion XL Models

# Load the Stable Diffusion XL base model
base = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True
)
base.to("cuda")

# Load the Stable Diffusion XL refiner model
refiner = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-refiner-1.0",
    text_encoder_2=base.text_encoder_2,
    vae=base.vae,
    torch_dtype=torch.float16,
    use_safetensors=True,
    variant="fp16",
)
refiner.to("cuda")


#openai.api_key = "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"

# Loading GPT and BERT as NLU Models
# Load GPT model for NLU
# nlu_model_gpt = pipeline("text2text-generation", model="gpt-3.5-turbo")

# Load BERT model for NLU
nlu_model_bert = pipeline("fill-mask", model="bert-base-uncased")

# Define the Prompt Processing Function

def process_prompt_with_nlu(prompt, model_type="gpt", mode="literal"):
    refined_prompt = prompt  # Default to literal

    if model_type == "gpt":
        if mode == "creative":
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",   # this is the model as GPT NLU model that's why "nlu_model_gpt" is commented above
                messages=[
                    {"role": "system", "content": "You are a creative assistant."},
                    {"role": "user", "content": f"Create a creative and vivid description for: {prompt}"}
                ]
            )
            refined_prompt = response['choices'][0]['message']['content'].strip()
        elif mode == "paraphrased":
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a paraphrasing assistant."},
                    {"role": "user", "content": f"Paraphrase the following: {prompt}"}
                ]
            )
            refined_prompt = response['choices'][0]['message']['content'].strip()
        elif mode == "summarized":
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a summarizing assistant."},
                    {"role": "user", "content": f"Summarize the following: {prompt}"}
                ]
            )
            refined_prompt = response['choices'][0]['message']['content'].strip()
        elif mode == "detail":
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a detailed description assistant."},
                    {"role": "user", "content": f"Add more details to the following: {prompt}"}
                ]
            )
            refined_prompt = response['choices'][0]['message']['content'].strip()

    elif model_type == "bert":
        if mode != "literal":
            masked_prompt = prompt.replace("a ", "[MASK] ")
            refined_prompt = nlu_model_bert(masked_prompt)[0]['sequence']

    return refined_prompt


# Define the Image Generation Function

def generate_image_with_nlu(prompt, mode="literal", model_type="gpt"):
    refined_prompt = process_prompt_with_nlu(prompt, model_type, mode)
    print(f"Refined Prompt ({mode}): {refined_prompt}")

    n_steps = 40
    high_noise_frac = 0.8

    image = base(
        prompt=refined_prompt,
        num_inference_steps=n_steps,
        denoising_end=high_noise_frac,
        output_type="latent",
    ).images
    image = refiner(
        prompt=refined_prompt,
        num_inference_steps=n_steps,
        denoising_start=high_noise_frac,
        image=image,
    ).images[0]

    return image


# Create Streamlit Interface

def main():
    st.title("Stable Diffusion XL with Customizable NLU")

    # User input for the prompt
    prompt = st.text_area("Enter your description", "A majestic lion jumping from a big stone at night")

    # Interpretation mode selection
    mode = st.selectbox("Choose Interpretation Mode", ["Literal", "Creative", "Paraphrased", "Detail"])

    # Model type selection
    model_type = st.selectbox("Choose NLU Model", ["GPT", "BERT"])

    # Optional negative prompts
    negative_prompt = st.text_area("Enter any negative prompts (optional)", "")

    # Generate button
    if st.button("Generate Image"):
        with st.spinner("Generating image..."):
            image = generate_image_with_nlu(prompt, mode=mode.lower(), model_type=model_type.lower())
            st.image(image, caption="Generated Image")

    # Clear button
    if st.button("Clear"):
        st.caching.clear_cache()

if __name__ == "__main__":
    main()

