import numpy as np
import wave
import struct

def generate_upbeat_lofi_track(filename="/config/Desktop/BuildWithGemini/demo_recording/bg_lofi.wav", duration=60.0, sample_rate=44100):
    bpm = 84
    spb = 60.0 / bpm  # seconds per beat (~0.714s)
    total_samples = int(duration * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float32)

    # Chord progression: Dm9 -> G13 -> Cmaj9 -> Am9 (Upbeat jazzy lo-fi in C major / A minor)
    # Frequencies in Hz:
    # Dm9: D3 (146.83), F3 (174.61), A3 (220.00), C4 (261.63), E4 (329.63)
    # G13: G2 (98.00), F3 (174.61), B3 (246.94), E4 (329.63), A4 (440.00)
    # Cmaj9: C3 (130.81), E3 (164.81), G3 (196.00), B3 (246.94), D4 (293.66)
    # Am9: A2 (110.00), E3 (164.81), G3 (196.00), C4 (261.63), B4 (493.88)
    
    chords = [
        ([146.83, 174.61, 220.00, 261.63, 329.63], 146.83),  # Dm9, bass D
        ([98.00, 174.61, 246.94, 329.63, 440.00], 98.00),     # G13, bass G
        ([130.81, 164.81, 196.00, 246.94, 293.66], 130.81),  # Cmaj9, bass C
        ([110.00, 164.81, 196.00, 261.63, 493.88], 110.00),   # Am9, bass A
    ]
    
    # Generate time array
    t = np.arange(total_samples) / sample_rate

    # 1. Warm Vinyl Tape Noise & Lo-Fi Crackle
    np.random.seed(42)
    noise = np.random.normal(0, 0.015, total_samples)
    # Random crackles
    crackle_idx = np.random.choice(total_samples, size=int(duration * 12), replace=False)
    noise[crackle_idx] += np.random.uniform(-0.15, 0.15, len(crackle_idx))
    audio += noise * 0.35

    # 2. Electric Piano (Chords with slight tremolo / vibrato & warm harmonics)
    samples_per_chord = int(spb * 4 * sample_rate) # 4 beats per chord
    num_chords_total = int(np.ceil(total_samples / samples_per_chord))

    for i in range(num_chords_total):
        chord_notes, bass_freq = chords[i % len(chords)]
        start_samp = i * samples_per_chord
        end_samp = min(total_samples, (i + 1) * samples_per_chord)
        chord_len = end_samp - start_samp
        if chord_len <= 0:
            break
            
        t_chord = np.arange(chord_len) / sample_rate
        chord_wave = np.zeros(chord_len, dtype=np.float32)

        # Decay envelope for Rhodes / electric piano
        env = np.exp(-t_chord / 1.8) * (1.0 - np.exp(-t_chord / 0.02))

        # Electric piano notes
        for freq in chord_notes:
            # Vibrato
            vib = 1.0 + 0.003 * np.sin(2 * np.pi * 4.5 * t_chord)
            # Fundamental + soft harmonics
            wave_note = (
                0.6 * np.sin(2 * np.pi * freq * vib * t_chord) +
                0.25 * np.sin(2 * np.pi * 2 * freq * vib * t_chord) +
                0.1 * np.sin(2 * np.pi * 3 * freq * vib * t_chord)
            )
            chord_wave += wave_note * 0.12 * env

        # Warm Lo-Fi Sub-Bass (Sine wave)
        bass_env = np.exp(-t_chord / 2.0)
        bass_wave = np.sin(2 * np.pi * (bass_freq / 2.0) * t_chord) * 0.22 * bass_env
        chord_wave += bass_wave

        audio[start_samp:end_samp] += chord_wave

    # 3. Lo-Fi Hip Hop Drum Beat (Kick, Snare/Clap, Hi-Hat)
    samples_per_beat = int(spb * sample_rate)
    total_beats = int(duration / spb)

    for b in range(total_beats):
        b_start = int(b * spb * sample_rate)
        beat_in_bar = b % 4

        # Hi-hat on every 8th note (straight / light swing)
        for sub in [0, 0.5]:
            h_start = int((b + sub) * spb * sample_rate)
            h_len = int(0.04 * sample_rate)
            if h_start + h_len < total_samples:
                t_h = np.arange(h_len) / sample_rate
                # High frequency filtered noise
                h_env = np.exp(-t_h / 0.015)
                h_sound = np.random.normal(0, 0.08, h_len) * h_env
                audio[h_start:h_start + h_len] += h_sound * 0.35

        # Kick on beat 0 and syncopated beat 2.5
        if beat_in_bar == 0 or (beat_in_bar == 2 and np.random.rand() > 0.3):
            k_len = int(0.25 * sample_rate)
            if b_start + k_len < total_samples:
                t_k = np.arange(k_len) / sample_rate
                # Pitch drop from 120Hz to 45Hz
                k_pitch = 45.0 + 80.0 * np.exp(-t_k / 0.035)
                k_phase = 2 * np.pi * np.cumsum(k_pitch) / sample_rate
                k_env = np.exp(-t_k / 0.08)
                k_sound = np.sin(k_phase) * 0.38 * k_env
                audio[b_start:b_start + k_len] += k_sound

        # Snare / Rimshot on beat 1 and beat 3 (0-indexed: 1 and 3)
        if beat_in_bar in [1, 3]:
            s_len = int(0.18 * sample_rate)
            if b_start + s_len < total_samples:
                t_s = np.arange(s_len) / sample_rate
                s_env = np.exp(-t_s / 0.045)
                # Tone (180Hz) + white noise snap
                s_tone = np.sin(2 * np.pi * 180 * t_s) * 0.15
                s_noise = np.random.normal(0, 0.12, s_len)
                s_sound = (s_tone + s_noise) * s_env * 0.4
                audio[b_start:b_start + s_len] += s_sound

    # 4. Master Fade-out at the last 2 seconds
    fade_len = int(2.5 * sample_rate)
    fade_curve = np.linspace(1.0, 0.0, fade_len)
    audio[-fade_len:] *= fade_curve

    # Normalize audio to prevent clipping
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.85

    # Export to 16-bit PCM WAV
    int_audio = (audio * 32767).astype(np.int16)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_audio.tobytes())

    print(f"Lo-fi track generated successfully: {filename}")

if __name__ == "__main__":
    generate_upbeat_lofi_track()
