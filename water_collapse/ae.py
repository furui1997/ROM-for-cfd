import os
import sys
sys.path.append("/home/ray/.virtualenvs/venv_p3/lib/python3.6/site-packages")
import vtktools
import numpy as np
import matplotlib.pyplot as plt
import datetime
import math
import keras.backend as K
import process_data as Pcd
# import mkdirs
from keras.layers import Input, Dense, LSTM, Dropout
from keras import regularizers
from keras.models import Model, Sequential, load_model
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error,mean_absolute_error
from keras.callbacks import LearningRateScheduler


def variable_value():

	path =  "/home/ray/Downloads/fluidity-master/examples/water_collapse"
	vertify_rate = 0.4
	my_epochs = 200
	encoding_dim = 8
	originalFile = "/home/ray/Downloads/fluidity-master/examples/water_collapse"# original file
	destinationFile = "/home/ray/Documents/data/water_collapse_test" # destination file

	return path, vertify_rate, my_epochs, encoding_dim, originalFile, destinationFile


def ae_vol(vol, my_epochs, encoding_dim):# dim = 3

	input_img = Input(shape=(vol.shape[1], ))
	encoded = Dense(encoding_dim * 32, activation='relu')(input_img)
	encoded = Dense(encoding_dim * 16, activation='relu')(encoded)
	encoded = Dense(encoding_dim * 8, activation='relu')(encoded)
	encoded = Dense(encoding_dim * 2, activation='relu')(encoded)
	encoded = Dense(encoding_dim)(encoded)
	
	# "decoded" is the lossy reconstruction of the input
	decoded = Dense(encoding_dim * 2, activation='relu')(encoded)
	decoded = Dense(encoding_dim * 8, activation='relu')(decoded)
	decoded = Dense(encoding_dim * 16, activation='relu')(decoded)
	decoded = Dense(encoding_dim * 32, activation='relu')(decoded)
	decoded = Dense(vol.shape[1], activation='tanh')(decoded)

	# this model maps an input to its reconstruction
	autoencoder = Model(input_img, decoded)
	encoder = Model(input_img, encoded)
	encoded_input = Input(shape=(encoding_dim, ))

	decoder_layer1 = autoencoder.layers[-1]
	decoder_layer2 = autoencoder.layers[-2]
	decoder_layer3 = autoencoder.layers[-3]
	decoder_layer4 = autoencoder.layers[-4]
	decoder_layer5 = autoencoder.layers[-5]

	# create the decoder model
	decoder = Model(encoded_input, decoder_layer1(decoder_layer2(decoder_layer3(decoder_layer4(decoder_layer5(encoded_input))))))

	# configure model to use a per-pixel binary crossentropy loss, and the Adadelta optimizer
	autoencoder.compile(optimizer='adam', loss = 'mean_absolute_error', metrics = ['accuracy'])

	# train the model
	x_train = vol

	# def scheduler(epoch):
	# 	lr_epochs=5
	# 	lr = K.get_value(autoencoder.optimizer.lr)
	# 	K.set_value(autoencoder.optimizer.lr, lr * (0.01 ** (epoch // lr_epochs)))

	# 	return K.get_value(autoencoder.optimizer.lr)

	# reduce_lr = LearningRateScheduler(scheduler)

	# history = autoencoder.fit(x_train, x_train, epochs=my_epochs, batch_size=128,  callbacks=[reduce_lr], validation_split=0.2)
	history = autoencoder.fit(x_train, x_train, epochs=my_epochs, batch_size=16, validation_split=0.1)

	Pcd.draw_acc_loss(history)

	encoder.save('vol_encoder.h5') 
	autoencoder.save('vol_ae.h5')
	decoder.save('vol_decoder.h5')

	print("ae-model train succeed")  

def train_vol(vol):
	my_epochs, encoding_dim = variable_value()[2],variable_value()[3]

	if not os.path.exists('vol_encoder.h5'):
		ae_vol(vol, my_epochs, encoding_dim)


if __name__=="__main__":  

	path, vertify_rate, my_epochs, encoding_dim, originalFile, destinationFile = variable_value()

	#load data
	print("Data loading...")
	vol = Pcd.get_data(path)
	dataset, vertify = Pcd.train_and_vertify(vol,vertify_rate) 
	print("training_dataset shape:",dataset.shape, "   vertify_dataset shape:", vertify.shape)

	#process data
	scaler = MinMaxScaler()
	scalered_vol = scaler.fit_transform(dataset)

	#train model
	print("Model Building and training... ")
	train_vol(scalered_vol)

	# test
	print("Data testing...")  
	scaler_ver = MinMaxScaler()
	scaler_vertify = scaler_ver.fit_transform(vertify)

	autoencoder = load_model('vol_ae.h5', compile=False)
	outpus  = autoencoder.predict(scaler_vertify)

	scaler_outpus = scaler_ver.inverse_transform(outpus)

	value = mean_squared_error(vertify, scaler_outpus)
	print(value)
	# mkdirs.transform(out_vertify, originalFile, destinationFile)








	