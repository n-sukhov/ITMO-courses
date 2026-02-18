import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

## Draw several images on a sigle plot side-by-side
## @param[in] Is tuples of image names and images to draw
## @param[in] ncols Number of culumns to use (0 to display them separately)
## @param[in] hide_axes If hide axes for a better view
def ShowImages(Is, ncols = 0, hide_axes = True, vmin = None, vmax = None):
  if len(Is) == 0:
    return
  
  # Show images one-by-one
  if len(Is) == 1 or ncols == 0:
    for I in Is:
      if I == None:
        continue

      if I[1].ndim == 2:
        axes = plt.imshow(I[1], cmap='gray', vmin = vmin, vmax = vmax)
      else:
        axes = plt.imshow(cv.cvtColor(I[1], cv.COLOR_BGR2RGB), vmin = vmin, vmax = vmax)
      plt.title(I[0])

      # If we don't need axes display, then let's hide it
      if hide_axes:
        axes.axes.get_xaxis().set_visible(False)
        axes.axes.get_yaxis().set_visible(False)
      
      # And now show image
      plt.show()
    return

  # Show images side-by-side
  fig, axes = plt.subplots(nrows = (len(Is) + ncols - 1) // ncols, ncols = ncols)
  axes = axes.flatten()
  for i in range(len(Is)):
    if Is[i] != None:
      if Is[i][1].ndim == 2:
        axes[i].imshow(Is[i][1], cmap='gray', vmin = vmin, vmax = vmax)
      else:
        axes[i].imshow(cv.cvtColor(Is[i][1], cv.COLOR_BGR2RGB), vmin = vmin, vmax = vmax)
      axes[i].set_title(Is[i][0])

    # If we don't need axes display, then let's hide it
    if hide_axes:
      axes[i].axes.get_xaxis().set_visible(False)
      axes[i].axes.get_yaxis().set_visible(False)
  
  for i in range(len(Is), ncols * ((len(Is) + ncols - 1) // ncols)):
    axes[i].set_visible(False)

  # And now show image
  plt.show()

## Draw a histogram in a given image drawing context
## @param[in, out] image image drawing context
## @param[in] data_array data to draw
## @param[in] color color to use when drawing
## @param[in] max_val scale factor for the histogram values (default is 1)
def DrawHist(image, data_array, color, max_val = 1.0):
  image_w = image.shape[1]
  image_h = image.shape[0]
  data_size = data_array.shape[0]

  step = image_w / data_size
  x = 0
  for i in range(0, data_size):
    cv.rectangle(image, 
                 (int(x), image_h - 1 - int((image_h - 1) * data_array[i] / max_val)),
                 (int(x + step) - 1, image_h - 1),
                 color, thickness = -1)
    x += step

## Draw a plot in a given image drawing context
## @param[in, out] image image drawing context
## @param[in] data_array data to draw
## @param[in] color color to use when drawing
## @param[in] max_val scale factor for the histogram values (default is 1)
def DrawGraph(image, data_array, color, max_val = 1.0):
  image_w = image.shape[1]
  image_h = image.shape[0]
  data_size = data_array.shape[0]

  step = image_w / data_size
  x = step * 0.5
  cv.line(image, 
          (0, image_h - 1 - int((image_h - 1) * data_array[0] / max_val)),
          (int(x), image_h - 1 - int((image_h - 1) * data_array[0] / max_val)),
          color, thickness = 1)

  for i in range(1, data_size):
    cv.line(image, 
            (int(x), image_h - 1 - int((image_h - 1) * data_array[i - 1] / max_val)),
            (int(x + step), image_h - 1 - int((image_h - 1) * data_array[i] / max_val)),
            color, thickness = 1)
    x += step

  cv.line(image, 
          (int(x), image_h - 1 - int((image_h - 1) * data_array[data_size - 1] / max_val)),
          (image_w - 1, image_h - 1 - int((image_h - 1) * data_array[data_size - 1] / max_val)),
          color, thickness = 1)
  
## Add the salt and pepper noise to an image
## @param[in] image An image 
## @param[in] p Probability of noise
## @param[in] s_vs_p Salt vs pepper distribution
## @return An image with noise
def SaltAndPepper(I, p = 0.05, s_vs_p = 0.5):
  # Select the salt value
  if I.dtype == np.uint8:
    salt = 255
  elif I.dtype == np.float32:
    salt = 1.0
  else:
    print("Unsopported image type")
    return None

  # Create an image
  Inoise = np.copy(I)
  # Get random value for each image poxel
  rng = np.random.default_rng()
  vals = rng.random(Inoise.shape)
  # Add salt
  Inoise[vals < p * s_vs_p] = salt
  # Add pepper
  Inoise[np.logical_and(vals >= p * s_vs_p, vals < p)] = 0
  
  return Inoise

## Add the speckle noise to an image
## @param[in] image An image 
## @param[in] var Random number variance
## @return An image with noise
def Speckle(I, var = 0.05):
  if I.dtype != np.uint8 and I.dtype != np.float32:
      print("Unsopported image values type.")
      return None

  # Generate a random number with normal distribution for each image pixel
  rng = np.random.default_rng()
  gauss = rng.normal(0, var ** 0.5, I.shape)

  # Add a multiple of this distribution to our image
  # The image values type should be taken into an account here 
  # as we should work with floating point values
  if I.dtype == np.uint8:
    out = (I.astype(np.float32) * (gauss + 1)).clip(0, 255).astype(np.uint8)
  else:
    out = I * (gauss + 1)

  return out

## Add the Gaussian noise to an image
## @param[in] image An image 
## @param[in] mean Mean value
## @param[in] var Variance
## @return An image with noise
def Gaussian(I, mean = 0, var = 0.01):
  if I.dtype != np.uint8 and I.dtype != np.float32:
    print("Unsopported image values type.")
    return None

  rng = np.random.default_rng()
  gauss = rng.normal(mean, var ** 0.5, I.shape)
  
  if I.dtype == np.uint8:
    out = (I.astype(np.float32) + gauss * 255).clip(0, 255).astype(np.uint8)
  else:
    out = (I + gauss).astype(np.float32)
  
  return out

## Add the poison noise to an image
## @param[in] image An image 
## @return An image with noise
def Poisson(I):
  rng = np.random.default_rng()
  # We have to calculate the number of unique values then add
  # the poisson distribution noise basing on this number to
  # simulate the quantization noise
  if I.dtype == np.uint8:
    Ifloat = I.astype(np.float32) / 255
    vals = len(np.unique(Ifloat))
    vals = 2 ** np.ceil(np.log2(vals))
    out = (255 * (rng.poisson(Ifloat * vals) / float(vals)).clip(0, 1)).astype(np.uint8)
  elif I.dtype == np.float32:
    vals = len(np.unique(I))
    vals = 2 ** np.ceil(np.log2(vals))
    out = rng.poisson(I * vals) / float(vals)
  else:
    print("Unsopported image values type.")
    return None
  
  return out

################################################################################
## Add noise to an image
## @param[in] image An image 
## @param[in] noise_type Noise type to add
## @param[in] param1 First noise-dependent parameter
## @param[in] param2 Second noise-dependent parameter
## @return An image with noise
## @note For "salt & pepper" type, param1 is the probability, param2 is the salt vs pepper ratio.
## @note For "speckle" type, param1 is variance.
## @note For "gaussian" type, param1 is mean, param2 is variance.
def imnoise(I, noise_type, param1 = None, param2 = None):
  # Salt & pepper (param1 - probability)
  if noise_type == "salt & pepper":
    if param1 != None:
      d = param1
    else:
      d = 0.05
    if param2 != None:
      s_vs_p = param2
    else:
      s_vs_p = 0.5
    
    return SaltAndPepper(I, d, s_vs_p)

  # Multiplicative Noise (param1 - variance)
  if noise_type =="speckle": # Variance of multiplicative noise, specified as a numeric scalar
    if param1 != None:
      var = param1
    else:
      var = 0.05

    return Speckle(I, var)

  # Gaussian Noise (param1 - mean, param2 - variance)
  if noise_type == "gaussian":
    if param1 != None:
      mean = param1
    else:
      mean = 0
    if param2 != None:
      var = param2
    else:
      var = 0.01

    return Gaussian(I, mean, var)

  # Quantization Noise
  if noise_type == "poisson":
    return Poisson(I)

  return None
