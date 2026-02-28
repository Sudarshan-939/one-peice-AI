const jsdom = require("jsdom");
const fs = require("fs");
const { JSDOM } = jsdom;

const html = fs.readFileSync("index.html", "utf-8");
const dom = new JSDOM(html, { runScripts: "dangerously", resources: "usable" });

dom.window.addEventListener('load', () => {
    try {
        const window = dom.window;
        const document = window.document;

        // Evaluate the script manually because external scripts might not load synchronously
        const scriptContent = fs.readFileSync("script.js", "utf-8");
        window.eval(scriptContent);

        const form = document.getElementById('chat-form');
        const messageInput = document.getElementById('message-input');

        messageInput.value = "Hello World";
        // Simulate enter key press
        const event = new window.KeyboardEvent('keydown', { key: 'Enter', shiftKey: false });
        messageInput.dispatchEvent(event);

        console.log("Chat messages after submit:", document.getElementById('chat-messages').innerHTML);
    } catch (e) {
        console.error("Error evaluating:", e);
    }
});
