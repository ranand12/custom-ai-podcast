import streamlit as st
from app_generic import PodcastGenerator
import os
import base64
from google.cloud import aiplatform
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import requests
from urllib.parse import urlparse
from newspaper import Article
import PyPDF2
from app_config import Config
import json
from pathlib import Path

def setup_vertex():
    """Initialize Vertex AI"""
    try:
        vertexai.init(
            project=Config.VERTEX_PROJECT,
            location=Config.VERTEX_LOCATION
        )
        model = GenerativeModel(Config.VERTEX_MODEL)
        return model
    except Exception as e:
        st.error(f"Error initializing Vertex AI: {str(e)}")
        return None

def enhance_transcript(model, transcript_text):
    """Enhance the transcript using Vertex AI"""
    prompt = """
Create a natural, engaging podcast conversation between two hosts - discussing the content from [INSERT URL]. The conversation should include:
HOSTS' PERSONALITIES:

{Config.SPEAKER_1_NAME}: {Config.SPEAKER_1_PERSONALITY}
{Config.SPEAKER_2_NAME}: {Config.SPEAKER_2_PERSONALITY}

CONVERSATION STRUCTURE:

Opening banter ({Config.OPENING_WORDS_MIN}-{Config.OPENING_WORDS_MAX} words)
- High-energy greeting
- Excited sharing of their day
- Enthusiastic pivot to topic

Main Discussion ({Config.MAIN_DISCUSSION_MIN}-{Config.MAIN_DISCUSSION_MAX} words)
- Dynamic back-and-forth exploration of points
- Lots of "Yes, and!" moments
- Excited interruptions to add details
- Both hosts building on each other's enthusiasm
- Quick-paced but clear delivery
- Shared excitement over discoveries
- Playful banter throughout

NATURAL SPEECH ELEMENTS:
- "!" for shared excitement
- "!!" for extra enthusiasm
- "Oh wow!" for amazement
- "Yes!" for strong agreement
- "Haha " for energetic laughter
- "Right?!" for enthusiastic confirmation
- "I know!!" for excited agreement

Example:
{Config.SPEAKER_1_NAME}: Oh my gosh! Jamie, you're going to LOVE this!!
Jamie: Yes! Is this about that amazing thing you mentioned?!
{Config.SPEAKER_1_NAME}: It totally is! And it's even better than I thought!!
Jamie: No way! Tell me everything!!
{Config.SPEAKER_1_NAME}: Okay, okay! So you know how... [excited explanation]
Jamie: That's incredible! And you know what else this reminds me of?!

CONVERSATION ELEMENTS:
- High-energy exchanges
- Enthusiastic building on each other's points
- Excited sharing of insights
- Quick, energetic pace
- Shared moments of discovery
- Playful, positive dynamics
- Mutual enthusiasm for details

STYLE GUIDELINES:

Keep everything in plain text
No special characters or markup
Use regular punctuation for emphasis
Write out all sounds phonetically
Use regular quotation marks when needed

The final conversation should sound like two friends genuinely excited to share interesting information with their audience. Embrace the natural messiness of real conversation while maintaining engaging content delivery.

{transcript}

Provide only the enhanced transcript with no additional text or formatting.
    """.format(transcript=transcript_text, Config=Config)

    try:
        response = model.generate_content(prompt)
        # Clean up any potential formatting
        enhanced_text = response.text.strip()
        # Remove any markdown or special characters
        enhanced_text = enhanced_text.replace('*', '').replace('#', '').replace('`', '')
        # Remove any blank lines
        enhanced_text = '\n'.join(line for line in enhanced_text.split('\n') if line.strip())
        return enhanced_text
    except Exception as e:
        st.error(f"Error enhancing transcript: {str(e)}")
        return transcript_text

def get_audio_player_html(audio_path):
    """Generate HTML code for a custom audio player"""
    audio_placeholder = f"""
        <audio controls style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_path}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
    """
    return audio_placeholder

def extract_url_content(url):
    """Extract raw content from URL using newspaper3k"""
    try:
        # Create Article object
        article = Article(url)
        
        # Download and parse article
        article.download()
        article.parse()
        
        # Get the main text content
        content = article.text.strip()
        
        if not content:
            raise Exception("No content extracted from the article")
            
        return content
    except Exception as e:
        st.error(f"Error extracting content from URL: {str(e)}")
        return None

def extract_pdf_content(pdf_file):
    """Extract text content from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        if not text.strip():
            raise Exception("No content extracted from PDF")
            
        return text.strip()
    except Exception as e:
        st.error(f"Error extracting content from PDF: {str(e)}")
        return None

def is_valid_url(url):
    """Check if the URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def increment_visitor_count():
    """Increment and return the visitor count"""
    counter_file = Path("visitor_counter.json")
    
    try:
        if counter_file.exists():
            with open(counter_file, "r") as f:
                data = json.load(f)
                count = data.get("visitors", 0) + 1
        else:
            count = 1
            
        with open(counter_file, "w") as f:
            json.dump({"visitors": count}, f)
            
        return count
    except Exception as e:
        st.error(f"Error tracking visitors: {str(e)}")
        return 0

