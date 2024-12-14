from pathlib import Path
import json
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
import os
from pathlib import Path
import subprocess

import requests
import gradio as gr

from dotenv import load_dotenv

load_dotenv()
PERCHANCE_PROXY_PORT = int(os.getenv("PERCHANCE_PROXY_PORT", "7862"))


class ProxyManager:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ProxyManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.perchance_proxy = f"http://localhost:{PERCHANCE_PROXY_PORT}/generate?name="
        self.perchance_proxy_instance: subprocess.CompletedProcess = None
        self.perchance_file_path = Path(__file__).parent / "perchance_proxy"

    def proxy_init(self):
        if not self._initialized:
            self.node_install()
            self.run_local_perchance_proxy()
            self._initialized = True

    def get_perchance(self, name):
        result = requests.get(self.perchance_proxy + name).json()
        try:
            assert result["output"]
            result["output"]
            result["output"] = result["output"].replace("<BR>", "\n")
            return (
                result["output"],
                gr.Dropdown.update(choices=self.get_local_perchance_files()),
            )
        except Exception as e:
            raise Exception(f"Failed to get output: {e}")

    def get_local_perchance_files(self):
        valid_files: list = []
        perchance_validation_pattern = 'href="https://perchance.org/"'
        html_files = [
            f for f in os.listdir(self.perchance_file_path) if f.endswith(".html")
        ]
        for file in html_files:
            file_path = os.path.join(self.perchance_file_path, file)
            with open(file_path, "r", encoding="utf-8") as fh:
                if perchance_validation_pattern in fh.read():
                    valid_files.append(file.strip(".html"))
        return valid_files

    def update_local_perchance_file(self, name):
        self.delete_local_perchance_file(name)
        requests.get(self.perchance_proxy + name).content.decode("utf-8")
        return (
            f"Updated {name}",
            gr.Dropdown.update(choices=self.get_local_perchance_files()),
        )

    def delete_local_perchance_file(self, name):
        message = ""
        file_path = os.path.join(self.perchance_file_path, name + ".html")
        if os.path.exists(file_path):
            os.remove(file_path)
            message = f"Removed {file_path}"
        else:
            message = f"Could not find {file_path}"
        return (message, gr.Dropdown.update(choices=self.get_local_perchance_files()))

    def delete_local_perchance_files(self):
        html_files = [
            f for f in os.listdir(self.perchance_file_path) if f.endswith(".html")
        ]
        for file in html_files:
            file_path = os.path.join(self.perchance_file_path, file)
            os.remove(file_path)
        return (
            "Local Perchance cache was cleared",
            gr.Dropdown.update(choices=self.get_local_perchance_files()),
        )

    def node_install(self):
        # Not working yet
        print("Checking Node version")
        node = subprocess.run(["node", "-v"], shell=True, cwd=self.perchance_file_path)
        if node.returncode == 1:
            return "Node.js/NPM required"
        print("Installing Node package dependencies")
        npm = subprocess.run(
            ["npm", "install"], shell=True, cwd=self.perchance_file_path
        )
        if npm.returncode == 1:
            return "Install failed."
        self.run_local_perchance_proxy()

    def run_local_perchance_proxy(self):
        """Run local Node.js proxy"""
        proxy_js = self.perchance_file_path.joinpath("perchance_proxy.js")
        print(f"proxy location: {proxy_js}")
        message = ""
        # Check if running,
        try:
            stopped = self.perchance_proxy_instance.poll()
        except:
            stopped = 1
        if stopped:
            self.perchance_proxy_instance = subprocess.Popen(
                f"node {proxy_js}", shell=True
            )
            message = f"Node Running on pid {self.perchance_proxy_instance.pid}"
        else:
            message = "Perchance Proxy already running"
        print(f"proxy returncode: {self.perchance_proxy_instance.poll()}")
        return message


def load_from_cache(selected_name):
    return selected_name


