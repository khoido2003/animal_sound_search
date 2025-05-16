import numpy as np
import librosa

class AnimalSoundFeatures:
    """A class to extract time-domain features from animal sound audio files."""
    
    def __init__(self, frame_length=2048, hop_length=512):
        """
        Initialize the feature extractor.
        
        Args:
            frame_length (int): Number of samples per frame (e.g., 2048 samples ~ 46ms at 44.1kHz).
            hop_length (int): Number of samples between successive frames (e.g., 512 samples ~ 11ms).
        """
        self.frame_length = frame_length
        self.hop_length = hop_length

    def load_audio(self, file_path, sr=None):
        """
        Load an audio file using librosa.
        
        Args:
            file_path (str): Path to the audio file (e.g., .wav).
            sr (int, optional): Target sampling rate. If None, use the file's native rate.
        
        Returns:
            tuple: (audio signal as numpy array, sampling rate)
        """
        try:
            audio, sr = librosa.load(file_path, sr=sr)
            return audio, sr
        except Exception as e:
            raise ValueError(f"Error loading audio file: {e}")

    def split_into_frames(self, audio):
        """
        Split audio into overlapping frames.
        
        Args:
            audio (numpy array): Input audio signal.
        
        Returns:
            numpy array: Matrix of frames (shape: [num_frames, frame_length]).
        """
        #  num_frames = 1 + (N - frame_length) // hop_length
        
        # N = 2 seconds × 11025 samples/second = 22050 samples
        # num_frames = 1 + (22050 - 2048) // 512
        #            = 1 + 20002 // 512
        #            = 1 + 39
        #            = 40 frames


        frames = librosa.util.frame(
            audio, frame_length=self.frame_length, hop_length=self.hop_length
        )
        return frames.T  # Transpose to get frames as rows

    def compute_zcr(self, frames):
        """
        Compute Zero Crossing Rate for each frame.
        
        Args:
            frames (numpy array): Matrix of frames.
        
        Returns:
            numpy array: ZCR values for each frame.
        """
        # Count sign changes in each frame
        zcr = np.sum(np.abs(np.diff(np.sign(frames), axis=1)), axis=1) / (2 * self.frame_length)
        return zcr

    def compute_rms(self, frames):
        """
        Compute Root Mean Square for each frame.
        
        Args:
            frames (numpy array): Matrix of frames.
        
        Returns:
            numpy array: RMS values for each frame.
        """
        rms = np.sqrt(np.mean(frames ** 2, axis=1))
        return rms

    def extract_features(self, file_path, sr=None):
        """
        Extract time-domain features (ZCR, RMS) from an audio file.
        
        Args:
            file_path (str): Path to the audio file.
            sr (int, optional): Target sampling rate.
        
        Returns:
            dict: Dictionary containing:
                - zcr: Zero Crossing Rate per frame.
                - rms: Root Mean Square per frame.
                - sr: Sampling rate.
                - frame_times: Time of each frame's center (in seconds).
        """
        # Load audio
        audio, sr = self.load_audio(file_path, sr)
        
        # Split into frames
        frames = self.split_into_frames(audio)
        
        # Compute features
        zcr = self.compute_zcr(frames)
        rms = self.compute_rms(frames)
        
        # Compute frame times (center of each frame)
        frame_times = np.arange(len(zcr)) * self.hop_length / sr
        
        return {
            'zcr': zcr,
            'rms': rms,
            'sr': sr,
            'frame_times': frame_times
        }

if __name__ == "__main__":
    extractor = AnimalSoundFeatures(frame_length=2048, hop_length=512)
    
    audio_file = "E:/ptit/animal_sound_search/sounds_data/Donkey/esek_5.wav"
    
    try:
        # Extract features
        features = extractor.extract_features(audio_file)
        
        # Print results
        print("Zero Crossing Rate:", features['zcr'][:5])  # First 5 frames
        print("Root Mean Square:", features['rms'][:5])   # First 5 frames
        print("Frame Times (s):", features['frame_times'][:5])  # First 5 frame times
        print("Sampling Rate:", features['sr'])
    except Exception as e:
        print(f"Error: {e}")
