from google.cloud import texttospeech_v1beta1
import os
import argparse
import json
from datetime import datetime
from app_config import Config
import io
from pydub import AudioSegment

class PodcastGenerator:
    def __init__(self):
        Config.validate_config()
        
        self.config = {
            "language_code": Config.TTS_LANGUAGE_CODE,
            "voice_name": Config.TTS_VOICE_NAME,
            "speaking_rate": Config.TTS_SPEAKING_RATE,
            "pitch": Config.TTS_PITCH,
            "volume_gain_db": Config.TTS_VOLUME_GAIN_DB,
            "output_directory": Config.TTS_OUTPUT_DIRECTORY,
            "file_format": Config.TTS_FILE_FORMAT
        }
        
        os.makedirs(self.config["output_directory"], exist_ok=True)
        self.client = texttospeech_v1beta1.TextToSpeechClient()

    def create_podcast(self, input_file, output_filename=None):
        """Generate podcast from input transcript file"""
        try:
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input file not found: {input_file}")

            # Read all lines from the file
            with open(input_file, 'r', encoding='utf-8') as file:
                all_lines = [line.strip() for line in file.readlines() if line.strip()]

            # Generate base filename if not provided
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"podcast_{timestamp}"

            # Process in smaller chunks (5 lines per chunk)
            chunk_size = 5
            chunks = [all_lines[i:i + chunk_size] for i in range(0, len(all_lines), chunk_size)]
            chunk_paths = []

            # Generate audio for each chunk
            for i, chunk_lines in enumerate(chunks):
                print(f"Processing chunk {i + 1}/{len(chunks)}")
                
                multi_speaker_markup = texttospeech_v1beta1.MultiSpeakerMarkup()
                for line in chunk_lines:
                    turn = self._process_line(line)
                    if turn:
                        multi_speaker_markup.turns.append(turn)

                if multi_speaker_markup.turns:
                    audio_content = self.generate_audio_chunk(multi_speaker_markup)
                    if audio_content:
                        # Save individual chunk
                        chunk_filename = f"{output_filename}_chunk_{i+1}.wav"
                        chunk_path = os.path.join(self.config["output_directory"], chunk_filename)
                        with open(chunk_path, 'wb') as f:
                            f.write(audio_content)
                        chunk_paths.append(chunk_path)
                        print(f"Generated audio for chunk {i + 1} - Size: {len(audio_content)} bytes")
                        print(f"Saved chunk file: {chunk_filename}")
                    else:
                        print(f"Failed to generate audio for chunk {i + 1}")
                else:
                    print(f"No valid turns in chunk {i + 1}")

            if not chunk_paths:
                raise ValueError("No audio content was generated")

            # Combine chunks using pydub
            print(f"\nCombining {len(chunk_paths)} chunks...")
            combined_filename = f"{output_filename}_combined.wav"
            combined_path = os.path.join(self.config["output_directory"], combined_filename)
            
            # Combine audio files
            combined = AudioSegment.empty()
            for i, chunk_path in enumerate(chunk_paths, 1):
                print(f"Adding chunk {i} to combined audio: {os.path.basename(chunk_path)}")
                audio = AudioSegment.from_wav(chunk_path)
                combined += audio

            # Export combined file
            print(f"Exporting combined file to: {combined_filename}")
            combined.export(combined_path, format="wav")
            
            # Verify file sizes
            print("\nFile size verification:")
            total_chunk_size = 0
            for i, path in enumerate(chunk_paths, 1):
                chunk_size = os.path.getsize(path)
                total_chunk_size += chunk_size
                print(f"Chunk {i}: {chunk_size} bytes")
            
            final_size = os.path.getsize(combined_path)
            print(f"Total chunks size: {total_chunk_size} bytes")
            print(f"Combined file size: {final_size} bytes")
            print(f"Combined file path: {combined_path}")

            return combined_path

        except Exception as e:
            print(f"Error during podcast generation: {str(e)}")
            raise

    def _process_line(self, line):
        if not line or line.startswith("(") or line.startswith("["):
            return None

        if ': ' in line:
            speaker, text = line.split(': ', 1)
            turn = texttospeech_v1beta1.MultiSpeakerMarkup.Turn()
            
            if speaker.lower() == Config.SPEAKER_1_NAME.lower():
                turn.speaker = Config.SPEAKER_1_VOICE
                turn.text = text.strip()
                print(f"Processed {Config.SPEAKER_1_NAME}'s line: {text[:50]}...")
            elif speaker.lower() == Config.SPEAKER_2_NAME.lower():
                turn.speaker = Config.SPEAKER_2_VOICE
                turn.text = text.strip()
                print(f"Processed {Config.SPEAKER_2_NAME}'s line: {text[:50]}...")
            else:
                print(f"Unknown speaker: {speaker}")
                return None
            
            return turn
        return None

    def generate_audio_chunk(self, multi_speaker_markup):
        """Generate audio for a chunk of conversation"""
        try:
            synthesis_input = texttospeech_v1beta1.SynthesisInput(
                multi_speaker_markup=multi_speaker_markup
            )

            voice = texttospeech_v1beta1.VoiceSelectionParams(
                language_code=self.config["language_code"],
                name=self.config["voice_name"]
            )

            audio_config = texttospeech_v1beta1.AudioConfig(
                audio_encoding=texttospeech_v1beta1.AudioEncoding.LINEAR16,
                speaking_rate=self.config["speaking_rate"],
                pitch=self.config["pitch"],
                volume_gain_db=self.config["volume_gain_db"]
            )

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            if not response.audio_content:
                print("No audio content in response")
                return None

            return response.audio_content

        except Exception as e:
            print(f"Error generating audio chunk: {str(e)}")
            return None

    def _find_mp3_start(self, data):
        if data.startswith(b'ID3'):
            size = ((data[6] & 0x7f) << 21) | ((data[7] & 0x7f) << 14) | \
                   ((data[8] & 0x7f) << 7) | (data[9] & 0x7f)
            start = 10 + size
        else:
            start = 0

        for i in range(start, len(data) - 1):
            if data[i] == 0xFF and data[i+1] & 0xE0 == 0xE0:
                return i

        return -1

def main():
    parser = argparse.ArgumentParser(description='Generate podcast from transcript')
    parser.add_argument('input_file', help='Path to input transcript file')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output', help='Output filename')
    args = parser.parse_args()

    generator = PodcastGenerator()
    output_path = generator.create_podcast(args.input_file, args.output)
    print(f"Podcast saved as: {output_path}")

if __name__ == "__main__":
    main()
