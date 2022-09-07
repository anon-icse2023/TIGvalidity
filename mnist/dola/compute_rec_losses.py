import numpy as np
from tensorflow.keras import backend as K
import tensorflow as tf
from tensorflow.keras.datasets import mnist, fashion_mnist


image_size = 28
image_chn = 1
input_shape = (image_size, image_size, image_chn)


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
    reconstructed_prob = np.zeros((X.shape[0],), dtype='float32')
    L = 1
    for l in range(L):
        sampled_zs = sampling([z_mean, z_log_var])
        mu_hat, log_sigma_hat = dec(sampled_zs)
        log_sigma_hat = np.float64(log_sigma_hat)
        sigma_hat = np.exp(log_sigma_hat) + 0.00001

        loss_a = np.log(2 * np.pi * sigma_hat)
        loss_m = np.square(mu_hat - X) / sigma_hat

        reconstructed_prob += -0.5 * np.sum(loss_a + loss_m, axis=1)
    reconstructed_prob /= L
    print(reconstructed_prob)
    return reconstructed_prob


# Calculates and returns probability density of test input
def calculate_density(x_target_orig, enc, dec):
    x_target_orig = np.clip(x_target_orig, 0, 1)
    x_target = np.reshape(x_target_orig, (-1, 28*28))
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


def main():
    #VAE = "original_dola"
    ROOT_VAE = "mnist_vae_dola"
    VAE_TYPE = "all_classes"

    VAE = ROOT_VAE+"_"+VAE_TYPE
    decoder = tf.keras.models.load_model("trained/"+VAE+"/decoder", compile=False)
    encoder = tf.keras.models.load_model("trained/"+VAE+"/encoder", compile=False)

    DATASET = "FMNIST"
    #DATASET = "MNIST"
    if DATASET=="MNIST":
        (x_train, y_train), (x_test, y_test) = mnist.load_data()
    else:
        (x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
    #x_train = np.reshape(x_train, [-1, image_size, image_size, 1])
    x_test = np.reshape(x_test, [-1, image_size, image_size, 1])
    #x_train = x_train.astype('float32') / 255
    x_test = x_test.astype('float32') / 255
    data = x_test

    rec_losses = []
    for batch in data:
        batch = np.expand_dims(batch,0)
        rec_loss = calculate_density(batch, encoder, decoder)
        rec_losses.append(rec_loss)

    rec_loss_summary = np.vstack(rec_losses)
    np.save('dola_rec_losses_'+DATASET+'_'+VAE_TYPE+'.npy', rec_loss_summary)


if __name__ == "__main__":
    main()
