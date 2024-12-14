/*
A very simple Node.js server script to provide an API proxy to Perchance
Takes the generator name on https://localhost:7864/generate?name=[perchance-name],
saves the html locally for reuse, then uses JSDOM to return the output of the generator.
*/

const { JSDOM } = require("jsdom"); // v16.4.0
const express = require('express');
const fetch = require("node-fetch");  // v2.6.1
const fs = require("fs");
const path = require("path");

const app = express();
const port = "7864";

// Custom error class for application-specific errors
class PerchanceError extends Error {
    constructor(message, statusCode) {
        super(message);
        this.name = 'PerchanceError';
        this.statusCode = statusCode;
    }
}

async function fetchPerchanceHTML(generatorName) {
    try {
        const response = await fetch(
            `https://perchance.org/api/downloadGenerator?generatorName=${generatorName}&__cacheBust=${Math.random()}`
        );

        if (!response.ok) {
            throw new PerchanceError(
                `Failed to fetch generator: ${response.statusText}`,
                response.status
            );
        }

        const html = await response.text();
        if (html === "Not found.") {
            throw new PerchanceError("Generator not found", 404);
        }

        return html;
    } catch (error) {
        if (error instanceof PerchanceError) {
            throw error;
        }
        throw new PerchanceError(
            `Network error: ${error.message}`,
            503
        );
    }
}

async function getPerchanceOutput(generatorName) {
    // Input validation
    if (!generatorName || typeof generatorName !== 'string') {
        throw new PerchanceError("Generator name is required and must be a string", 400);
    }

    // Sanitize generator name to prevent directory traversal
    const sanitizedName = path.basename(generatorName);
    const filename = path.join(__dirname, sanitizedName + '.html');
    
    let html;
    try {
        // Try to read from cache first
        if (fs.existsSync(filename)) {
            html = fs.readFileSync(filename, 'utf8');
        } else {
            // Fetch and cache if not exists
            html = await fetchPerchanceHTML(sanitizedName);
            fs.writeFileSync(filename, html, 'utf8');
        }

        // Parse HTML and execute scripts
        const { window } = await new JSDOM(html, {
            runScripts: "dangerously",
            resources: "usable"
        });

        // Validate output
        if (!window.root || !window.root.output) {
            throw new PerchanceError("Invalid generator output", 500);
        }

        const output = window.root.output.toString();
        if (!output) {
            throw new PerchanceError("Generator produced empty output", 500);
        }

        return output;
    } catch (error) {
        if (error instanceof PerchanceError) {
            throw error;
        }
        // Handle file system errors
        if (error.code === 'ENOENT' || error.code === 'EACCES') {
            throw new PerchanceError(`File system error: ${error.message}`, 500);
        }
        // Handle JSDOM errors
        if (error.message.includes('JSDOM')) {
            throw new PerchanceError(`Parser error: ${error.message}`, 500);
        }
        // Generic error handler
        throw new PerchanceError(`Internal server error: ${error.message}`, 500);
    }
}

// Request validation middleware
app.use('/generate', (req, res, next) => {
    if (!req.query.name) {
        next(new PerchanceError("Missing required query parameter: name", 400));
        return;
    }
    next();
});

// Main route handler
app.get('/generate', async (req, res, next) => {
    try {
        const output = await getPerchanceOutput(req.query.name);
        res.json({ success: true, output });
    } catch (error) {
        next(error);
    }
});

// Error handling middleware
app.use((error, req, res, next) => {
    const statusCode = error.statusCode || 500;
    const message = error.message || 'Internal Server Error';
    
    console.error(`[${new Date().toISOString()}] Error: ${message}`);
    
    res.status(statusCode).json({
        success: false,
        error: {
            message,
            status: statusCode
        }
    });
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error(`[${new Date().toISOString()}] Uncaught Exception:`, error);
    process.exit(1);
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
    console.error(`[${new Date().toISOString()}] Unhandled Rejection:`, reason);
    process.exit(1);
});

app.listen(port, () => {
    console.log(`Perchance proxy server running on port ${port}`);
});
