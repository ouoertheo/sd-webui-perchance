# Stable Diffusion Prompt Perchance
An AUTOMATIC1111/Gradio Stable Diffusion script that inserts output from a [perchance.org](https://perchance.org) generator into the prompt.

## How it works
Unfortunately, perchance does not have a public API, so a local node.js API server/proxy is included. You will need to install node.js, then from the UI under the script's Proxy section, you can install dependencies and start the server. This will run a small local node server using Node Express, which will open up an endpoint on `http://localhost:7864` that will listen for `GET /generate?name=[perchance_name]` calls from the script. 

## Installation
Go to Extensions > Install from URL > https://github.com/ouoertheo/sd-webui-perchance

Install [NodeJS](https://nodejs.org/en/download/package-manager/current)

## Usage
In Stable Diffusion WebUI, select the Perchance script, expand the Proxy section, click install dependencies, start the server (only have to do this once), put in the name of the desired generator then click Refresh. Put in `{perchance}` into the prompt, and it will be replaced with the generated perchance output.
