# Stable Diffusion Prompt Perchance
An AUTOMATIC1111/Gradio Stable Diffusion script that inserts output from a [perchance.org](https://perchance.org) generator into the prompt.

## How it works
Unfortunately, perchance does not have a public API, so a local node.js API server/proxy is included. You will need to install node.js, then from the UI under the script's Proxy section, you can install dependencies and start the server. This will run a small local node server using Node Express, which will open up an endpoint on `http://localhost:7864` that will listen for `GET /generate?name=[perchance_name]` calls from the script. 

## Installation
1. Go to Extensions > Install from URL > https://github.com/ouoertheo/sd-webui-perchance
2. Install [NodeJS](https://nodejs.org/en/download/package-manager/current)
3. In Stable Diffusion WebUI, select the Perchance script, expand the Proxy section, click install dependencies

## Usage
1. Open Stable Diffusion WebUI
2. Select the Perchance script
3. Expand Proxy > Start Proxy (do this any time SD is restarted)
4. Put in the name of the desired generator into Generator Name.
5. Click Refresh. The generator will now be stored locally and can be loaded in the future from the Cache section.
6. Put in `{perchance}` into the prompt, and it will be replaced with the generated perchance output.
