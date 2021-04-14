import logging, argparse
import os 

import numpy as np
import collections

import bfio
from bfio import BioReader

from csbdeep.utils import normalize

from splinedist import fill_label_holes
from splinedist.utils import phi_generator, grid_generator, get_contoursize_max
from splinedist.models import Config2D, SplineDist2D, SplineDistData2D
from splinedist.utils import phi_generator, grid_generator, get_contoursize_max
from splinedist import random_label_cmap

import keras.backend as K
import tensorflow as tf
from tensorflow import keras

import cv2

import matplotlib
matplotlib.rcParams["image.interpolation"] = None
import matplotlib.pyplot as plt
lbl_cmap = random_label_cmap()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger("train")
logger.setLevel(logging.INFO)


def get_jaccard_index(prediction, ground_truth):
    imageshape = prediction.shape
    prediction[prediction > 0] = 1
    ground_truth[ground_truth > 0] = 1

    totalsum = np.sum(prediction == ground_truth)
    jaccard = totalsum/(imageshape[0]*imageshape[1])

    return jaccard

def random_fliprot(img, mask): 
    img = np.array(img)
    mask = np.array(mask)
    assert img.ndim >= mask.ndim
    axes = tuple(range(mask.ndim))
    perm = tuple(np.random.permutation(axes))
    img = img.transpose(perm + tuple(range(mask.ndim, img.ndim))) 
    mask = mask.transpose(perm) 
    for ax in axes: 
        if np.random.rand() > 0.5:
            img = np.flip(img, axis=ax) # reverses the order of elements
            mask = np.flip(mask, axis=ax) # reverses the order of elements
    return img, mask 

def random_intensity_change(img):
    img = img*np.random.uniform(0.6,2) + np.random.uniform(-0.2,0.2)
    return img

def augmenter(x, y):
    """Augmentation of a single input/label image pair.
    x is an input image
    y is the corresponding ground-truth label image
    """
    x, y = random_fliprot(x, y)
    x = random_intensity_change(x)
    sig = 0.02*np.random.uniform(0,1)
    x = x + sig*np.random.normal(0,1,x.shape)
    return x, y


def create_plots(array_images, array_labels, input_len, output_dir, model):
    jaccard_indexes = []
    
    for i in range(input_len):
        fig, (a_image,a_groundtruth,a_prediction) = plt.subplots(1, 3, 
                                                            figsize=(12,5), 
                                                            gridspec_kw=dict(width_ratios=(1,1,1)))

        image = array_images[i]
        ground_truth = array_labels[i]
        prediction, details = model.predict_instances(ground_truth)
        print(np.unique(prediction))
        
        plt_image = a_image.imshow(image)
        a_image.set_title("Image")

        plt_groundtruth = a_groundtruth.imshow(ground_truth)
        a_groundtruth.set_title("Ground Truth")

        plt_prediction = a_prediction.imshow(prediction)
        a_prediction.set_title("Prediction")

        jaccard = get_jaccard_index(prediction, ground_truth)
        jaccard_indexes.append(jaccard)
        plot_file = "{}.jpg".format(i)
        fig.text(0.50, 0.02, 'Jaccard Index = {}'.format(jaccard), 
            horizontalalignment='center', wrap=True)
        plt.savefig(os.path.join(output_dir, plot_file))
        plt.clf()
        plt.cla()
        plt.close(fig)
 
        logger.info("{} has a jaccard index of {}".format(plot_file, jaccard))

    average_jaccard = sum(jaccard_indexes)/input_len
    logger.info("Average Jaccard Index for Testing Data: {}".format(average_jaccard))

