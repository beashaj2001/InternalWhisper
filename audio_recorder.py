import io
import time
import wave
import numpy as np
import sounddevice as sd
import logging
import tempfile
import os

logger = logging.getLogger("InternalWhisper.AudioRecorder")

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.frames = []
        self.stream = None
        self.device_index = None
        self.current_volume_rms = 0.0

    @staticmethod
    def get_input_devices():
        """Returns a list of input audio devices [(index, name), ...]"""
        devices = []
        try:
            dev_list = sd.query_devices()
            for idx, dev in enumerate(dev_list):
                if dev.get('max_input_channels', 0) > 0:
                    devices.append((idx, dev.get('name', f'Device {idx}')))
        except Exception as e:
            logger.error(f"Failed to query audio devices: {e}")
        return devices

    def set_device(self, device_index):
        self.device_index = device_index

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio stream status: {status}")
        if self.is_recording:
            # Copy incoming audio data
            data_copy = indata.copy()
            self.frames.append(data_copy)
            
            # Calculate RMS for visualizer VU meter (0.0 to 1.0)
            rms = np.sqrt(np.mean(data_copy**2)) if len(data_copy) > 0 else 0.0
            # Scale & normalize RMS for easier UI representation
            self.current_volume_rms = float(np.clip(rms * 10.0, 0.0, 1.0))

    def start_recording(self, device_index=None):
        if self.is_recording:
            return
        
        self.frames = []
        self.is_recording = True
        self.current_volume_rms = 0.0
        target_device = device_index if device_index is not None else self.device_index
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                device=target_device,
                callback=self._audio_callback
            )
            self.stream.start()
            logger.info("Audio recording started.")
        except Exception as e:
            self.is_recording = False
            logger.error(f"Failed to start audio recording stream: {e}")
            raise e

    def stop_recording(self):
        if not self.is_recording:
            return None
            
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")
            self.stream = None
            
        logger.info("Audio recording stopped.")
        return self._save_to_temp_wav()

    def _save_to_temp_wav(self):
        if not self.frames:
            logger.warning("No audio frames recorded.")
            return None
            
        try:
            # Concatenate all recorded float32 frames
            audio_data = np.concatenate(self.frames, axis=0)
            # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
            int16_data = (audio_data * 32767).astype(np.int16)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_path = temp_file.name
            temp_file.close()
            
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(int16_data.tobytes())
                
            logger.info(f"Audio saved to temporary WAV: {temp_path} ({os.path.getsize(temp_path)} bytes)")
            return temp_path
        except Exception as e:
            logger.error(f"Failed to save audio frames to WAV file: {e}")
            return None

    def get_volume_level(self):
        """Returns normalized audio level (0.0 - 1.0) for visualizer"""
        return self.current_volume_rms
