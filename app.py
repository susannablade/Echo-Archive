import os
import random
import re
import requests
import streamlit as st
import google.generativeai as genai  # Updated import
import resend

# ---------------------------
# CONFIG
# ---------------------------
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
RESEND_KEY = os.environ.get("RESEND_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
else:
    st.error("Gemini API Key missing! Check HF Secrets.")

if RESEND_KEY:
    resend.api_key = RESEND_KEY

ARTIC_API_URL = "https://api.artic.edu/api/v1/artworks"

session = requests.Session()

# ---------------------------
# SESSION STATE
# ---------------------------
DEFAULT_STATE = {
    "artwork": None,
    "description": "",
    "interpretation": "",
    "reflection_text": "",
    "user_input": "",
    "show_email_input": False
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value

# ---------------------------
# HELPERS
# ---------------------------
def build_image_url(image_id):

    return (
        f"https://www.artic.edu/iiif/2/"
        f"{image_id}/full/843,/0/default.jpg"
    )


def valid_email(email):

    pattern = r"^[^@]+@[^@]+\.[^@]+$"

    return re.match(pattern, email)


def ask_gemini(prompt):

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if (
            response
            and hasattr(response, "text")
            and response.text
        ):

            return response.text.strip()

    except Exception as e:

        print(f"Gemini error: {e}")

    return "The archive remains quiet."


# ---------------------------
# ARTWORK RETRIEVAL
# ---------------------------
def get_random_artwork(retries=5):

    for _ in range(retries):

        random_page = random.randint(1, 500)

        try:

            response = session.get(
                ARTIC_API_URL,
                params={
                    "page": random_page,
                    "limit": 25,
                    "fields": (
                        "id,title,image_id,artist_title,"
                        "artist_display,date_display,"
                        "medium_display,dimensions,"
                        "description,classification_title,"
                        "style_title,theme_titles,"
                        "provenance_text,exhibition_history"
                    )
                },
                timeout=10
            )

            response.raise_for_status()

            data = response.json().get(
                "data",
                []
            )

        except Exception as e:

            print(f"ARTIC API error: {e}")

            continue

        artworks = []

        for obj in data:

            image_id = obj.get("image_id")

            if not image_id:
                continue

            has_context = any([
                obj.get("description"),
                obj.get("provenance_text"),
                obj.get("artist_display"),
                obj.get("exhibition_history")
            ])

            if not has_context:
                continue

            artworks.append({
                "id": obj.get("id"),
                "title": obj.get("title") or "Untitled",
                "artist": (
                    obj.get("artist_title")
                    or "Unknown Artist"
                ),
                "artist_display": (
                    obj.get("artist_display")
                    or ""
                ),
                "date": (
                    obj.get("date_display")
                    or "Unknown Date"
                ),
                "medium": (
                    obj.get("medium_display")
                    or "Unknown Medium"
                ),
                "dimensions": (
                    obj.get("dimensions")
                    or ""
                ),
                "description": (
                    obj.get("description")
                    or ""
                ),
                "classification": (
                    obj.get("classification_title")
                    or ""
                ),
                "style": (
                    obj.get("style_title")
                    or ""
                ),
                "themes": (
                    obj.get("theme_titles")
                    or []
                ),
                "provenance": (
                    obj.get("provenance_text")
                    or ""
                ),
                "exhibition_history": (
                    obj.get("exhibition_history")
                    or ""
                ),
                "image": build_image_url(
                    image_id
                )
            })

        if artworks:

            return random.choice(
                artworks
            )

    return None


# ---------------------------
# DESCRIPTION
# ---------------------------
def generate_description(artwork):

    prompt = f"""
    You are writing a curatorial description
    for a museum visitor.

    Help the user emotionally and historically
    connect to the artwork.

    Artwork Information:

    Title: {artwork['title']}
    Artist: {artwork['artist']}
    Artist Bio: {artwork['artist_display']}
    Date: {artwork['date']}
    Medium: {artwork['medium']}
    Classification: {artwork['classification']}
    Style: {artwork['style']}

    Themes:
    {
        ', '.join(artwork['themes'])
        if artwork['themes']
        else 'None listed'
    }

    Museum Description:
    {artwork['description']}

    Provenance:
    {artwork['provenance']}

    Exhibition History:
    {artwork['exhibition_history']}

    Write a rich atmospheric description
    in 4-5 sentences.

    Guidelines:
    - Treat the artwork as emotionally alive
    - Connect material, history, and mood
    - Avoid academic stiffness
    - Be restrained and literary

    Output only the description.
    """

    return ask_gemini(prompt)


# ---------------------------
# INTERPRETATION
# ---------------------------
def generate_interpretation(
    user_input,
    artwork,
    description
):

    prompt = f"""
    A user shared this thought:

    "{user_input}"

    Artwork:
    {artwork['title']}
    by {artwork['artist']}

    Curatorial Description:
    "{description}"

    Write a reflective interpretation
    in 5-6 sentences.

    Guidelines:
    - Avoid generic spiritual language
    - Be emotionally observant
    - Do not summarize literally
    - Sound thoughtful and restrained

    Output only the interpretation.
    """

    return ask_gemini(prompt)


# ---------------------------
# USER REFLECTION
# ---------------------------
def generate_user_reflection(
    user_input,
    artwork,
    interpretation
):

    prompt = f"""
    Help the user write a personal reflection
    inspired by this artwork encounter.

    User Thought:
    "{user_input}"

    Artwork:
    {artwork['title']}
    by {artwork['artist']}

    Interpretation:
    "{interpretation}"

    Write a short first-person reflection.

    Guidelines:
    - Sound intimate and grounded
    - Write like a journal entry
    - Avoid sounding mystical
    - Keep emotional specificity

    Output only the reflection.
    """

    return ask_gemini(prompt)


# ---------------------------
# EMAIL
# ---------------------------
def send_archive_email(
    recipient_email,
    artwork,
    description,
    interpretation,
    reflection
):

    subject = (
        f"Echo Archive — "
        f"{artwork['title']}"
    )

    html_body = f"""
    <h2>Echo Archive — Reflection Record</h2>

    <h3>Artwork</h3>

    <p>
    <strong>{artwork['title']}</strong><br>
    {artwork['artist']}<br>
    {artwork['date']}<br>
    {artwork['medium']}
    </p>

    <h3>Curatorial Description</h3>
    <p>{description}</p>

    <h3>Interpretation</h3>
    <p>{interpretation}</p>

    <h3>Personal Reflection</h3>
    <p>{reflection}</p>

    <h3>Artwork Image</h3>

    <p>
    <a href="{artwork['image']}">
    View Artwork
    </a>
    </p>
    """

    try:

        resend.Emails.send({
            "from": (
                "Echo Archive "
                "<onboarding@resend.dev>"
            ),
            "to": recipient_email,
            "subject": subject,
            "html": html_body
        })

        return True

    except Exception as e:

        print(f"Email error: {e}")

        return False


# ---------------------------
# UI
# ---------------------------
st.title("Echo Archive")

st.write(
    "A quiet experiment in reflection. "
    "An artwork is drawn from the archive "
    "of the Art Institute of Chicago."
)

# ---------------------------
# INPUT FORM
# ---------------------------
with st.form("archive_form"):

    user_input = st.text_area(
        "What is circling your mind right now?",
        placeholder=(
            "A thought, concept, memory or feeling..."
        ),
        height=80
    )

    submitted = st.form_submit_button(
        "Draw from the archive"
    )

# ---------------------------
# SUBMISSION
# ---------------------------
if submitted:

    if not user_input.strip():

        st.warning(
            "Please enter a thought first."
        )

        st.stop()

    st.session_state.user_input = (
        user_input
    )

    st.session_state.description = ""
    st.session_state.interpretation = ""
    st.session_state.reflection_text = ""
    st.session_state.show_email_input = False

    with st.spinner(
        "Searching the archive..."
    ):

        artwork = get_random_artwork()

    if artwork is None:

        st.error(
            "The archive returned nothing."
        )

        st.stop()

    st.session_state.artwork = artwork

# ---------------------------
# DISPLAY
# ---------------------------
if st.session_state.artwork:

    art = st.session_state.artwork

    st.image(
        art["image"],
        use_container_width=True
    )

    st.markdown(
        f"### {art['title']}"
    )

    st.caption(
        f"{art['artist']} · {art['date']}"
    )

    st.caption(
        art["medium"]
    )

    # ---------------------------
    # DESCRIPTION
    # ---------------------------
    if not st.session_state.description:

        with st.spinner(
            "The archive gathers its thoughts..."
        ):

            st.session_state.description = (
                generate_description(art)
            )

    with st.expander(
        "About this work",
        expanded=True
    ):

        st.write(
            st.session_state.description
        )

        if art["provenance"]:

            st.markdown(
                "#### Provenance"
            )

            st.write(
                art["provenance"]
            )

    st.divider()

    # ---------------------------
    # INTERPRET BUTTON
    # ---------------------------
    interpret = st.button(
        "Reflect on this artwork"
    )

    if (
        interpret
        and not st.session_state.interpretation
    ):

        with st.spinner(
            "Listening closely..."
        ):

            st.session_state.interpretation = (
                generate_interpretation(
                    st.session_state.user_input,
                    art,
                    st.session_state.description
                )
            )

    # ---------------------------
    # DISPLAY INTERPRETATION
    # ---------------------------
    if st.session_state.interpretation:

        st.markdown(
            "### Reflection"
        )

        st.write(
            st.session_state.interpretation
        )

    st.divider()

    # ---------------------------
    # USER REFLECTION
    # ---------------------------
    st.markdown(
        "### Your Reflection"
    )

    reflection_text = st.text_area(
        "Write your response to this encounter.",
        value=(
            st.session_state.reflection_text
        ),
        height=140,
        placeholder=(
            "What does this artwork leave behind?"
        )
    )

    st.session_state.reflection_text = (
        reflection_text
    )

    # ---------------------------
    # AI ASSIST BUTTON
    # ---------------------------
    assist = st.button(
        "Help me articulate this"
    )

    if assist:

        with st.spinner(
            "Finding the language..."
        ):

            st.session_state.reflection_text = (
                generate_user_reflection(
                    st.session_state.user_input,
                    art,
                    st.session_state.interpretation
                )
            )

        st.rerun()

    st.divider()

    # ---------------------------
    # EMAIL ARCHIVE
    # ---------------------------
    archive = st.button(
        "Send me an email to archive this reflection"
    )

    if archive:

        st.session_state.show_email_input = True

    if st.session_state.show_email_input:

        email_input = st.text_input(
            "Enter your email address"
        )

        send = st.button(
            "Archive Reflection"
        )

        if send:

            if not valid_email(
                email_input
            ):

                st.warning(
                    "Please enter a valid email."
                )

            else:

                with st.spinner(
                    "Archiving reflection..."
                ):

                    success = send_archive_email(
                        recipient_email=email_input,
                        artwork=art,
                        description=(
                            st.session_state.description
                        ),
                        interpretation=(
                            st.session_state.interpretation
                        ),
                        reflection=(
                            st.session_state.reflection_text
                        )
                    )

                if success:

                    st.success(
                        "Your reflection has been archived."
                    )

                else:

                    st.error(
                        "Unable to send email."
                    )