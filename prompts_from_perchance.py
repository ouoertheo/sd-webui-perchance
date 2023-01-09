
import modules.scripts as scripts
import gradio as gr
import requests
from modules.processing import process_images, Processed, StableDiffusionProcessing

from modules import ui, images
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
        refresh_on_run = gr.Checkbox(label="Refresh on each run")
        refresh = gr.Button(value="Refresh")
        refresh.click(get_perchance,inputs=[generator_name],outputs=[output])
        return [generator_name, output, refresh_on_run, refresh]

    def run(self, p: StableDiffusionProcessing, generator_name, output, refresh_on_run, refresh):
        original_prompt: str = p.prompt[0] if type(p.prompt) == list else p.prompt

        if "{perchance}" not in original_prompt:
            raise Exception("Missing {perchance} in prompt")

        if refresh_on_run and not p.n_iter == 1:
            all_images = []
            batch_count = p.n_iter
            p.n_iter = 1
            p.batch_size = 1
            initial_seed = None
            for i in range(batch_count):
                p.do_not_save_grid = True
                p.prompt = original_prompt.replace("{perchance}",get_perchance(generator_name))
                state.job = f"Batch {i + 1}/{batch_count}"
                processed = process_images(p)
                
                if initial_seed is None:
                    initial_seed = processed.seed
                    initial_info = processed.info

                p.seed = processed.seed + 1
                all_images.append(processed.images[0])
                
            grid = images.image_grid(all_images, rows=1)
            if opts.grid_save:
                images.save_image(grid, p.outpath_grids, "grid", processed.seed, p.prompt, opts.grid_format, info=processed.info, short_filename=not opts.grid_extended_filename, grid=True, p=p)
            
            if opts.return_grid:
                all_images = [grid] + all_images
                
            processed = Processed(p, all_images, initial_seed, initial_info)
                
        else:
            p.prompt = original_prompt.replace("{perchance}",output)
            processed = process_images(p)
        return processed
