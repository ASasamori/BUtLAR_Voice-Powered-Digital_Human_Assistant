import tkinter as tk
import numpy as np
import threading
import time
import random
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog
import pygame
import wave
import os

class AudioWaveformGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice AI")
        self.root.geometry("800x480")  # Common resolution for Pi displays
        self.root.configure(bg='black')
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Audio file path - check if the hardcoded path exists, otherwise set to None
        default_path = "/Users/noamargolin/Desktop/BUtLAR_Voice-Powered-Digital_Human_Assistant/GUI/ecaudio.wav"
        self.audio_file_path = default_path if os.path.exists(default_path) else None
        self.waveform_data = None
        
        # Set up full screen mode for Pi
        # Uncomment the line below when running on Raspberry Pi
        # self.root.attributes('-fullscreen', True)
        
        # Status text (Listening/Speaking)
        self.status_label = tk.Label(
            root, 
            text="Ready", 
            font=("Arial", 24),
            fg="#00FF00",
            bg="black"
        )
        self.status_label.pack(pady=20)
        
        # Create a Figure and Axes for matplotlib
        self.fig = Figure(figsize=(8, 3), facecolor='black')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('black')
        
        # Style the plot
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Create canvas for the figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Initialize the line for the waveform
        self.x = np.linspace(0, 100, 100)
        self.y = np.zeros(100)
        self.line, = self.ax.plot(self.x, self.y, color='#00FF00', linewidth=3)
        
        # Set y-axis limits
        self.ax.set_ylim(-1, 1)
        
        # Buttons frame at the bottom
        self.button_frame = tk.Frame(root, bg='black')
        self.button_frame.pack(pady=20)
        
        # Load audio file button
        self.load_button = tk.Button(
            self.button_frame,
            text="Load Audio",
            command=self.load_audio_file,
            bg="#333333",
            fg="white",
            font=("Arial", 14),
            padx=20,
            pady=10,
            relief=tk.FLAT
        )
        self.load_button.pack(side=tk.LEFT, padx=10)
        
        # Play button
        self.play_button = tk.Button(
            self.button_frame,
            text="Play Audio",
            command=self.play_audio,
            bg="#333333",
            fg="white",
            font=("Arial", 14),
            padx=20,
            pady=10,
            relief=tk.FLAT
        )
        self.play_button.pack(side=tk.LEFT, padx=10)
        
        # Ask button (to simulate starting a query)
        self.ask_button = tk.Button(
            self.button_frame,
            text="Ask Question",
            command=self.simulate_conversation,
            bg="#333333",
            fg="white",
            font=("Arial", 14),
            padx=20,
            pady=10,
            relief=tk.FLAT
        )
        self.ask_button.pack(side=tk.LEFT, padx=10)
        
        # Stop button
        self.stop_button = tk.Button(
            self.button_frame,
            text="Stop",
            command=self.stop_animation,
            bg="#333333",
            fg="white",
            font=("Arial", 14),
            padx=20,
            pady=10,
            relief=tk.FLAT
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # Animation control
        self.animation_running = False
        self.animation_thread = None
        self.current_frame = 0
        
        # Load default audio if it exists
        if self.audio_file_path:
            self.load_waveform_data()
            self.status_label.config(text=f"Loaded: {os.path.basename(self.audio_file_path)}", fg="#00FFFF")
        
    def load_audio_file(self):
        """Open file dialog to select an audio file"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        
        if file_path:
            self.audio_file_path = file_path
            self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}", fg="#00FFFF")
            self.load_waveform_data()
    
    def load_waveform_data(self):
        """Load and process waveform data from the audio file"""
        try:
            with wave.open(self.audio_file_path, 'rb') as wf:
                # Get basic file properties
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                n_frames = wf.getnframes()
                frame_rate = wf.getframerate()
                
                # Read all frames
                frames = wf.readframes(n_frames)
                
                # Convert to numpy array
                if sample_width == 2:  # 16-bit audio
                    dtype = np.int16
                elif sample_width == 4:  # 32-bit audio
                    dtype = np.int32
                else:
                    dtype = np.int8
                
                # Convert bytes to numpy array
                samples = np.frombuffer(frames, dtype=dtype)
                
                # If stereo, take only one channel
                if n_channels == 2:
                    samples = samples[::2]  # Take only left channel
                
                # Normalize to range between -1 and 1
                self.waveform_data = samples / (2**(8 * sample_width - 1))
                #self.waveform_data = samples.astype(np.float32)

                
                # Print some debug info
                print(f"Audio loaded: {os.path.basename(self.audio_file_path)}")
                print(f"Sample rate: {frame_rate}Hz, Channels: {n_channels}, Duration: {n_frames/frame_rate:.2f}s")
                
                # Downsample for visualization - adjust for longer files
                # For long files, we need a reasonable number of samples for visualization
                max_samples = 5000  # Maximum number of samples to keep for visualization
                if len(self.waveform_data) > max_samples:
                    indices = np.linspace(0, len(self.waveform_data) - 1, max_samples, dtype=int)
                    self.waveform_data = self.waveform_data[indices]
                
                # Update x-axis for the new data length
                self.x = np.linspace(0, len(self.waveform_data), len(self.waveform_data))
                self.line.set_xdata(self.x)
                self.ax.set_xlim(0, len(self.waveform_data))  # Adjust X-axis to fit the full range

                

                
                # Show part of the waveform in the display
                display_size = min(100, len(self.waveform_data))
                preview_data = self.waveform_data[:display_size]

                # y axis
                self.ax.set_ylim(np.min(self.waveform_data), np.max(self.waveform_data))
                
                # Update the plot
                self.line.set_xdata(self.x[:display_size])
                self.line.set_ydata(preview_data)
                self.ax.set_xlim(0, 100)
                #self.ax.set_ylim(-1, 1)
                self.ax.set_ylim(np.min(self.waveform_data), np.max(self.waveform_data))

                self.canvas.draw_idle()
                
        except Exception as e:
            self.status_label.config(text=f"Error loading audio: {str(e)}", fg="red")
            print(f"Error loading audio: {str(e)}")
    
    def play_audio(self):
        """Play the loaded audio file and animate the waveform"""
        if not self.audio_file_path:
            self.status_label.config(text="No audio file loaded", fg="red")
            return
        
        # Make sure pygame mixer is stopped first to avoid conflicts
        pygame.mixer.music.stop()
        
        self.status_label.config(text="Playing audio...", fg="#00FF00")
        
        # Start the waveform animation
        self.start_animation()
        
        # Play the audio in a separate thread
        def play_sound():
            try:
                pygame.mixer.music.load(self.audio_file_path)
                pygame.mixer.music.play()
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    if not self.animation_running:
                        break
                # Stop animation when audio finishes
                self.stop_animation()
                self.status_label.config(text="Ready", fg="#00FF00")
            except Exception as e:
                self.status_label.config(text=f"Playback error: {str(e)}", fg="red")
                print(f"Playback error: {str(e)}")
                self.stop_animation()
        
        threading.Thread(target=play_sound, daemon=True).start()
    
    def update_waveform(self):
        """Update the waveform animation while audio is playing"""
        frame_count = 0
        chunk_size = 5  # Reduced for smoother animation - how many frames to advance per update
        
        if self.waveform_data is not None and len(self.waveform_data) > 100:
            # Use actual audio data for visualization
            while self.animation_running:
                if frame_count >= len(self.waveform_data) - 100:
                    frame_count = 0  # Loop back to beginning
                
                # Get current window of data
                window = self.waveform_data[frame_count:frame_count + 100]
                if len(window) < 100:  # Pad if needed
                    window = np.pad(window, (0, 100 - len(window)), 'constant')
                
                # Update the line data
                self.line.set_ydata(window)
                self.canvas.draw_idle()
                
                # Advance frame counter
                frame_count += chunk_size
                time.sleep(0.03)  # Faster refresh for smoother animation
        else:
            # Fallback to generated waveform if no data available
            while self.animation_running:
                # Generate a new waveform pattern with some randomness
                amplitude = 0.7
                new_y = np.zeros(100)
                for i in range(100):
                    # Create a wave-like pattern with some randomness
                    new_y[i] = amplitude * np.sin(i * 0.2 + time.time() * 10) * random.uniform(0.5, 1.0)
                    
                # Update the line data
                self.line.set_ydata(new_y)
                self.canvas.draw_idle()
                time.sleep(0.03)
    
    def simulate_conversation(self):
        """Simulate the conversation flow"""
        # Update status to listening
        self.status_label.config(text="Listening...", fg="#00FFFF")
        self.root.update()
        
        # Simulate listening for 2 seconds
        time.sleep(2)
        
        # If we have a loaded audio file, play it
        if self.audio_file_path:
            self.status_label.config(text="Speaking...", fg="#00FF00")
            self.play_audio()
        else:
            # Otherwise just animate a fake response
            self.status_label.config(text="Speaking...", fg="#00FF00")
            self.start_animation()
            
            # Simulate AI speaking for 5 seconds
            time.sleep(5)
            
            # Stop the animation and reset status
            self.stop_animation()
            self.status_label.config(text="Ready", fg="#00FF00")
    
    def start_animation(self):
        """Start the waveform animation"""
        if not self.animation_running:
            self.animation_running = True
            self.animation_thread = threading.Thread(target=self.update_waveform)
            self.animation_thread.daemon = True
            self.animation_thread.start()
    
    def stop_animation(self):
        """Stop the waveform animation"""
        self.animation_running = False
        if self.animation_thread:
            # Wait for the thread to finish
            if self.animation_thread.is_alive():
                self.animation_thread.join(0.5)  # Reduced timeout for faster response
            self.animation_thread = None
        pygame.mixer.music.stop()

# For testing the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioWaveformGUI(root)
    root.mainloop()