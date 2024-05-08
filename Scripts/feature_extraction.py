import chemical_analysis as ca
import matplotlib.pyplot as plt
import cv2
import numpy as np
import json
import os

from typing import Tuple, List, Dict, Any
from tqdm import tqdm
from chemical_analysis.alkalinity import AlkalinitySampleDataset, ProcessedAlkalinitySampleDataset
from chemical_analysis.chloride import ChlorideSampleDataset, ProcessedChlorideSampleDataset
#from chemical_analysis.sulfate import SulfateSampleDataset, ProcessedSulfateSampleDataset
#from chemical_analysis.phosphate import PhosphateSampleDataset, ProcessedPhosphateSampleDataset

#variables
ANALYTE = "Chloride"
SKIP_BLANK = False

SAMPLES_PATH = os.path.join(os.path.dirname(__file__), "..", f"{ANALYTE}_Samples")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "cache_dir")

if SKIP_BLANK:
    SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "images", f"{ANALYTE}", "no_blank")
    TRAIN_TEST_PATH = os.path.join(os.path.dirname(__file__), "..", "Train_Test_Samples", f"{ANALYTE}", "no_blank")
else:
    SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "images", f"{ANALYTE}", "with_blank")
    TRAIN_TEST_PATH = os.path.join(os.path.dirname(__file__), "..", "Train_Test_Samples", f"{ANALYTE}", "with_blank")

#makes path dir
os.makedirs(SAVE_PATH, exist_ok = True)
os.makedirs(CACHE_PATH, exist_ok = True)
os.makedirs(TRAIN_TEST_PATH, exist_ok = True)


dataset_processor = {"Alkalinity":{"dataset": AlkalinitySampleDataset, "processed_dataset": ProcessedAlkalinitySampleDataset},
                     "Chloride": {"dataset": ChlorideSampleDataset, "processed_dataset": ProcessedChlorideSampleDataset},
                     #"Sulfate": {"dataset": SulfateSampleDataset, "processed_dataset": ProcessedSulfateSampleDataset},
                     #"Phosphate": {"dataset": PhosphateSampleDataset, "processed_dataset": ProcessedPhosphateSampleDataset},
                    }

pca_stats = {
             #"Alkalinity": {"lab_mean": np.load(ca.alkalinity.PCA_STATS)['lab_mean'], "lab_sorted_eigenvectors": np.load(ca.alkalinity.PCA_STATS)['lab_sorted_eigenvectors']},
             "Chloride"  : {"lab_mean": np.load(ca.chloride.PCA_STATS)['lab_mean']  , "lab_sorted_eigenvectors": np.load(ca.chloride.PCA_STATS)['lab_sorted_eigenvectors']},
             #"Sulfate"   : {"lab_mean": np.load(ca.sulfate.PCA_STATS)['lab_mean']   , "lab_sorted_eigenvectors": np.load(ca.sulfate.PCA_STATS)['lab_sorted_eigenvectors']},
             #"Phosphate" : {"lab_mean": np.load(ca.phosphate.PCA_STATS)['lab_mean'] , "lab_sorted_eigenvectors": np.load(ca.phosphate.PCA_STATS)['lab_sorted_eigenvectors']}
            }

SampleDataset = dataset_processor[f"{ANALYTE}"]["dataset"]
ProcessedSampleDataset = dataset_processor[f"{ANALYTE}"]["processed_dataset"]

#data preprocessing
samples = SampleDataset(
    base_dirs = SAMPLES_PATH,
    progress_bar = True,
    skip_blank_samples = SKIP_BLANK,
    skip_incomplete_samples = True,
    skip_inference_sample= True,
    skip_training_sample = False,
    verbose = True
)

processed_samples = ProcessedSampleDataset(
    dataset = samples,
    cache_dir = CACHE_PATH,
    num_augmented_samples = 0,
    progress_bar = True,
    transform = None,
    lab_mean= pca_stats[f"{ANALYTE}"]['lab_mean'],
    lab_sorted_eigenvectors = pca_stats[f"{ANALYTE}"]['lab_sorted_eigenvectors']
)

#centered crop
count_of_valid_samples = 0
for i, _ in enumerate(processed_samples):
    try:
        print(f"Imagem {i}")

        #gets the mask for that sample
        mask =  processed_samples[i].sample_analyte_mask

        nonzero_rows, nonzero_cols = np.nonzero(mask)
        min_row, max_row = min(nonzero_rows), max(nonzero_rows)
        min_col, max_col = min(nonzero_cols), max(nonzero_cols)

        #cropp based on mask
        actual_image = processed_samples[i].sample_bgr_image[min_row:max_row, min_col:max_col]

        image_heigth, image_width = actual_image.shape[0], actual_image.shape[1]

        #cropp for vgg input
        cropped_image = actual_image[int(image_heigth/2)-112:int(image_heigth/2)+112, int(image_width/2)-112:int(image_width/2)+112]

        #saves images
        plt.imsave(f"{SAVE_PATH}/sample_{count_of_valid_samples}.png", cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)/255)

        #saves analyte value
        with open(f"{SAVE_PATH}/sample_{count_of_valid_samples}.txt", "w", encoding='utf-8') as f:
            json.dump(processed_samples.analyte_values[i]['theoreticalValue'], f, ensure_ascii=False, indent=4)

        #saves analyte identifier
        with open(f"{SAVE_PATH}/sample_{count_of_valid_samples}_identity.txt", "w", encoding='utf-8') as f:
            json.dump(processed_samples[i].identifier, f, ensure_ascii=False, indent=4)
            f.write('\n')
            json.dump(processed_samples[i].sample_prefix, f, ensure_ascii=False, indent=4)

        count_of_valid_samples+=1

    except:
        print(f"Imagem problematica : {processed_samples[i].identifier},{processed_samples[i].sample_prefix}")



#DISABLED
#save images for train test of pmf based model
# for i, _ in enumerate(processed_samples):
#     #saves images
#     plt.imsave(f"{TRAIN_TEST_PATH}/sample_{i}.png", cv2.cvtColor(processed_samples[i].sample_bgr_image, cv2.COLOR_BGR2RGB)/255)
#     #saves jsons
#     with open(f"{TRAIN_TEST_PATH}/sample_{i}.txt", "w", encoding='utf-8') as f:
#         json.dump(processed_samples.alkalinity_values[i]['theoreticalValue'],f, ensure_ascii=False, indent=4)

#     print(f"sample_{i} finished!")