import cv2
import numpy as np
import matplotlib.pyplot as plt
from tifffile import imread, imsave
from scipy.ndimage import median_filter

def process_channel(channel, minColor, maxColor):
    channel = (channel - minColor) / (maxColor - minColor)
    channel = median_filter(channel, size=3)
    return channel

image = imread('CC123786_081022_4_Pten_pRubiGCre_redRubi_GSK3b_1to200_AR_01.lsm')

# Shape: (1, 27, 3, 512, 512)

minRed = np.min(image[0, :, 0, :, :])
maxRed = np.max(image[0, :, 0, :, :])

minGreen = np.min(image[0, :, 1, :, :])
maxGreen = np.max(image[0, :, 1, :, :])

minBlue = np.min(image[0, :, 2, :, :])
maxBlue = np.max(image[0, :, 2, :, :])

layers = []

for zStackPosition in range(27):
    red = image[0, zStackPosition, 0, :, :]
    green = image[0, zStackPosition, 1, :, :]
    blue = image[0, zStackPosition, 2, :, :]

    red = process_channel(red, minRed, maxRed)
    green = process_channel(green, minGreen, maxGreen)
    blue = process_channel(blue, minBlue, maxBlue)

    shift_red_green = cv2.phaseCorrelate(np.float32(red), np.float32(green))
    shift_red_blue = cv2.phaseCorrelate(np.float32(red), np.float32(blue))

    # round the x and y shift values to nearest integer
    dx, dy = np.round(shift_red_green[0])

    print(f"dx: {dx}, dy: {dy}")

    dx, dy = np.round(shift_red_blue[0])

    print(f"dx: {dx}, dy: {dy}")

    # create the composite image
    composite = np.zeros((red.shape[0], red.shape[1], 3), dtype=np.float32)
    composite[:, :, 0] = red
    composite[:, :, 1] = green
    composite[:, :, 2] = blue

    layers.append(composite)

# assemble the layers into a tiff stack
layers = np.array(layers)
tiff = np.transpose(layers, (0, 3, 1, 2))
tiff = np.expand_dims(tiff, axis=1)
tiff = tiff.astype(np.float32)

# save the tiff stack
imsave('output.tiff', tiff)

# plt.imshow(composite)
# plt.axis('off')
# plt.show()