import sys
import numpy as np
# from keras import backend as K
from keras.layers import Input, Dense
from keras.models import Model, load_model
from keras.callbacks import ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
import joblib
from LoadVolData import *
from modelProcessing import *


class DeepAE(object):
	"""DeepAutoencoder Model"""
	def __init__(self):
		super(DeepAE, self).__init__()

	def build_DeepAE_model(self, input_dim, encoding_dim):

		input_img = Input(shape=(input_dim, ))
		encoded = Dense(encoding_dim * 32, activation='relu')(input_img)
		encoded = Dense(encoding_dim * 16, activation='relu')(encoded)
		encoded = Dense(encoding_dim * 8, activation='relu')(encoded)
		encoded = Dense(encoding_dim * 4, activation='relu')(encoded)
		encoded = Dense(encoding_dim * 2, activation='relu')(encoded)
		encoded = Dense(encoding_dim)(encoded)

		# "decoded" is the lossy reconstruction of the input
		decoded = Dense(encoding_dim * 2, activation='relu')(encoded)
		decoded = Dense(encoding_dim * 4, activation='relu')(decoded)
		decoded = Dense(encoding_dim * 8, activation='relu')(decoded)
		decoded = Dense(encoding_dim * 16, activation='relu')(decoded)
		decoded = Dense(encoding_dim * 32, activation='relu')(decoded)
		decoded = Dense(input_dim, activation='sigmoid')(decoded)


		# this model maps an input to its reconstruction
		self.autoencoder = Model(input_img, decoded)
		self.encoder = Model(input_img, encoded)
		encoded_input = Input(shape=(encoding_dim, ))

		decoder_layer1 = self.autoencoder.layers[-1]
		decoder_layer2 = self.autoencoder.layers[-2]
		decoder_layer3 = self.autoencoder.layers[-3]		
		decoder_layer4 = self.autoencoder.layers[-4]
		decoder_layer5 = self.autoencoder.layers[-5]
		decoder_layer6 = self.autoencoder.layers[-6]

		# # create the decoder model
		self.decoder = Model(encoded_input, decoder_layer1(decoder_layer2(decoder_layer3(decoder_layer4(decoder_layer5(decoder_layer6(encoded_input)))))))

		# configure model to use a per-pixel binary crossentropy loss, and the Adadelta optimizer
		self.autoencoder.compile(optimizer='adam', loss = 'mse', metrics = ['accuracy'])

		self.autoencoder.summary()

		
	def train_DeepAE_model(self, x_train, x_test, epochs, batch_size, modelsFolder, encoderFileName, decoderFileName, AEFileName):
		
		self.history_record = self.autoencoder.fit(x_train, x_train, epochs = epochs, batch_size = batch_size, validation_split=0.2)
		# draw_Acc_Loss(self.history_record)		
		save_model(self.encoder, encoderFileName, modelsFolder)
		save_model(self.decoder, decoderFileName, modelsFolder)
		save_model(self.autoencoder, AEFileName, modelsFolder)

		print(" DeepAE model trained successfully")  

		scores = self.autoencoder.evaluate(x_test, x_test, verbose=1)
		print('Test loss:', scores[0], '\nTest accuracy:', scores[1])
	

def AE(path, ori_path, fileName, field_name, di, data_file_name, ae_encoding_dim, ae_epochs, ae_batch_size, modelsFolder,
	encoderFileName, decoderFileName, AEFileName, destinationFolder, newFieldName, Trans_code_name):

	# Load data for AE & DeepAE
	print("Data loading...")
	# load and pre-processing data
	data = LoadmyData()
	Velocity_scaler = data.get_data(ori_path, fileName, field_name, di, data_file_name, modelsFolder)
	random_velocity = data.data_shuffle(Velocity_scaler)
	train, test = data.train_and_test(random_velocity, test_rate = 0.2)

	# train model
	deepAE = DeepAE()
	deepAE.build_DeepAE_model(input_dim = train.shape[1], encoding_dim = ae_encoding_dim)
	deepAE.train_DeepAE_model(train, test,epochs = ae_epochs, 
										batch_size = ae_batch_size, 
										modelsFolder = modelsFolder, 
										encoderFileName = encoderFileName, 
										decoderFileName = decoderFileName, 
										AEFileName = AEFileName)
	print('AE model is trained successfully.')

	# test and restore
	ae = load_model(modelsFolder + "/" + AEFileName, compile=False)
	ae_outputs = ae.predict(Velocity_scaler)

	if di == 2:
		u ,v = np.hsplit(ae_outputs, 2)
		scaler_u = joblib.load(modelsFolder + '/scaler_u.pkl')
		scaler_v = joblib.load(modelsFolder + '/scaler_v.pkl')
		outputs_u = scaler_u.inverse_transform(u)
		outputs_v = scaler_v.inverse_transform(v)
		Velocity_DIM = np.dstack((outputs_u, outputs_v))
	elif di == 1:
		scaler = joblib.load(modelsFolder + '/scaler_1d.pkl')
		outputs_u = scaler.inverse_transform(ae_outputs)
	print('AE train successfully.\n The shape of \'DeepAE outputs\' is ',Velocity_DIM.shape)
	transform_vector(Velocity_DIM, Velocity_DIM.shape[0], ori_path, destinationFolder, fileName, newFieldName)

	# generate the code for forecasting training
	AE_encoder = load_model(modelsFolder + "/" + encoderFileName, compile=False)
	AEcode = AE_encoder.predict(Velocity_scaler)
	np.save(path + Trans_code_name, AEcode)
	print('The shape of \'AE_Code for Predict\' is ',AEcode.shape)


# if __name__=="__main__":  

# 	# ROM train
# 	path = '../../datasets/flow_past_cylinder/'	
# 	ori_path = path + 'Rui_2002'
# 	fileName = '/circle-2d-drag_'
# 	field_name = 'Velocity'
# 	di = 2
# 	data_file_name = '../Velocity_U_V.npy'
# 	ae_encoding_dim = 8
# 	ae_epochs = 300
# 	ae_batch_size = 64
# 	modelsFolder = './saved_models'
# 	encoderFileName = 'AE_vel_encoder_8.h5'
# 	decoderFileName = 'AE_vel_decoder_8.h5'
# 	AEFileName = 'AE_vel_8.h5'
# 	destinationFolder = path +'AE_outputs'
# 	newFieldName = 'Velocity_dim_8'
# 	Trans_code_name = 'Transformer_code_8.npy'

# 	AE(path, ori_path, fileName, field_name, di, data_file_name, ae_encoding_dim, ae_epochs, ae_batch_size, modelsFolder,
# 	encoderFileName, decoderFileName, AEFileName, destinationFolder, newFieldName, Trans_code_name)