import pathlib
import os.path
import re
import subprocess
import shlex
from typing import Tuple, Dict

import numpy as np

SAMPLE_RATE = 48_000
OUTPUT_PATH = pathlib.Path('output')
STANDARD_PITCH = 440.0
BPM = 120
TIME_SIGNATURE = (3, 4)
RE_NOTE_NAME = re.compile(
    r"(?P<note>[ABCDEFG])"
    r"(?P<accidental>[#b]?)"
    r"(?P<scale>[0-8])"
    r"(?:-(?P<beats>\d*\.?\d+))?"
    r"|(?P<rest>R[lbsmcq])"
)
SUSTAIN_LEVEL = 0.5
# attack, decay, sustain, release
ADSR_ENVELOPE = np.array([0.0, 1.0] + [SUSTAIN_LEVEL] + [SUSTAIN_LEVEL] * 20 + [SUSTAIN_LEVEL, 0.0])

SEMITONE_DIST_TO_A = {
    "A": 0,
    "B": 2,
    "C": -9,
    "D": -7,
    "E": -5,
    "F": -4,
    "G": -2,
}


RESTS_TO_MULTIPLIER: Dict[str, float] = {
    "Rl": 4.,       # Long
    "Rb": 2.,       # Breve
    "Rs": 1.,       # Semibreve
    "Rm": 0.5,      # Minim
    "Rc": 0.25,     # Crotchet
    "Rq": 0.125,    # Quaver
}


def f(semitone: int) -> float:
    return STANDARD_PITCH * (2 ** (1.0 / 12.0)) ** semitone


def pulse(hz: float, duration: float) -> np.ndarray:
    return (np.sin(2 * np.pi * np.arange(SAMPLE_RATE * duration) * hz / SAMPLE_RATE)).astype(np.float32)


def envelope(freq: np.ndarray, adsr_envelope: np.ndarray=ADSR_ENVELOPE) -> np.ndarray:
    interpolated_envelope = np.interp(np.linspace(0, 1.0, len(freq)), np.linspace(0, 1.0, len(adsr_envelope)), adsr_envelope)
    e = np.multiply(freq, interpolated_envelope).astype(np.float32)
    return e


def note(hz: float, beats: float) -> np.ndarray:
    n = envelope(pulse(hz, beats * 60 / BPM))
    return n


def note2(name: str, beats: float) -> np.ndarray:
    freq, multiplier = note_name_to_freq_and_multiplier(name)
    n = envelope(pulse(freq, multiplier * beats * 60 / BPM))
    return n


def note_name_to_freq_and_multiplier(name: str) -> Tuple[float, float]:
    """
    Accepted names are case-insensitive and in the form
        A4, B4, A3, A#4, Bb4

    Beats multiplier can be added so
        A4-2 will mean that it's 2x longer than the normal beat multiplier

    Moreover, the following rests are accepted:
        Rl  Long          4
        Rb  Breve         2
        Rs  Semibreve     1
        Rm  Minim         1/2
        Rc  Crotchet      1/4
        Rq  Quaver        1/8
    """
    name = name.lower().capitalize()
    if match := RE_NOTE_NAME.match(name):
        note_props = match.groupdict()
        if note_props['rest'] is not None:
            return 0.0, float(RESTS_TO_MULTIPLIER[note_props['rest']]) * TIME_SIGNATURE[1]
        rank = (
                12 * (int(note_props['scale']) - 4)
                + SEMITONE_DIST_TO_A[note_props['note']]
                + (1 if note_props['accidental'] == '#' else
                   -1 if note_props['accidental'] == 'b' else 0)
        )
        print(f"note {name} => {rank} => {f(rank)} Hz")

        return f(rank), float(note_props['beats']) if note_props['beats'] else 1
    raise Exception


def main() -> None:
    score_left_hand = """
    E5 D#5
    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 G#4 B4
    C5-2 Rq E4 E5 D#5
    
    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 C5 B4
    A4-4 Rm E5 D#5
    E5 D#5 E5 B4 D5 C5
    
    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 G#4 B4
    C5-2 Rq E4 E5 D#5
    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4
    
    B4-2 Rq E4 C5 B4
    A4-2 Rq B4 C5 D5
    E5-2 Rq G4 F5 E5
    D5-2 Rq F4 E5 D5
    C5-2 Rq E4 D5 C5
    
    B4-2 E4 E4 E5 E4
    E5 E5 E6 D#5 E5 D#5
    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 G#4 B4
    
    C5-2 Rq E4 E5 D#5
    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 C5 B4
    A4-2 Rm
    """

    score_right_hand = """
    Rm
    Rs Rm
    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm
    
    Rs Rm
    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm
    Rs Rm
    
    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm
    Rs Rm
    A2 E3 A3 Rq Rm
    
    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm
    C3 G3 C4 Rq Rm
    G2 G3 B3 Rq Rm
    A2 E3 A3 Rq Rm
    
    E2 E3 Rm Rm
    Rs Rm
    Rs Rm
    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm
    
    A2 E3 A3 Rq Rm
    Rs Rm
    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm
  """
    wave_left_hand = np.concatenate(np.array(
        [note2(n, 0.5) for n in score_left_hand.replace("  ", " ").replace('\n', '').strip().split()]
    )).ravel()
    wave_right_hand = np.concatenate(np.array(
        [note2(n, 0.5) for n in score_right_hand.replace("  ", " ").replace('\n', '').strip().split()]
    )).ravel()

    wave_len = max(len(wave_left_hand), len(wave_right_hand))

    wave_left_hand = np.pad(wave_left_hand, (0, wave_len - len(wave_left_hand)), 'constant', constant_values=(.0, .0))
    wave_right_hand = np.pad(wave_right_hand, (0, wave_len - len(wave_right_hand)), 'constant', constant_values=(.0, .0))

    os.makedirs(OUTPUT_PATH, exist_ok=True)

    # when muxed directly in numpy, the overlap sounds bad
    wave = (wave_left_hand + wave_right_hand)
    output_bin_file = pathlib.Path(OUTPUT_PATH, 'output.bin')

    with open(output_bin_file, 'wb') as output:
        output.write(wave.tobytes())

    output_numpy_mp3 = pathlib.Path(OUTPUT_PATH, 'output_numpy.mp3')
    output_numpy_mp3.unlink(missing_ok=True)
    subprocess.Popen(shlex.split(
        f'ffmpeg -f f32le -ar {SAMPLE_RATE} -i {output_bin_file} {output_numpy_mp3}'
    )).wait()

    # when muxed in ffmpeg, the overlap sounds perfect
    left_output_bin_file = pathlib.Path(OUTPUT_PATH, 'left_output.bin')
    right_output_bin_file = pathlib.Path(OUTPUT_PATH, 'right_output.bin')
    with open(left_output_bin_file, 'wb') as output:
        output.write(wave_left_hand.tobytes())
    with open(right_output_bin_file, 'wb') as output:
        output.write(wave_right_hand.tobytes())

    output_mp3 = pathlib.Path(OUTPUT_PATH, 'output.mp3')
    output_mp3.unlink(missing_ok=True)
    subprocess.Popen(shlex.split(
        f'ffmpeg '
        f'-f f32le -ar {SAMPLE_RATE} -i {left_output_bin_file} '
        f'-f f32le -ar {SAMPLE_RATE} -i {right_output_bin_file} '
        f'-filter_complex amix=inputs=2:duration=longest '
        f'{output_mp3}'
    )).wait()

    # let's play!
    subprocess.Popen(shlex.split(f"ffplay -autoexit -showmode 0 {output_mp3}")).wait()


if __name__ == '__main__':
    main()
