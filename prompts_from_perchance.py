import pathlib
import modules.scripts as scripts
import gradio as gr
import random
import requests
from modules.processing import process_images, Processed, StableDiffusionProcessing
import os
import subprocess
from subprocess import CompletedProcess
from modules import images
from modules.processing import Processed, process_images
from modules.shared import opts, state


perchance_proxy = "http://localhost:7864/generate?name="
perchance_proxy_instance: CompletedProcess = None
perchance_file_path = pathlib.Path('scripts\perchance_proxy')

def get_perchance(name):
    return(requests.get(perchance_proxy+name).content.decode('utf-8'))


def get_local_perchance_files():
    global perchance_file_path
    valid_files: list = []
    perchance_validation_pattern = 'let __selectOneMethod = function()'
    html_files = [f for f in os.listdir(perchance_file_path) if f.endswith('.html')]
    for file in html_files:
        file_path = os.path.join(perchance_file_path,file)
        with open(file_path, 'r',encoding='utf-8') as fh:
            if perchance_validation_pattern in fh.read():
                valid_files.append(file.strip('.html'))
    return valid_files

def delete_local_perchance_files():
    global perchance_file_path
    html_files = [f for f in os.listdir(perchance_file_path) if f.endswith('.html')]
    for file in html_files:
        file_path = os.path.join(perchance_file_path,file)
        os.remove(file_path)
    return "Local Perchance cache was cleared"

def node_install():
    # Not working yet
    print("Checking Node version")
    global perchance_file_path
    node = subprocess.run(["node","-v"],shell=True,cwd=perchance_file_path)
    if node.returncode == 1:
        return "Node.js/NPM required"
    print("Installing Node package dependencies")
    npm = subprocess.run(["npm","install"],shell=True,cwd=perchance_file_path)
    if npm.returncode == 1:
        return "Install failed."

def run_local_perchance_proxy():
    global perchance_proxy_instance, perchance_file_path
    """Run local Node.js proxy"""
    proxy_js = perchance_file_path.joinpath("perchance_proxy.js")
    print(f"proxy location: {proxy_js}")
    # Check if running, 
    try:
        stopped = perchance_proxy_instance.poll()
    except:
        stopped = 1
    if stopped:
        perchance_proxy_instance = subprocess.Popen(f"node {proxy_js}",shell=True)
    else: 
        print("Perchance Proxy already running")
    message = f"Node Running on pid {perchance_proxy_instance.pid}"
    print(message)
    return message

class Script(scripts.Script):
    def title(self):
        return "Perchance"

    def ui(self, is_img2img):
        with gr.Accordion(label="Instructions",open=False):
            gr.Markdown("You must have Node.js installed to run the Perchance proxy service. Expand Proxy settings and click `Start`. Insert `{perchance}` into prompt text and it will be replaced with perchance output. Enter in name of Perchance generator (last part of URL) Proxy must be running.")
        with gr.Accordion("History",open=True) as history:
            with gr.Row():
                history_dropdown = gr.Dropdown(get_local_perchance_files(),label="Prompt History",type='value')
                history_submit = gr.Button("Submit")
        generator_name = gr.Textbox(label="Generator Name",elem_id='generator-name')
        output = gr.Textbox(label="Perchance Output",elem_id="perchance-output")
        refresh_on_run = gr.Checkbox(label="Refresh on each run")
        sequential = gr.Checkbox(label="Sequential seeds")
        refresh = gr.Button(value="Refresh")
        with gr.Accordion("Proxy",open=False) as proxy:
            with gr.Row():
                install_deps = gr.Button("Install Dependencies")
                proxy_start = gr.Button("Start Proxy")
                reset_cache = gr.Button("Reset Cache")
            proxy_message = gr.Textbox(label="Proxy Status", interactive=False)
        history_submit.click(None, inputs=[history_dropdown],outputs=[generator_name])
        refresh.click(get_perchance,inputs=[generator_name],outputs=[output])
        proxy_start.click(run_local_perchance_proxy,inputs=[],outputs=[proxy_message])
        install_deps.click(node_install,inputs=[],outputs=[proxy_message])
        reset_cache.click(delete_local_perchance_files,inputs=[],outputs=[proxy_message])

        # TODO Implement install_deps and install_node
        return [generator_name, output, refresh_on_run, sequential, proxy_message]

    def run(self, p: StableDiffusionProcessing, generator_name, output, refresh_on_run, sequential, proxy_message: gr.Textbox):
        original_prompt: str = p.prompt[0] if type(p.prompt) == list else p.prompt

        if perchance_proxy_instance.poll() == 0:
            raise Exception("Perchance Proxy not running. Ensure node.js is installed and click 'Install Dependencies' then 'Start Proxy'")
            
        # Randomize prompt if enabled. Currently disregards batch size.
        # Intercepts batch_count and (p_iter) and 
        if refresh_on_run and not p.n_iter == 1:
            all_images = []
            batch_count = p.n_iter
            p.n_iter = 1
            p.batch_size = 1
            state.job_count = batch_count
            initial_seed = None
            for i in range(batch_count):
                if state.interrupted:
                    break
                p.do_not_save_grid = True

                # Do the actual thing this script is supposed to do.
                p.prompt = original_prompt.replace("{perchance}",get_perchance(generator_name))
                state.job = f"Batch {i + 1}/{batch_count}"
                processed = process_images(p)
                
                # Capture initial info for the set
                if initial_seed is None:
                    initial_seed = processed.seed
                    initial_info = processed.info

                if sequential:
                    p.seed = processed.seed +1
                else:
                    p.seed = -1

                all_images.append(processed.images[0])
            
            # Return the grid only if >1 picture
            if batch_count > 1:
                grid = images.image_grid(all_images)
                if opts.grid_save:
                    images.save_image(grid, p.outpath_grids, "grid", processed.seed, p.prompt, opts.grid_format, info=processed.info, short_filename=not opts.grid_extended_filename, grid=True, p=p)
                
                if opts.return_grid:
                    all_images = [grid] + all_images
                
            processed = Processed(p, all_images, initial_seed, initial_info)
                
        else:
            # Do the actual thing this script is supposed to do.
            p.prompt = original_prompt.replace("{perchance}",output)
            processed = process_images(p)
        return processed