def main():
    # Initialize session state
    if 'enhanced_transcript' not in st.session_state:
        st.session_state.enhanced_transcript = None
    if 'raw_content' not in st.session_state:
        st.session_state.raw_content = None

    # Initialize Vertex AI
    model = setup_vertex()
    if model is None:
        st.error("Failed to initialize Vertex AI. Please check your credentials.")
        return

    st.set_page_config(
        page_title="Podcast Generator",
        page_icon="🎙️",
        layout="centered"
    )

    visitor_count = increment_visitor_count()
    st.markdown(
        f"""
        <div style='position: fixed; 
                    bottom: 10px; 
                    left: 50%; 
                    transform: translateX(-50%);
                    text-align: center; 
                    color: gray; 
                    font-size: 14px;'>
            👥 Visitors: {visitor_count}
        </div>
        """, 
        unsafe_allow_html=True
    )

    st.title("🎙️ AI Podcast Generator")
    st.write("Transform your text or web content into natural-sounding podcasts")

    # Add input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Upload File", "Enter URL"],
        horizontal=True
    )

    if input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload your document",
            type=['txt', 'pdf'],
            help="Supported formats: TXT, PDF",
            key='file_uploader'
        )
        
        if uploaded_file is not None:
            if uploaded_file.type == "application/pdf":
                current_content = extract_pdf_content(uploaded_file)
            else:  # txt file
                current_content = uploaded_file.getvalue().decode()
            
            if current_content:
                st.session_state.raw_content = current_content
                
                if st.session_state.enhanced_transcript is None:
                    with st.spinner("Enhancing content with AI..."):
                        st.session_state.enhanced_transcript = enhance_transcript(model, current_content)

    else:  # URL input
        url = st.text_input("Enter URL:", placeholder="https://example.com/article")
        
        if url and is_valid_url(url):
            if st.session_state.get('last_url') != url:
                # First, get the raw content using newspaper3k
                with st.spinner("Extracting content from URL..."):
                    raw_content = extract_url_content(url)
                    if raw_content:
                        st.session_state.raw_content = raw_content
                        # Then enhance it
                        with st.spinner("Enhancing content with AI..."):
                            st.session_state.enhanced_transcript = enhance_transcript(model, raw_content)
                            st.session_state.last_url = url
                    else:
                        st.error("Failed to extract content from the URL")
        elif url:
            st.error("Please enter a valid URL")

    # Show content in tabs if available
    if st.session_state.get('raw_content') and input_method == "Enter URL":
        tab1, tab2 = st.tabs(["Enhanced Transcript", "Raw Article"])
        
        with tab1:
            st.write("### Edit Enhanced Transcript")
            st.write("Make any necessary adjustments to the AI-enhanced transcript below:")
            edited_text = st.text_area(
                "",
                value=st.session_state.enhanced_transcript,
                height=400,
                key="transcript_editor"
            )
            st.session_state.enhanced_transcript = edited_text

        with tab2:
            st.write("### Raw Article Content")
            st.write("Original content extracted from the URL:")
            st.text_area(
                "",
                value=st.session_state.raw_content,
                height=400,
                key="raw_content_viewer",
                disabled=True
            )

    # For file uploads, show only the enhanced transcript
    elif st.session_state.get('enhanced_transcript') and input_method == "Upload File":
        st.write("### Edit Enhanced Transcript")
        st.write("Make any necessary adjustments to the AI-enhanced transcript below:")
        edited_text = st.text_area(
            "",
            value=st.session_state.enhanced_transcript,
            height=400,
            key="transcript_editor"
        )
        st.session_state.enhanced_transcript = edited_text

    # Generate button (outside tabs)
    if st.button("Generate Podcast 🎯", type="primary"):
        temp_path = os.path.join("temp", "transcript.txt")
        os.makedirs("temp", exist_ok=True)
        
        with open(temp_path, "w", encoding='utf-8') as f:
            f.write(st.session_state.enhanced_transcript)

        with st.spinner("Generating your podcast..."):
            try:
                generator = PodcastGenerator()
                output_path = generator.create_podcast(temp_path)
                
                # Read the audio file and create player
                with open(output_path, "rb") as f:
                    audio_bytes = f.read()
                    audio_base64 = base64.b64encode(audio_bytes).decode()
                    
                    st.success("🎉 Podcast generated successfully!")
                    
                    # Display audio player
                    st.write("### Listen to your podcast")
                    st.markdown(get_audio_player_html(audio_base64), unsafe_allow_html=True)
                    
                    # Download buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="Download Podcast 📥",
                            data=audio_bytes,
                            file_name=os.path.basename(output_path),
                            mime="audio/mp3"
                        )
                    with col2:
                        # Add option to download the transcript
                        transcript_to_download = st.session_state.enhanced_transcript
                        
                        st.download_button(
                            label="Download Transcript 📝",
                            data=transcript_to_download,
                            file_name="transcript.txt",
                            mime="text/plain"
                        )
            except Exception as e:
                st.error(f"Error generating podcast: {str(e)}")
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)

if __name__ == "__main__":
    main() 