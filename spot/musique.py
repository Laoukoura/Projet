"""Musique originale synthétisée pour le spot (44 s, ~120 BPM, progression I–V–vi–IV en do majeur)."""
import numpy as np, wave, sys

SR = 44100
DUR = 44.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
BEAT = 0.5  # 120 BPM
CUTS = [4.2, 9.0, 15.0, 22.0, 29.0, 35.0]


def lowpass(x, fc):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / fc) ** 4)
    return np.fft.irfft(X, len(x))


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) if na else 1
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def place(buf, sig, start):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


# Accords (notes MIDI) : C, G, Am, F — un accord par mesure (2 s)
CH = [[48, 55, 60, 64, 67], [43, 55, 59, 62, 67], [45, 57, 60, 64, 69], [41, 53, 57, 60, 65]]
ROOT = [36, 43, 45, 41]

pad = np.zeros(N); bass = np.zeros(N); arp = np.zeros(N); drums = np.zeros(N); fx = np.zeros(N); piano = np.zeros(N)

bar = 2.0
nbars = int(np.ceil(DUR / bar))
for b in range(nbars):
    c = CH[b % 4]; t0 = b * bar
    n = int((bar + 0.6) * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    for m in c[1:]:
        for d in (-0.08, 0.08):
            ph = hz(m + d) * tt
            s += 2 * (ph % 1) - 1
    place(pad, s * env(n, 0.5, 0.7) / 8, t0)
    # basse (à partir de 4.2 s)
    if t0 >= 4:
        for k in range(4):
            nb = int(0.45 * SR); tb = np.arange(nb) / SR
            f = hz(ROOT[b % 4])
            sb = np.sin(2 * np.pi * f * tb) + 0.3 * np.sin(4 * np.pi * f * tb)
            place(bass, sb * env(nb, 0.005, 0.25) * 0.5, t0 + k * BEAT)
    # arpège (croches)
    for k in range(8):
        m = c[1:][[0, 1, 2, 3, 2, 1, 3, 2][k]] + 12
        na = int(0.35 * SR); ta = np.arange(na) / SR
        sa = np.sin(2 * np.pi * hz(m) * ta) * np.exp(-ta * 9) + 0.25 * np.sin(4 * np.pi * hz(m) * ta) * np.exp(-ta * 14)
        place(arp, sa * 0.22, t0 + k * BEAT / 2)

# piano d'intro et d'outro (accords plaqués)
def piano_chord(c, start, length=1.9, vol=0.18):
    n = int(length * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for m in c[2:]:
        f = hz(m + 12)
        s += (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt) + 0.15 * np.sin(6 * np.pi * f * tt)) * np.exp(-tt * 1.6)
    place(piano, s * vol, start)

for b in range(2):
    piano_chord(CH[b % 4], b * bar)
for b in range(17, 22):
    piano_chord(CH[b % 4], b * bar, vol=0.2)

# batterie
def kick():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    f = 50 + 90 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7) * 0.9

def clap():
    n = int(0.25 * SR); tt = np.arange(n) / SR
    return lowpass(rng.normal(0, 1, n), 3500) * np.exp(-tt * 22) * 0.35

def hat():
    n = int(0.08 * SR); tt = np.arange(n) / SR
    x = rng.normal(0, 1, n); x = x - lowpass(x, 7000)
    return x * np.exp(-tt * 60) * 0.18

K, C, H = kick(), clap(), hat()
bt = 4.0
while bt < 35.0:
    i = round((bt - 4) / BEAT)
    full = 15.0 <= bt < 35.0
    place(drums, K, bt)
    if i % 2 == 1:
        place(drums, C, bt)
    if full or bt >= 9:
        place(drums, H, bt + BEAT / 2)
    if full and i % 2 == 0:
        place(drums, H * 0.6, bt + BEAT / 4)
    bt += BEAT

# montées (riser) avant les coupes principales + impacts aux coupes
def riser(length):
    n = int(length * SR); tt = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    x = x - lowpass(x, 800)
    return x * (tt / length) ** 2 * 0.25

def impact():
    n = int(1.6 * SR); tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 3)
    noise = lowpass(rng.normal(0, 1, n), 1500) * np.exp(-tt * 6) * 0.4
    return (boom + noise) * 0.7

for c, L in [(4.2, 2.0), (15.0, 3.0), (35.0, 3.0)]:
    place(fx, riser(L), c - L)
for c in CUTS:
    place(fx, impact() * (1.0 if c in (4.2, 15.0, 35.0) else 0.55), c)

pad = lowpass(pad, 1800); arp = lowpass(arp, 6000)
mix = 0.55 * pad + 0.9 * bass + 0.6 * arp + 0.9 * drums + 0.8 * fx + piano
# réverbération simple (échos multiples) sur pad/arp/piano
wet = 0.6 * pad + 0.6 * arp + piano
rv = np.zeros(N)
for d, g in [(0.031, .5), (0.047, .45), (0.071, .4), (0.113, .32), (0.167, .25), (0.241, .18), (0.353, .12)]:
    k = int(d * SR); rv[k:] += wet[:-k] * g
mix += lowpass(rv, 4000) * 0.35

# stéréo léger + fondu
L = mix + 0.15 * np.roll(arp, 300); R = mix + 0.15 * np.roll(arp, -300)
fade = np.ones(N); fo = int(2.5 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
fade[: int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
st = np.stack([L * fade, R * fade], 1)
st = np.tanh(st / np.abs(st).max() * 1.4) * 0.9
out = sys.argv[1] if len(sys.argv) > 1 else "musique.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype("<i2").tobytes())
print("ok", out)
