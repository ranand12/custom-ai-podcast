from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration class
class Config:
    # Google Cloud settings
    VERTEX_PROJECT = os.getenv('VERTEX_PROJECT')
    VERTEX_LOCATION = os.getenv('VERTEX_LOCATION', 'us-central1')
    VERTEX_MODEL = os.getenv('VERTEX_MODEL', 'gemini-1.5-pro-002')

    # Text-to-Speech settings
    TTS_LANGUAGE_CODE = os.getenv('TTS_LANGUAGE_CODE', 'en-US')
    TTS_VOICE_NAME = os.getenv('TTS_VOICE_NAME', 'en-US-Studio-MultiSpeaker')
    TTS_SPEAKING_RATE = float(os.getenv('TTS_SPEAKING_RATE', '1.1'))
    TTS_PITCH = float(os.getenv('TTS_PITCH', '0.5'))
    TTS_VOLUME_GAIN_DB = float(os.getenv('TTS_VOLUME_GAIN_DB', '2.0'))
    TTS_HOST_SPEAKER = os.getenv('TTS_HOST_SPEAKER', 'S')
    TTS_GUEST_SPEAKER = os.getenv('TTS_GUEST_SPEAKER', 'R')
    TTS_OUTPUT_DIRECTORY = os.getenv('TTS_OUTPUT_DIRECTORY', 'output')
    TTS_FILE_FORMAT = os.getenv('TTS_FILE_FORMAT', 'wav')

    # Speaker Names and Personalities
    SPEAKER_1_NAME = os.getenv('SPEAKER_1_NAME', 'Alex')
    SPEAKER_2_NAME = os.getenv('SPEAKER_2_NAME', 'Emma')
    SPEAKER_1_PERSONALITY = os.getenv('SPEAKER_1_PERSONALITY', 
        'Super enthusiastic, loves diving deep into details, uses lots of exclamation points, rapid-fire energy')
    SPEAKER_2_PERSONALITY = os.getenv('SPEAKER_2_PERSONALITY', 
        'Equally excited but channels it through lots of questions and "aha!" moments, loves building on points')

    # Vertex AI settings
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
    MAX_OUTPUT_TOKENS = int(os.getenv('MAX_OUTPUT_TOKENS', '2048'))
    TOP_K = int(os.getenv('TOP_K', '40'))
    TOP_P = float(os.getenv('TOP_P', '0.8'))

    # Speaker Configuration
    SPEAKER_1_VOICE = os.getenv('SPEAKER_1_VOICE', 'S')
    SPEAKER_2_VOICE = os.getenv('SPEAKER_2_VOICE', 'R')

    # Conversation Structure
    OPENING_WORDS_MIN = int(os.getenv('OPENING_WORDS_MIN', '30'))
    OPENING_WORDS_MAX = int(os.getenv('OPENING_WORDS_MAX', '45'))
    MAIN_DISCUSSION_MIN = int(os.getenv('MAIN_DISCUSSION_MIN', '400'))
    MAIN_DISCUSSION_MAX = int(os.getenv('MAIN_DISCUSSION_MAX', '700'))

    # Speech Elements
    PAUSE_MARKER = os.getenv('PAUSE_MARKER', '...')
    EXCITEMENT_MARKER = os.getenv('EXCITEMENT_MARKER', '!')
    QUESTION_MARKER = os.getenv('QUESTION_MARKER', '?')
    THINKING_SOUND = os.getenv('THINKING_SOUND', 'Hmm')
    AGREEMENT_SOUND = os.getenv('AGREEMENT_SOUND', 'Mm')
    LAUGHTER_SOUND = os.getenv('LAUGHTER_SOUND', 'hehe')

    @classmethod
    def validate_config(cls):
        """Validate that all required configuration values are present"""
        required_vars = [
            'VERTEX_PROJECT',
            'VERTEX_LOCATION',
            'VERTEX_MODEL',
            'SPEAKER_1_NAME',
            'SPEAKER_2_NAME',
            'SPEAKER_1_VOICE',
            'SPEAKER_2_VOICE',
            'SPEAKER_1_PERSONALITY',
            'SPEAKER_2_PERSONALITY',
            'OPENING_WORDS_MIN',
            'OPENING_WORDS_MAX',
            'MAIN_DISCUSSION_MIN',
            'MAIN_DISCUSSION_MAX',
            'PAUSE_MARKER',
            'EXCITEMENT_MARKER',
            'QUESTION_MARKER',
            'THINKING_SOUND',
            'AGREEMENT_SOUND',
            'LAUGHTER_SOUND',
            'TTS_LANGUAGE_CODE',
            'TTS_VOICE_NAME',
            'TTS_SPEAKING_RATE',
            'TTS_PITCH',
            'TTS_VOLUME_GAIN_DB',
            'TTS_OUTPUT_DIRECTORY',
            'TTS_FILE_FORMAT'
        ]
        
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")