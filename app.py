import numpy as np
import gradio as gr
from transformers import AutoFeatureExtractor, AutoTokenizer, VisionEncoderDecoderModel
import re
import jaconv
import cutlet
import translators as ts
from requests.exceptions import HTTPError

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

def infer(image, deepL, google):
    image = image.convert('L').convert('RGB')
    pixel_values = feature_extractor(image, return_tensors="pt").pixel_values
    ouput = model.generate(pixel_values)[0]
    text = tokenizer.decode(ouput, skip_special_tokens=True)
    text = post_process(text)
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
        

iface = gr.Interface(
    fn=infer,
    inputs=[
        gr.components.Image(label="Input", type="pil"),
        gr.components.Checkbox(True, label="Translate with DeepL"),
        gr.components.Checkbox(True, label="Translate with Google")],
    outputs= [
        gr.components.Text(label="Original Text"),
        gr.components.Text(label="Romaji"), 
        gr.components.Text(label="DeepL Translation"),
        gr.components.Text(label="Google Translation")],
    title="Optical Character Recognition and Translation Suggestions",
    description="Load image, use image edit to select the region you want to process, submit",
   # article= "Author: <a href=\"https://huggingface.co/vumichien\">Vu Minh Chien</a>. ",
    allow_flagging='never'
)
iface.launch(enable_queue=True)
