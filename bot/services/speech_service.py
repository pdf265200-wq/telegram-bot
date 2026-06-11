import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS
import io
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.supported_formats = ['.ogg', '.mp3', '.wav', '.m4a']
    
    async def voice_to_text(self, file_path, language=None):
        """Convert voice message to text"""
        try:
            # Convert to WAV if needed
            if not file_path.endswith('.wav'):
                audio = AudioSegment.from_file(file_path)
                file_path = file_path.rsplit('.', 1)[0] + '.wav'
                audio.export(file_path, format='wav')
            
            # Recognize speech
            with sr.AudioFile(file_path) as source:
                audio = self.recognizer.record(source)
            
            # Auto-detect language if not specified
            if not language:
                try:
                    # Try Arabic first
                    text = self.recognizer.recognize_google(audio, language='ar-SA')
                    return text, 'ar'
                except:
                    # Fall back to English
                    text = self.recognizer.recognize_google(audio, language='en-US')
                    return text, 'en'
            else:
                text = self.recognizer.recognize_google(
                    audio, 
                    language='ar-SA' if language == 'ar' else 'en-US'
                )
                return text, language
                
        except sr.UnknownValueError:
            return None, "Could not understand audio"
        except sr.RequestError as e:
            return None, f"Speech recognition service error: {e}"
        except Exception as e:
            logger.error(f"Voice to text error: {e}")
            return None, str(e)
    
    async def text_to_speech(self, text, language='en', slow=False):
        """Convert text to speech"""
        try:
            # Create TTS object
            tts = gTTS(
                text=text,
                lang='ar' if language == 'ar' else 'en',
                slow=slow
            )
            
            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer, None
            
        except Exception as e:
            logger.error(f"Text to speech error: {e}")
            return None, str(e)
