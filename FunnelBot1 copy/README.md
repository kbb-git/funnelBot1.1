# FunnelBot - Sales Funneling Assessment Chatbot

FunnelBot is a web application designed to help assess the effectiveness of sales funneling techniques employed by sales representatives during client calls.

## Overview

Users can paste a transcript of a sales call into the application. FunnelBot then utilizes a Large Language Model (LLM), specifically Gemini 2.5, via its API to analyze the transcript based on predefined criteria for sales funneling. The application provides a rating and a qualitative assessment of how well the funneling technique was applied.

## Features (Planned)

-   **Transcript Input:** A simple interface to paste call transcripts.
-   **AI-Powered Analysis:** Leverages the Gemini 2.5 API for in-depth analysis of the transcript.
-   **Funneling Assessment:** Evaluates the transcript against specific criteria related to sales funneling stages (e.g., awareness, interest, consideration, decision).
-   **Scoring/Rating:** Provides a quantitative score or rating based on the analysis.
-   **Qualitative Feedback:** Offers textual feedback on strengths and areas for improvement in the funneling technique observed.

## Technology Stack (Planned)

-   **Backend:** Python (Flask)
-   **Frontend:** HTML, CSS, JavaScript
-   **LLM:** Google Gemini 2.5 Pro (via API)

## Project Structure

```
/FunnelBot1
  /static
    /css
      style.css
    /js
      script.js
  /templates
    index.html
  app.py
  requirements.txt
  README.md
```

## Setup and Running (To be detailed later)

Instructions for setting up the environment, installing dependencies, and running the application will be added here once the initial development is complete. This will include:
- Setting up a Python virtual environment.
- Installing packages from `requirements.txt`.
- Configuring API keys for the Gemini API.
- Running the Flask development server. 