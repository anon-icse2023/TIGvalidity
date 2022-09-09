import glob
import math
import csv
import ntpath

import numpy as np
import random
from tensorflow.keras import backend as K
import tensorflow as tf
from imagenet.anomaly_detectors.utils import deprocess_image_tf

img_dim = 128
img_chn = 3


# Logic for calculating reconstruction probability
def reconstruction_probability(dec, z_mean, z_log_var, X):
    """
    :param decoder: decoder model
    :param z_mean: encoder predicted mean value
    :param z_log_var: encoder predicted sigma square value
    :param X: input data
    :return: reconstruction probability of input
            calculated over L samples from z_mean and z_log_var distribution
    """
    sampled_zs = sampling([z_mean, z_log_var])
    reconstruction = dec(sampled_zs)

    reconstructed_prob = tf.reduce_mean(
        tf.reduce_sum(
            tf.keras.losses.mean_squared_error(X, reconstruction), axis=(-1, -2, -3)
            )
    )

    #print(reconstructed_prob)
    return reconstructed_prob


# Calculates and returns probability density of test input
def calculate_density(x_target_orig, enc, dec):
    x_target = np.clip(x_target_orig, 0, 1)
    z_mean, z_log_var, _ = enc(x_target)
    reconstructed_prob_x_target = reconstruction_probability(dec, z_mean, z_log_var, x_target)
    return reconstructed_prob_x_target

def sampling(args):
    """Reparameterization trick by sampling from an isotropic unit Gaussian.
    # Arguments
        args (tensor): mean and log of variance of Q(z|X)
    # Returns
        z (tensor): sampled latent vector
    """
    z_mean, z_log_var = args
    batch = K.shape(z_mean)[0]
    dim = K.int_shape(z_mean)[1]
    # by default, random_normal has mean = 0 and std = 1.0
    epsilon = K.random_normal(shape=(batch, dim))
    return z_mean + K.exp(0.5 * z_log_var) * epsilon


def preprocess_sample(batch):
    batch = deprocess_image_tf(batch)
    batch = tf.image.resize(batch, [img_dim, img_dim]).numpy()
    batch = batch / 255.
    batch = np.expand_dims(batch, 0)
    return batch


def compute_valid(sample, encoder, decoder, tshd):
    #fp = []
    #tn = []
    #for batch in anomaly_test:
    batch = preprocess_sample(sample)
    #batch = np.expand_dims(batch, 0)
    rec_loss = calculate_density(batch, encoder, decoder)
    #print(rec_loss)
    if rec_loss > tshd or math.isnan(rec_loss):
        distr = 'ood'
    else:
        distr = 'id'
    return distr, rec_loss.numpy()


def main():
    csv_file = r"losses/ood_analysis_stocco_all_classes.csv"
    # multiclass
    # VAE density threshold for classifying invalid inputs
    vae_threshold = 299.3629597975091
    VAE = "imagenet_selforacle_long"

    decoder = tf.keras.models.load_model("trained/" + VAE + "/decoder", compile=False)
    encoder = tf.keras.models.load_model("trained/" + VAE + "/encoder", compile=False)

    RESULTS_PATH = r"../../../imagenet_inputs/"

    with open(csv_file, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['TOOL', 'SAMPLE', 'ID/OOD', 'loss'])

        print("DLFuzz")
        DLF_FOLDER = RESULTS_PATH+"imagenet_dlf/*.npy"
        filelist = [f for f in glob.glob(DLF_FOLDER)]
        print("found samples:" + str(len(filelist)))
        # samples = [np.load(sample) for sample in filelist]
        for sample in filelist:
            s = np.load(sample)
            distr, loss = compute_valid(s, encoder, decoder, vae_threshold)
            sample_name = ntpath.split(sample)[-1]
            writer.writerow(['DLF', sample_name, distr, loss])

        print("DeepXplore")
        DX_FOLDER = RESULTS_PATH+"imagenet_dx/*.npy"
        filelist = [f for f in glob.glob(DX_FOLDER)]
        print("found samples:" + str(len(filelist)))
        # samples = [np.load(sample) for sample in filelist]
        for sample in filelist:
            s = np.load(sample)
            distr, loss = compute_valid(s, encoder, decoder, vae_threshold)
            sample_name = ntpath.split(sample)[-1]
            writer.writerow(['DX', sample_name, distr, loss])

        print("Oxford")
        OX_FOLDER = RESULTS_PATH+"imagenet_ox/*.npy"
        filelist = [f for f in glob.glob(OX_FOLDER)]
        print("found samples:" + str(len(filelist)))
        # samples = [np.load(sample) for sample in filelist]
        for sample in filelist:
            s = np.load(sample)
            distr, loss = compute_valid(s, encoder, decoder, vae_threshold)
            sample_name = ntpath.split(sample)[-1]
            writer.writerow(['OX', sample_name, distr, loss])

        print("Sinvad")
        SV_FOLDER = RESULTS_PATH+"imagenet_sv/*.npy"
        filelist = [f for f in glob.glob(SV_FOLDER)]
        print("found samples:" + str(len(filelist)))
        # samples = [np.load(sample) for sample in filelist]
        for sample in filelist:
            s = np.load(sample)
            distr, loss = compute_valid(s, encoder, decoder, vae_threshold)
            sample_name = ntpath.split(sample)[-1]
            writer.writerow(['SV', sample_name, distr, loss])


if __name__ == "__main__":
    main()