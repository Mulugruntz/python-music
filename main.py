import pathlib
import os.path
import re
import subprocess
import shlex
from importlib import import_module
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


def note(name: str, beats: float, bpm: int = BPM, time_signature: Tuple[int, int] = TIME_SIGNATURE) -> np.ndarray:
    freq, multiplier = note_name_to_freq_and_multiplier(name, time_signature)
    n = envelope(pulse(freq, multiplier * beats * 60 / bpm))
    return n


def note_name_to_freq_and_multiplier(name: str, time_signature: Tuple[int, int]) -> Tuple[float, float]:
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
            return 0.0, float(RESTS_TO_MULTIPLIER[note_props['rest']]) * time_signature[1]
        rank = (
                12 * (int(note_props['scale']) - 4)
                + SEMITONE_DIST_TO_A[note_props['note']]
                + (1 if note_props['accidental'] == '#' else
                   -1 if note_props['accidental'] == 'b' else 0)
        )
        print(f"note {name} => {rank} => {f(rank)} Hz")

        return f(rank), float(note_props['beats']) if note_props['beats'] else 1
    raise Exception


def read_pyscore_into_mp3(pyscore_name: str) -> str:
    input_music_data = import_module(pyscore_name)
    if 'score' not in input_music_data.__dict__:
        raise ImportError(f'Could not find variable `score` in {input_music_data.__file__}')

    package_name = input_music_data.__package__
    if package_name.startswith('input.'):
        package_name = package_name[6:]

    output_dir = pathlib.Path(OUTPUT_PATH, *package_name.split('.'))

    score = input_music_data.score
    waves = []
    bpm = score.bpm
    time_signature = score.time_signature
    for i, channel in enumerate(score.channels):
        waves.append(np.concatenate(np.array(
            [note(n, 0.5, bpm, time_signature)
             for n in channel.channel_score.replace("  ", " ").replace('\n', '').strip().split()]
        )).ravel())

    wave_len = max(map(len, waves))

    for i, wave in enumerate(waves.copy()):
        waves[i] = np.pad(wave, (0, wave_len - len(wave)), 'constant', constant_values=(.0, .0))

    os.makedirs(output_dir, exist_ok=True)

    # when muxed directly in numpy, the overlap sounds bad
    wave = sum(waves)
    output_bin_file = pathlib.Path(output_dir, 'output_numpy.bin')

    with open(output_bin_file, 'wb') as output:
        output.write(wave.tobytes())

    output_numpy_mp3 = pathlib.Path(output_dir, 'output_numpy.mp3')
    output_numpy_mp3.unlink(missing_ok=True)
    subprocess.Popen(shlex.split(
        f'ffmpeg -f f32le -ar {SAMPLE_RATE} -i {output_bin_file} {output_numpy_mp3}'
    )).wait()

    # when muxed in ffmpeg, the overlap sounds perfect
    cmd_ffmpeg_i = []
    for i, channel in enumerate(score.channels):
        channel_output_bin_file = pathlib.Path(output_dir, f'{channel.name.replace(" ", "_").lower()}_output.bin')
        cmd_ffmpeg_i.append(f'-f f32le -ar {SAMPLE_RATE} -i {channel_output_bin_file}')
        with open(channel_output_bin_file, 'wb') as output:
            output.write(waves[i].tobytes())

    output_mp3 = pathlib.Path(output_dir, 'output.mp3')
    output_mp3.unlink(missing_ok=True)

    subprocess.Popen(shlex.split(
        f'ffmpeg '
        f'{" ".join(cmd_ffmpeg_i)} '
        f'-filter_complex amix=inputs={len(cmd_ffmpeg_i)}:duration=longest '
        f'{output_mp3}'
    )).wait()

    return output_mp3


def main() -> None:
    output_mp3 = read_pyscore_into_mp3('input.fur_elise_beginner')

    # let's play!
    subprocess.Popen(shlex.split(f"ffplay -autoexit -showmode 0 {output_mp3}")).wait()


if __name__ == '__main__':
    main()
