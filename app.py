import numpy as np
import gradio as gr
from transformers import AutoFeatureExtractor, AutoTokenizer, VisionEncoderDecoderModel
import re
import jaconv
import cutlet
import translators as ts
from requests.exceptions import HTTPError
from PIL import Image as PILImage
import os
import json

SUPPORTED_FORMATS = ["dds", "png", "jpg", "jpeg", "webp", "bmp", "gif", "tga"] # incomplete list but im lazy

DEFAULT_SAVE_SCHEMA = """
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
==============================
"""

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

def process(image):
    text = JPOCR(image)
    romaji = romanise(text)
    return (text, romaji)

def trans(text, deepL, google):
    deepLText = "DeepL translation is turned off"
    if (deepL):
        deepLText = translate(text, "deepl")
    googleText = "Google translation is truned off"
    if (google):
        googleText = translate(text, "google")
    return (deepLText, googleText)

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

def saveSettings(deepl, saveSchema):
    with open("settings.json", "w") as f:
        settings = {
            "deepl-api-key": deepl,
            "save-schema": saveSchema
        }
        json.dump(settings, f, indent=4)

def loadSettings():
    if not os.path.exists("settings.json"):
        saveSettings("<api-key-here>", DEFAULT_SAVE_SCHEMA)
    with open("settings.json", "r") as f:
        return json.load(f)


def saveAnalysis(org, romaji, deepL, googleT, transT, directory, filename, textIndex):
    section = "\n"+str(loadSettings()["save-schema"])+"\n"
    section = section.replace("{textIndex}", textIndex)
    section = section.replace("{org}", org)
    section = section.replace("{romaji}", romaji)
    section = section.replace("{deepL}", deepL)
    section = section.replace("{googleT}", googleT)
    section = section.replace("{transT}", transT)

    if not os.path.exists(directory):
        os.mkdir(directory)

    fp = os.path.join(directory, filename)
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

    with gr.Tab(label="Main"):
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
                restoreBtn = gr.Button("Restore", elem_id="restore-btn")
                deepL = gr.Checkbox(True, label="Translate with DeepL")
                google = gr.Checkbox(True, label="Translate with Google")
                with gr.Row():
                    analyseBtn = gr.Button("Analyse")
                    translateBtn = gr.Button("Translate")

            with gr.Column():
                org = gr.Text(label="Original Text", interactive=True)
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

        analyseBtn.click(process, inputs=[image], outputs=[org, romaji])
        translateBtn.click(trans, inputs=[org, deepL, google], outputs=[deepLText, googleText])

        org.change(romanise, inputs=[org], outputs=[romaji])

        image.change(saveImg, inputs=[image, sImage, isCleared], outputs=[sImage, isCleared])

        restoreBtn.click(restoreImg, inputs=[sImage], outputs=[image])

        saveBtn.click(saveAnalysis, inputs=[org, romaji, deepLText, googleText, transText, outputDir, filename, textIndex])
    with gr.Tab("Settings") as settingsTab:
        saveSettingsBtn = gr.Button("Save Settings")
        deeplKey = gr.Text(value=loadSettings()["deepl-api-key"], label="DeepL API Key", interactive=True)
        saveSchema = gr.Text(value=loadSettings()["save-schema"], label="Save Schema", interactive=True)
        
        saveSettingsBtn.click(saveSettings, inputs=[deeplKey, saveSchema])

if __name__ == "__main__":
    UI.launch()