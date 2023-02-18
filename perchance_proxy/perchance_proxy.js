/*
A very simple Node.js server script to provide an API proxy to Perchance
Takes the generator name on https://localhost:7864/generate?name=[perchance-name],
saves the html locally for reuse, then uses JSDOM to return the output of the generator.
*/

const { JSDOM } = require("jsdom"); // v16.4.0
const express = require('express')
const fetch = require("node-fetch");  // v2.6.1
const fs = require("fs");
const { nextTick } = require("process");

const app = express();
const port = "7864"
const path = "./scripts/perchance_proxy/"

async function fetchPerchanceHTML(generatorName, callback){
    html = await fetch(`https://perchance.org/api/downloadGenerator?generatorName=${generatorName}&__cacheBust=${Math.random()}`).then(r => r.text());
    let err
    if (html == "Not found."){
        err = new Error("Invalid generator name")
    } 
    callback(err, html)
}

async function getPerchanceOutput(generatorName, callback){
    // let generatorName = "animal-sentence";
    let filename = path+generatorName+'.html'
    let html
    let outer_err
    let output = ""
    if (fs.existsSync(filename)) {
        html = fs.readFileSync(filename)
    } else {
        await fetchPerchanceHTML(generatorName, (err, data) => {
            if (err) {
                outer_err = err
            } else {
                html = data
                fs.writeFileSync(filename,html)
            }
        })
    }
    if (!outer_err){
        const { window } = await new JSDOM(html, {runScripts: "dangerously"});
        output = window.root.output.toString()
    }
    callback(outer_err, output)
}

app.get('/generate', async (req, res, next) =>  {
    generatorName = req.query.name
    await getPerchanceOutput(generatorName, (err, data) => {
        if (err){
            next(err)
        } else {
            res.send(data); 
        }
    })
})

app.listen(port);

