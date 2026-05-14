---
title: Echo Archive
emoji: 🎨
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
target_port: 8501
---

# Echo Archive

Echo Archive is an AI-powered reflective archive designed to help users connect with artwork they may have never explored before.

For many people, artwork can feel historically distant, emotionally inaccessible, or difficult to interpret without formal artistic knowledge. Traditional digital museum experiences often prioritize metadata, search, and categorization, but rarely help users build a personal connection to the work itself.

Echo Archive addresses this problem by combining archival retrieval with generative AI interpretation.

# System Architecture

```text id="e04x6v"
User Reflection Input
        ↓
[Art Institute of Chicago API]
        ↓
Artwork Retrieval + Metadata Filtering
        ↓
Streamlit Artwork Display
        ↓
[Gemini 2.5 Flash]
Curatorial Description
        ↓
[Gemini 2.5 Flash]
Reflective Interpretation
        ↓
User or Gemini-Assisted Reflection
        ↓
Email Archival System
```

# Key Design Decisions

### Retrieval Before Generation

Artwork retrieval is grounded in real museum records and filtered for richer historical metadata.

### Layered Interpretation

The system separates:

* artwork retrieval
* curatorial description
* interpretation
* personal reflection

to create a paced reflective experience.

### Human + AI Co-Authorship

Users can either write their own reflections or use Gemini-assisted drafting.

# Tech Stack

* Streamlit
* Python
* Google Gemini 2.5 Flash
* Art Institute of Chicago API
* Resend Email API
* dotenv


## Core Features

* Randomized artwork retrieval with historical metadata filtering
* AI-generated curatorial descriptions
* Reflective interpretation pipeline
* User-authored or Gemini-assisted reflections
* Email archiving of encounters and reflections

## Run Locally

```bash id="v9m65e"
pip install -r requirements.txt
streamlit run app.py
```

Create a `.env` file with:

```env id="f3hkgm"
GEMINI_API_KEY=your_key_here
RESEND_API_KEY=your_key_here
```