def train_nn(image_dir_input,
             label_dir_input,
             image_dir_test,
             label_dir_test,
             split_percentile,
             output_directory,
             gpu,
             imagepattern):

    input_images = sorted(os.listdir(image_dir_input))
    input_labels = sorted(os.listdir(label_dir_input))
    num_inputs = len(input_images)
    
    logger.info("\n Getting Data for Training and Testing  ...")
    if split_percentile == None:
        logger.info("Getting From Testing Directories")
        X_trn = input_images
        Y_trn = input_labels
        X_val = sorted(os.listdir(image_dir_test))
        Y_val = sorted(os.listdir(label_dir_test))
    else:
        logger.info("Splitting Input Directories")
        rng = np.random.RandomState(42)
        index = rng.permutation(num_inputs)
        n_val = np.ceil((split_percentile/100) * num_inputs).astype('int')
        ind_train, ind_val = index[:-n_val], index[-n_val:]
        X_val, Y_val = [input_images[i] for i in ind_val]  , [input_labels[i] for i in ind_val] # splitting data into train and testing
        X_trn, Y_trn = [input_images[i] for i in ind_train], [input_labels[i] for i in ind_train] 
        image_dir_test = image_dir_input
        label_dir_test = label_dir_input
    
    num_images_trained = len(X_trn)
    num_labels_trained = len(Y_trn)
    num_images_tested = len(X_val)
    num_labels_tested = len(Y_trn)

    del input_images
    del input_labels
    del num_inputs

    assert num_images_trained > 1, "Not Enough Training Data"
    assert num_images_trained == num_labels_trained, "The number of images does not match the number of ground truths for training"
    assert num_images_tested == num_images_tested, "The number of images does not match the number of ground for testing"

    assert collections.Counter(X_val) == collections.Counter(Y_val), "Image Test Data does not match Label Test Data for neural network"
    assert collections.Counter(X_trn) == collections.Counter(Y_trn), "Image Train Data does not match Label Train Data for neural network"

    totalimages = num_images_trained+num_images_tested
    logger.info("{}/{} inputs used for training".format(num_images_trained/totalimages))
    logger.info("{}/{} inputs used for testing".format(num_images_trained/totalimages))

    array_images_trained = []
    array_labels_trained = []

    array_images_tested = []
    array_labels_tested = []

    axis_norm = (0,1)
    n_channel = 1

    for im in range(num_images_tested):
        image = os.path.join(image_dir_test, X_val[im])
        br_image = BioReader(image, max_workers=1)
        im_array = br_image[:,:,0:1,0:1,0:1]
        im_array = im_array.reshape(br_image.shape[:2])
        array_images_tested.append(normalize(im_array,pmin=1,pmax=99.8,axis=axis_norm))

    for lab in range(num_labels_tested):
        label = os.path.join(label_dir_test, Y_val[lab])
        br_label = BioReader(label, max_workers=1)
        lab_array = br_label[:,:,0:1,0:1,0:1]
        lab_array = lab_array.reshape(br_label.shape[:2])
        array_labels_tested.append(fill_label_holes(lab_array))
    
    for im in range(num_images_trained):
        image = os.path.join(image_dir_input, X_trn[im])
        br_image = BioReader(image, max_workers=1)
        if im == 0:
            n_channel = br_image.shape[2]
        im_array = br_image[:,:,0:1,0:1,0:1]
        im_array = im_array.reshape(br_image.shape[:2])
        array_images_trained.append(normalize(im_array,pmin=1,pmax=99.8,axis=axis_norm))
        

    model_dir = 'models'
    if os.path.exists(os.path.join(output_directory, model_dir)):

        model = SplineDist2D(None, name=model_dir, basedir=output_directory)
        logger.info("\n Done Loading Model ...")

        for lab in range(num_labels_trained):
            label = os.path.join(label_dir_input, Y_trn[lab])
            br_label = BioReader(label, max_workers=1)
            lab_array = br_label[:,:,0:1,0:1,0:1]
            lab_array = lab_array.reshape(br_label.shape[:2])
            array_labels_trained.append(fill_label_holes(lab_array))

        modelconfig = model.config.__dict__
        kerasmodel = tf.keras.models.load_model(os.path.join(output_directory, model_dir, 'saved_model'), custom_objects=modelconfig)
        np.testing.assert_allclose(
            kerasmodel.predict(array_images_trained), kerasmodel.predict(array_images_trained))

        kerasmodel.fit_generator(array_images_trained,array_labels_trained, validation_data=(array_images_tested, array_labels_tested), epochs = 1, verbose=1)

        logger.info("\n Done Training Model ...")
    
    else:

        contoursize_max = 0
        logger.info("\n Getting Max Contoursize  ...")

        for lab in range(num_labels_trained):
            label = os.path.join(label_dir_input, Y_trn[lab])
            br_label = BioReader(label, max_workers=1)
            lab_array = br_label[:,:,0:1,0:1,0:1]
            lab_array = lab_array.reshape(br_label.shape[:2])
            array_labels_trained.append(fill_label_holes(lab_array))

            obj_list = np.unique(lab_array)
            obj_list = obj_list[1:]

            for j in range(len(obj_list)):
                mask_temp = lab_array.copy()     
                mask_temp[mask_temp != obj_list[j]] = 0
                mask_temp[mask_temp > 0] = 1

                mask_temp = mask_temp.astype(np.uint8)    
                contours,_ = cv2.findContours(mask_temp, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                areas = [cv2.contourArea(cnt) for cnt in contours]    
                max_ind = np.argmax(areas)
                contour = np.squeeze(contours[max_ind])
                contour = np.reshape(contour,(-1,2))
                contour = np.append(contour,contour[0].reshape((-1,2)),axis=0)
                contoursize_max = max(int(contour.shape[0]), contoursize_max)

        logger.info("Max Contoursize: {}".format(contoursize_max))

        M = 6 # control points
        n_params = M*2

        grid = (2,2)
        
        conf = Config2D (
        n_params        = n_params,
        grid            = grid,
        n_channel_in    = n_channel,
        contoursize_max = contoursize_max,
        )
        conf.use_gpu = gpu

        logger.info("\n Generating phi and grids ... ")
        phi_generator(M, conf.contoursize_max, '.')
        grid_generator(M, conf.train_patch_size, conf.grid, '.')

        model = SplineDist2D(conf, name=model_dir, basedir=output_directory)
        model.train(array_images_trained,array_labels_trained, 
                    validation_data=(array_images_tested, array_labels_tested), 
                    augmenter=augmenter, epochs = 400)
        # model.keras_model.fit(array_images_trained,array_labels_trained, validation_data=(array_images_tested, array_labels_tested), epochs=1)

        logger.info("\n Done Training Model ...")
        model.keras_model.save(os.path.join(output_directory, model_dir, 'saved_model'), save_format='tf')
        logger.info("\n Done Saving Trained Keras Model ...")

    logger.info("\n Getting {} Jaccard Indexes ...".format(num_images_tested))
    create_plots(array_images_tested, array_labels_tested, num_images_tested, output_directory, model)
