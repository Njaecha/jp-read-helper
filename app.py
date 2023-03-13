import numpy as np
import gradio as gr
from transformers import AutoFeatureExtractor, AutoTokenizer, VisionEncoderDecoderModel
import re
import jaconv
import cutlet
import translators as ts
from requests.exceptions import HTTPError
from PIL import Image as PILImage
import pytesseract


#load model
model_path = "model/"
feature_extractor = AutoFeatureExtractor.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = VisionEncoderDecoderModel.from_pretrained(model_path)
            
def post_process(text):
    text = ''.join(text.split())
    text = text.replace('…', '...')
    text = re.sub('[・.]{2,}', lambda x: (x.end() - x.start()) * '.', text)
    text = jaconv.h2z(text, ascii=True, digit=True)
    return text

def JPOCR(image):
    image = image.convert('L').convert('RGB')
    pixel_values = feature_extractor(image, return_tensors="pt").pixel_values
    ouput = model.generate(pixel_values)[0]
    text = tokenizer.decode(ouput, skip_special_tokens=True)
    return post_process(text)

def process(image, deepL, google):
    text = JPOCR(image)
    romaji = romanise(text)
    deepLText = "DeepL translation is turned off"
    if (deepL):
        deepLText = translate(text, "deepl")
    googleText = "Google translation is truned off"
    if (google):
        googleText = translate(text, "google")
    return (text, romaji, deepLText, googleText)

def romanise(text):
    c = cutlet.Cutlet()
    return c.romaji(text)

def translate(text, translator):
    try:
        translation = ts.translate_text(text, translator, "ja", "en")
        print(f"Translated using {translator}:\n   Input: {text}\n   Output: {translation}")
        return translation
    except HTTPError as e:
        print(f"An HTTPError occoured while translating with {translator}:\n   {e}")
        return e

with gr.Blocks(title="Optical Character Recognition and Translation Suggestions", css="custom-style.css", ) as UI:
    gr.Markdown("# Optical Character Recognition and Translation Suggestions", elem_id="title-text")
    
    with gr.Row():
        with gr.Column():
            image = gr.Image(label="Input", type="pil", elem_id="input-img")
            deepL = gr.Checkbox(True, label="Translate with DeepL")
            google = gr.Checkbox(True, label="Translate with Google")
            btn = gr.Button("Analyse")
        with gr.Column():
            org = gr.Text(label="Original Text")
            romaji = gr.Text(label="Romaji")
            deepLText = gr.Text(label="DeepL Translation")
            googleText = gr.Text(label="Google Translation")

    btn.click(process
, inputs=[image, deepL, google], outputs=[org, romaji, deepLText, googleText])

if __name__ == "__main__":
    UI.launch()