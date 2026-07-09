from rtlsdr import RtlSdr
import numpy as np
import matplotlib.pyplot as plt

# GEOCOM base frequency
CENTER_FREQ = 454.975e6

# 1.024 MHz like SDR++
SAMPLE_RATE = 250e3

# Number of samples per FFT
FFT_SIZE = 4096


sdr = RtlSdr()

sdr.sample_rate = SAMPLE_RATE
sdr.center_freq = CENTER_FREQ
sdr.gain = 'auto'

plt.ion()

fig, ax = plt.subplots()

freqs = np.linspace(
    CENTER_FREQ - SAMPLE_RATE / 2,
    CENTER_FREQ + SAMPLE_RATE / 2,
    FFT_SIZE
)

line, = ax.plot(
    freqs / 1e6,
    np.zeros(FFT_SIZE)
)

ax.set_xlabel("Frequency (MHz)")
ax.set_ylabel("Power (dB)")
ax.set_title("RTL-SDR Spectrum")
ax.grid()


try:
    while True:

        samples = sdr.read_samples(FFT_SIZE)

        # FFT
        spectrum = np.fft.fftshift(
            np.fft.fft(samples)
        )

        power = 20 * np.log10(
            np.abs(spectrum)
        )

        line.set_ydata(power)

        ax.set_ylim(
            np.min(power),
            np.max(power) + 10
        )

        fig.canvas.draw()
        fig.canvas.flush_events()


except KeyboardInterrupt:
    print("Stopping SDR")

finally:
    sdr.close()
