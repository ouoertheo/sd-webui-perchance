
import modules.scripts as scripts
import gradio as gr
import requests
from modules.processing import process_images, Processed, StableDiffusionProcessing

from modules import ui
from modules.processing import Processed, process_images
from PIL import Image
from modules.shared import opts, cmd_opts, state


perchance_proxy = "http://localhost:7864/generate?name="

def get_perchance(name):
    return(requests.get(perchance_proxy+name).content.decode('utf-8'))


class Script(scripts.Script):
    def title(self):
        return "Perchance"

    def ui(self, is_img2img):
        generator_name = gr.Textbox(label="Generator Name",elem_id='generator-name')
        output = gr.Textbox(label="Perchance Output",elem_id="perchance-output")
        refresh = gr.Button(value="Refresh")
        refresh.click(get_perchance,inputs=[generator_name],outputs=[output])
        return [generator_name, output, refresh]

    def run(self, p: StableDiffusionProcessing, generator_name, output: gr.Textbox, refresh):
        original_prompt: str = p.prompt[0] if type(p.prompt) == list else p.prompt
        if "{perchance}" in original_prompt:
            prompt = original_prompt.replace("{perchance}",output)
        else:
            raise Exception("Missing {perchance} in prompt")
        p.prompt = prompt
        processed = process_images(p)
        return processed
