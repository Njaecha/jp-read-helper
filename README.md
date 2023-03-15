Project is Work in Progress

Tool to help with reading and translating japanese text from images. I mainly developed this to help my learn japanese while translating manga.

## Installation
1. Clone repository (`git clone https://github.com/NiggoJaecha/jp-read-helper.git`) into a directory of choice
2. Install requirements:
     - python 3.9/3.10
     - run: `pip install -r requirements.txt`. Pip may ask you to install Visual C++ 14+, do so. 
3. Download the OCR model from [this Space](https://huggingface.co/spaces/Detomo/Japanese-OCR) (`Files and Verisons` -> `model` -> `pytorch_model.bin`) and put it into the `model` folder.
4. **(Optional)** Register for a (free) [DeepL API plan](https://www.deepl.com/pro-api?cta=header-pro-api), which requires a credit card or similiar.

## Usage
![Main UI](https://i.imgur.com/lMJ4wEz.png)
- Upload or drop a image into the field on the left
- Cut down the image to the area of a section of text (speech bubble) using the edit mode
- With the `Restore` button, you can restore the image which was uploaded/dropped after the last time the image was cleared (with `[x]`)
- The checkboxes enable/disable deepL and google translation
- `Use official API` enables deepL to use the official API which requires you to have a authorisation key configured in the settings.
- Click `Analyse` to read the characters from the image.
- Click `Translate` to translate text in the `Original Text` field
- The `Original Text` field can be edited to fix OCR errors or to use the tool without OCR.
- The `Romaji` field shows a roman transcription of the original text and is updated live.
- The `DeepL-` and `Google Translation` fields show the translated text, or an error message.
- In the `Actual Translation` field you can write your own translation.
- `Save results` feature:
    - Choose a `Directory` and a `Filename` (usually you would reference the page or original image here).
    - Set a `Text Index` (usually you number the different speech bubbles in order, but you can also use arbitrary text) 
    - Clicking `Save Result` will append the result to the specified file using **a schema defined in the settings**, which can (but does not have to) contain any of the following keys (will be replaced with their according field when saving):
        - `{textIndex}`: the specified text index
        - `{org}`: the original text
        - `{romaji}`: the romaji transcription
        - `{deepL}`: the deepL translation
        - `{googleT}`: the google translation
        - `{transT}`: the actual translation
    - A message will pop up telling when the message was saved. It will go away if you change any of the three save result fields.

## Credits

Thanks goes to the author of the perviously mentioned hugginface space, which this tool is based on: `Vu Minh Chien`.