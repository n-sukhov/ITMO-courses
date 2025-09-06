# %%
import numpy as np
import cv2
from scipy import fft

# %%
plt_folder = "plots/"

# %% [markdown]
# # Задание 1

# %%
image_float = cv2.imread('1.png').astype(np.float64) / 255.0

fft_channels = []
for channel in range(3):
    channel_data = image_float[:, :, channel]
    fft_channel = fft.fftshift(fft.fft2(channel_data))
    fft_channels.append(fft_channel)
fft_image = np.stack(fft_channels, axis=-1)

original_fft = fft_image.copy()

magnitude_spectrum = np.abs(fft_image)
phase_spectrum = np.angle(fft_image)

log_magnitude = np.log1p(magnitude_spectrum)
normalized_log = (log_magnitude - np.min(log_magnitude)) / (np.max(log_magnitude) - np.min(log_magnitude))

spectrum_image = (normalized_log * 255).astype(np.uint8)
cv2.imwrite(plt_folder+'fourier_spectrum_1.png', spectrum_image)

# %%
spectrum_filtered = cv2.imread(plt_folder + 'fourier_spectrum_1_filtered.jpg').astype(np.float64) / 255.0

log_magnitude_filtered = spectrum_filtered * (np.max(log_magnitude) - np.min(log_magnitude)) + np.min(log_magnitude)
magnitude_filtered = np.expm1(log_magnitude_filtered)

filtered_fft_channels = []
for channel in range(3):
    magnitude_channel = magnitude_filtered[:, :, channel]
    phase_channel = phase_spectrum[:, :, channel]
    complex_spectrum = magnitude_channel * np.exp(1j * phase_channel)
    filtered_fft_channels.append(fft.ifft2(fft.ifftshift(complex_spectrum)))

reconstructed_image = np.stack(filtered_fft_channels, axis=-1)
reconstructed_image = np.real(reconstructed_image)
reconstructed_image = np.clip(reconstructed_image, 0, 1)
reconstructed_image_uint8 = (reconstructed_image * 255).astype(np.uint8)

cv2.imwrite(plt_folder + 'periodic_filtered_image.png', reconstructed_image_uint8)


