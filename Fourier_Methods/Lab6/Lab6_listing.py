# %%
import numpy as np
import cv2
from scipy import fft
import matplotlib.pyplot as plt
from scipy.signal import convolve2d

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

# %% [markdown]
# # Задание 2

# %%
dogsimg = cv2.imread("dogs.jpg")
gray_img = cv2.cvtColor(dogsimg, cv2.COLOR_BGR2GRAY)
cv2.imwrite("black_dogs.jpg", gray_img)

# %% [markdown]
# #### Ядра

# %%
def gaussian_kernel(N):
    sigma = (N - 1) / 6
    center = (N + 1) / 2
    i = np.arange(1, N+1) - center
    j = np.arange(1, N+1) - center
    ii, jj = np.meshgrid(i, j)
    kernel = np.exp(-(ii**2 + jj**2) / (2 * sigma**2))
    return kernel / np.sum(kernel)

def box_kernel(N):
    kernel = np.ones((N, N))
    return kernel / np.sum(kernel)

sharp_kernel = np.array([[0, -1, 0],
                         [-1, 5, -1],
                         [0, -1, 0]])

edge_kernel = np.array([[-1, -1, -1],
                        [-1, 8, -1],
                        [-1, -1, -1]])

negative_kernel = np.array([[0, 0, 0],
                            [0, -1, 0],
                            [0, 0, 0]])

# %%
img = np.array(gray_img)

N_values = [7, 27, 57]

gaussian_results = []
for N in N_values:
    kernel = gaussian_kernel(N)
    result = convolve2d(img, kernel, mode='same', boundary='symm')
    gaussian_results.append(result)

box_results = []
for N in N_values:
    kernel = box_kernel(N)
    result = convolve2d(img, kernel, mode='same', boundary='symm')
    box_results.append(result)

sharp_result = convolve2d(img, sharp_kernel, mode='same', boundary='symm')

edge_result = convolve2d(img, edge_kernel, mode='same', boundary='symm')

negative_result = convolve2d(img, negative_kernel, mode='same', boundary='symm')

# %%



