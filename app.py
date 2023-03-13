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
from os import path, listdir, system, mkdir

SUPPORTED_FORMATS = ["dds", "png", "jpg", "jpeg", "webp", "bmp", "gif", "tga"] # incomplete list but im lazy

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

def saveAnalysis(org, romaji, deepL, googleT, transT, directory, filename, textIndex):
    section = f"""
== {textIndex} ====================
Original: {org}
--
Romaji: {romaji}
--
DeepL: {deepL}
--
Google: {googleT}
--
Translation: {transT}
==============================\n
"""
    if not path.exists(directory):
        mkdir(directory)

    fp = path.join(directory, filename)
    with open(fp, "a", encoding="utf-8") as file:
        file.write(section)
        print("File was appended")

with gr.Blocks(title="Optical Character Recognition and Translation Suggestions", css="custom-style.css", ) as UI:
    sImage = gr.State(None)
    isCleared = gr.State(True)

    gr.Markdown("# Optical Character Recognition and Translation Suggestions", elem_id="title-text")

    def saveImg(image, saved, cleared):
        if cleared and image != None: #save Image
            cleared = False
            saved = image
        elif image == None: #clear Image
            cleared = True
            saved = None
        return {sImage: saved, isCleared: cleared }
    
    def clearImg(saved, cleared):
        print("clearing")
        saved = None
        cleared = True
        print(cleared)
        return {sImage: saved, isCleared: cleared }
    
    def restoreImg(saved):
        return saved

    # with gr.Accordion(label="Directoryloader", open=False):
    #     with gr.Row():
    #         loadDir = gr.Textbox(label="Directory Path")
    #         loadDirBtn = gr.Button("Load", elem_id="dir-load-btn")
    #     with gr.Row(visible=True) as r:

    #         def loadDirectory(dirpath):
    #             global FILE_LIST
    #             global DIRECORY_LOADED
    #             if path.exists(dirpath):
    #                 print("load dir")
    #                 FILE_LIST.clear()
    #                 for file in listdir(dirpath):
    #                     name, extension = path.splitext(file)
    #                     if extension in SUPPORTED_FORMATS:
    #                         FILE_LIST.append(file)
    #                 DIRECORY_LOADED = True
    #                 print(DIRECORY_LOADED)
    #                 r.visible = True
    #                 UI.update()
    
    #         def changeCurrentFileIndex(by: int):
    #             global CURRENT_FILE_INDEX
    #             if by < 0 and CURRENT_FILE_INDEX > 0:
    #                 CURRENT_FILE_INDEX += by
    #             elif by > 0 and CURRENT_FILE_INDEX < len(FILE_LIST):
    #                 CURRENT_FILE_INDEX += by
    #             print(CURRENT_FILE_INDEX)

    #         prev = gr.Button("<< Previous")
    #         prev.click(changeCurrentFileIndex(-1))
    #         loadFile = gr.Button(FILE_LIST[CURRENT_FILE_INDEX])
    #         next = gr.Button("Next >>")
    #         next.click(changeCurrentFileIndex(1))
    
    #     loadDirBtn.click(loadDirectory, inputs=[loadDir])
    
    with gr.Row():
        with gr.Column():
            image = gr.Image(label="Input", type="pil", elem_id="input-img")
            deepL = gr.Checkbox(True, label="Translate with DeepL")
            google = gr.Checkbox(True, label="Translate with Google")
            with gr.Row():
                restoreBtn = gr.Button("Restore")
                btn = gr.Button("Analyse")
        with gr.Column():
            org = gr.Text(label="Original Text", interactive=False)
            romaji = gr.Text(label="Romaji", interactive=False)
            deepLText = gr.Text(label="DeepL Translation", interactive=False)
            googleText = gr.Text(label="Google Translation", interactive=False)
            transText = gr.Text(label="Actual Translation", interactive=True)
            with gr.Accordion(label="Save results", open=True):
                outputDir = gr.Text(value="./output", label="Save Directory", interactive=True, max_lines=1)
                with gr.Row():
                    filename = gr.Text(value="1.translation.txt", label="Filename", interactive=True, max_lines=1)
                    textIndex = gr.Text(value="1", label="Text index", interactive=True, max_lines=1)
                    saveBtn = gr.Button("Save Result")

    btn.click(process, inputs=[image, deepL, google], outputs=[org, romaji, deepLText, googleText])

    image.change(saveImg, inputs=[image, sImage, isCleared], outputs=[sImage, isCleared])

    restoreBtn.click(restoreImg, inputs=[sImage], outputs=[image])

    saveBtn.click(saveAnalysis, inputs=[org, romaji, deepLText, googleText, transText, outputDir, filename, textIndex])

if __name__ == "__main__":
    UI.launch()