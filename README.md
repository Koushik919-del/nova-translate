# Nova Translate

A browser-based translation app with four tools: text translation, text reading from images, pronunciation practice, and website translation.

The project uses plain HTML, CSS, and JavaScript and is ready to import into Vercel. No build command or environment variables are required.

## Deploy on Vercel

1. Import this GitHub repository in Vercel.
2. Choose the **Other** framework preset.
3. Leave the build and output settings empty.
4. Deploy.

Vercel serves `index.html` from the repository root.

## How the tools work

- Text translation and image text translation use the MyMemory translation service.
- Image text is read in the browser with Tesseract.js.
- Pronunciation practice uses your browser's speech recognition. Microphone access and browser support are required.
- Website translation opens Google Translate in a new tab.
- Read-aloud uses the browser's built-in speech synthesis.

The browser calls these public services directly. Their availability, quotas, and language support can change independently of this repository.