class Script(scripts.Script):
    def __init__(self, *args, **kwargs):
        self.proxy = ProxyManager()
        self.proxy.proxy_init()
        super().__init__(*args, **kwargs)

    def title(self):
        return "Perchance"

    def ui(self, is_img2img):
        with gr.Accordion(label="Instructions", open=False):
            gr.Markdown(
                "You must have Node.js installed to run the Perchance proxy service. Expand Proxy settings and click `Start`. Insert `{perchance}` into prompt text and it will be replaced with perchance output. Enter in name of Perchance generator (last part of URL) Proxy must be running."
            )
        with gr.Accordion("Proxy", open=False) as proxy:
            with gr.Row():
                install_deps = gr.Button("Install Dependencies")
                proxy_start = gr.Button("Start Proxy")
        with gr.Accordion("Cache", open=True) as cache:
            with gr.Row():
                cache_dropdown = gr.Dropdown(
                    self.proxy.get_local_perchance_files(),
                    label="Prompt History",
                    type="value",
                )
            with gr.Row():
                cache_load = gr.Button("Load")
                cache_update = gr.Button("Update")
                cache_delete = gr.Button("Delete")
        generator_name = gr.Textbox(label="Generator Name", elem_id="generator-name")
        output = gr.Textbox(label="Perchance Output", elem_id="perchance-output")
        refresh_on_run = gr.Checkbox(label="Refresh on each run")
        sequential = gr.Checkbox(label="Sequential seeds")
        refresh = gr.Button(value="Refresh")

        status = gr.Textbox(label="Status", interactive=False)
        cache_load.click(
            load_from_cache, inputs=[cache_dropdown], outputs=[generator_name]
        )
        cache_update.click(
            self.proxy.update_local_perchance_file,
            inputs=cache_dropdown,
            outputs=[status, cache_dropdown],
        )
        cache_delete.click(
            self.proxy.delete_local_perchance_file,
            inputs=cache_dropdown,
            outputs=[status, cache_dropdown],
        )
        refresh.click(
            self.proxy.get_perchance,
            inputs=[generator_name],
            outputs=[output, cache_dropdown],
        )
        proxy_start.click(
            self.proxy.run_local_perchance_proxy, inputs=[], outputs=[status]
        )
        install_deps.click(self.proxy.node_install, inputs=[], outputs=[status])

        # TODO install_node
        return [generator_name, output, refresh_on_run, sequential, status]

    def run(
        self,
        p: StableDiffusionProcessing,
        generator_name,
        output,
        refresh_on_run,
        sequential,
        proxy_message: gr.Textbox,
    ):
        original_prompt: str = p.prompt[0] if type(p.prompt) == list else p.prompt
        batch_count = p.n_iter
        initial_seed = None
        initial_info = None
        all_images = []

        if refresh_on_run:
            # Always process one at a time when refresh is enabled
            p.n_iter = 1
            p.batch_size = 1
            state.job_count = batch_count

            for i in range(batch_count):
                if state.interrupted:
                    break
                p.do_not_save_grid = True

                # Get fresh perchance output for each generation
                p.prompt = original_prompt.replace(
                    "{perchance}", self.proxy.get_perchance(generator_name)[0]
                )
                state.job = f"Batch {i + 1}/{batch_count}"
                processed = process_images(p)

                # Capture initial info for the set
                if initial_seed is None:
                    initial_seed = processed.seed
                    initial_info = processed.info

                if sequential:
                    p.seed = processed.seed + 1
                else:
                    p.seed = -1

                all_images.append(processed.images[0])

            # Return the grid only if >1 picture
            if batch_count > 1:
                grid = images.image_grid(all_images)
                if opts.grid_save:
                    images.save_image(
                        grid,
                        p.outpath_grids,
                        "grid",
                        processed.seed,
                        p.prompt,
                        opts.grid_format,
                        info=processed.info,
                        short_filename=not opts.grid_extended_filename,
                        grid=True,
                        p=p,
                    )

                if opts.return_grid:
                    all_images = [grid] + all_images

            processed = Processed(p, all_images, initial_seed, initial_info)
        else:
            # Use cached output when refresh is disabled
            p.prompt = original_prompt.replace("{perchance}", output)
            processed = process_images(p)

        return processed
