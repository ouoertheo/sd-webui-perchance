# Stable Diffusion Prompt Perchance
An AUTOMATIC1111/Gradio Stable Diffusion script that inserts output from a [perchance.org](https://perchance.org) generator into the prompt.

## How it works
Unfortunately, perchance does not have a public API, so a local node.js API server/proxy is included. You will need to install node.js, then from the UI under the script's Proxy section, you can install dependencies and start the server. This will run a small local node server using Node Express, which will open up an endpoint on `http://localhost:7864` that will listen for `GET /generate?name=[perchance_name]` calls from the script. 

## Installation
1. Go to Extensions > Install from URL > https://github.com/ouoertheo/sd-webui-perchance
2. Install [NodeJS](https://nodejs.org/en/download/package-manager/current)
3. The default port is `7864`. If you need this to be different, copy `.env.default` in place and rename it to `.env`. Edit the file and set the port `PERCHANCE_PROXY_PORT=your_port_number`

## Usage
1. Open Stable Diffusion WebUI
2. Select the Perchance script
3. Put in the name of the desired generator into Generator Name.
4. Click Refresh. The generator will now be stored locally and can be loaded in the future from the Cache section.
5. Put in `{perchance}` into the prompt, and it will be replaced with the generated perchance output.

## Troubleshooting
* Make sure you have NodeJS installed
* Go to the Proxy section and click Start Proxy
* Make sure nothing else is running on 7862 (this can be changed by going into perchance_proxy.js and settin `port` to the desired port)