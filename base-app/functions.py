import numpy as np
from skimage.exposure import match_histograms
from scipy.ndimage import median_filter
from PIL import Image, ImageTk

def find_reference(channel):
    # Compute the mean and standard deviation along the z-axis
    means = np.mean(channel, axis=(1, 2))
    stds = np.std(channel, axis=(1, 2))

    # Compute the SNR for each z-slice
    snrs = 10 * np.log10(means / stds)

    # Find the index of the z-slice with the highest SNR
    reference = np.argmax(snrs)

    return reference

def process_channel(channel, channel_idx, progress, progress_label, preview_image, reference_image, update_time_estimate):
    reference = find_reference(channel)    
    normalized = []

    # the image is grayscale, but convert it to
    reference_img = ImageTk.PhotoImage(Image.fromarray(channel[reference]).resize((200, 200)))

    reference_image.configure(image=reference_img)
    reference_image.image = reference_img
    
    for image in channel:
        matched = match_histograms(image, channel[reference])
        normalized.append(median_filter(matched, size=3))
        
        # the image is 1024x1024, but put everything into the green channel

        color_image = np.zeros((channel[reference].shape[0], channel[reference].shape[1], 3), dtype=np.uint8)
        color_image[:, :, channel_idx] = normalized[-1]

        preview_img = ImageTk.PhotoImage(Image.fromarray(color_image).resize((200, 200)))
        preview_image.configure(image=preview_img)
        preview_image.image = preview_img
        progress['value'] += 1
        progress_label['text'] = "{}%".format(int(progress['value'] / progress['maximum'] * 100))

        update_time_estimate()
        
    # Use numpy array for efficient in-place operation
    normalized = np.array(normalized)
    
    return normalized

# before: 80.7450921535492s
# after: 47.067004919052124s