from archconvnets.unsupervised.cudnn_module.cudnn_module import *
import time
import numpy as np
from scipy.io import savemat, loadmat
import copy
from scipy.stats import zscore
import random
import gnumpy as gpu

#kernprof -l bp_movies_nat.py
#python -m line_profiler bp_movies_nat.py.lprof  > p
#@profile
#def sf():

N_C = 999

F1_scale = 0.01 # std of init normal distribution
F2_scale = 0.01
F3_scale = 0.01
FL_scale = 0.01
CEC_SCALE = 0.001
FCF_SCALE = 0.0001

EPS_E = 2#3
EPS = 1*10**(-EPS_E)

N_IMGS = 100 # batch size
IMG_SZ_CROP = 32 # input image size (px)
IMG_SZ = 34 # input image size (px)
PAD = 2

GPU_UNS = 1

N = 32
n1 = N # L1 filters
n2 = N# ...
n3 = N
n4 = N+1

s3 = 3 # L1 filter size (px)
s2 = 5 # ...
s1 = 5

file_name = '/home/darren/F1_' + str(N_C) + '_' + str(EPS_E) + 'eps_' + str(N) + 'N_cifar.mat'

max_output_sz3  = 5

np.random.seed(6166)
F1 = np.single(np.random.normal(scale=F1_scale, size=(n1, 3, s1, s1)))
F2 = np.single(np.random.normal(scale=F2_scale, size=(n2, n1, s2, s2)))
F3 = np.single(np.random.normal(scale=F3_scale, size=(n3, n2, s3, s3)))

FCm = np.single(np.random.normal(scale=FL_scale, size=(n4, n3, max_output_sz3, max_output_sz3)))
FCi = np.single(np.random.normal(scale=FL_scale, size=(n4, n3, max_output_sz3, max_output_sz3)))
FCo = np.single(np.random.normal(scale=FL_scale, size=(n4, n3, max_output_sz3, max_output_sz3)))
FCf = np.single(np.random.normal(scale=FCF_SCALE, size=(n4, n3, max_output_sz3, max_output_sz3)))
CEC = np.single(np.random.normal(scale=CEC_SCALE, size=(N_IMGS, n4)))
CEC2 = np.single(np.random.normal(scale=CEC_SCALE, size=(10000, n4)))

FL = np.single(np.random.normal(scale=FL_scale, size=(10, n4)))

imgs_mean = np.load('/home/darren/cifar-10-py-colmajor/batches.meta')['data_mean']


# gpu buffer indices
MAX_OUTPUT1 = 0; DF2_DATA = 1; CONV_OUTPUT1 = 2; DPOOL1 = 3
F1_IND = 4; IMGS_PAD = 5; DF1 = 6; F2_IND = 11
D_UNPOOL2 = 12;F3_IND = 13; MAX_OUTPUT2 = 14; MAX_OUTPUT3 = 15
CONV_OUTPUT1 = 19; CONV_OUTPUT2 = 20; CONV_OUTPUT3 = 21
DF2 = 25; DPOOL2 = 26; DF3_DATA = 27; DPOOL3 = 28; DF3 = 29; FL_PRED = 30;
FL_IND = 31; PRED = 32; DFL = 33

t_start = time.time()

##################
# load test imgs into buffers
z2 = np.load('/home/darren/cifar-10-py-colmajor/data_batch_' + str(6))
x = z2['data'] - imgs_mean
x = x.reshape((3, 32, 32, 10000))

labels_test = np.asarray(z2['labels'])
l = np.zeros((10000, 10),dtype='int')
l[np.arange(10000),np.asarray(z2['labels']).astype(int)] = 1
Y_test = np.single(l.T)

imgs_pad_test = np.zeros((3, IMG_SZ, IMG_SZ, 10000),dtype='single')
imgs_pad_test[:,PAD:PAD+IMG_SZ_CROP,PAD:PAD+IMG_SZ_CROP] = x
imgs_pad_test = np.ascontiguousarray(imgs_pad_test.transpose((3,0,1,2)))

##################
# load cifar train imgs into buffers
z2 = np.load('/home/darren/cifar-10-py-colmajor/data_batch_' + str(1))
for batch in range(2,6):
	y = np.load('/home/darren/cifar-10-py-colmajor/data_batch_' + str(batch))
	z2['data'] = np.concatenate((z2['data'], y['data']), axis=1)
	z2['labels'] = np.concatenate((z2['labels'], y['labels']))
	
x = z2['data'] - imgs_mean
x = x.reshape((3, 32, 32, 50000))

labels_cifar = np.asarray(z2['labels'])
l = np.zeros((50000, 10),dtype='uint8')
l[np.arange(50000),np.asarray(z2['labels']).astype(int)] = 1
Y_cifar = l.T

imgs_pad_cifar = np.zeros((3, IMG_SZ, IMG_SZ, 50000),dtype='single')
imgs_pad_cifar[:,PAD:PAD+IMG_SZ_CROP,PAD:PAD+IMG_SZ_CROP] = x
imgs_pad_cifar = np.ascontiguousarray(imgs_pad_cifar.transpose((3,0,1,2)))

epoch = 0
err = []
class_err = []

global_step = 0
while True:
	for s in range(500):
		if s % 100 == 0:
			t_mcc = time.time()
			###############################################
			# test imgs (cifar)
			conv_output1 = conv(F1, imgs_pad_test, gpu=GPU_UNS)
			max_output1 = max_pool_cudnn(conv_output1, gpu=GPU_UNS)
			conv_output2 = conv(F2, max_output1, gpu=GPU_UNS)
			max_output2 = max_pool_cudnn(conv_output2, gpu=GPU_UNS)
			conv_output3 = conv(F3, max_output2, gpu=GPU_UNS)
			max_output3 = max_pool_cudnn(conv_output3, gpu=GPU_UNS)
			
			FCm_output = np.einsum(FCm, range(4), max_output3, [4, 1,2,3], [4, 0])
			FCi_output = np.einsum(FCi, range(4), max_output3, [4, 1,2,3], [4, 0])
			FCo_output = np.einsum(FCo, range(4), max_output3, [4, 1,2,3], [4, 0])
			FCf_output = np.einsum(FCf, range(4), max_output3, [4, 1,2,3], [4, 0])
			
			FC_output = FCo_output*(CEC2*FCf_output + FCi_output*FCm_output)
			
			CEC2 = CEC2*FCf_output + FCi_output*FCm_output
			
			pred = np.einsum(FL, [0,1], FC_output, [2, 1], [2,0])
			
			err.append(np.mean((pred - Y_test.T)**2))
			class_err.append(1-(np.argmax(pred.T,axis=0) == np.asarray(np.squeeze(labels_test))).mean())
			
			print epoch, batch, 'class:', class_err[-1], 'err:', err[-1], ' F1:', np.sum(np.abs(F1)), time.time() - t_mcc, time.time() - t_start, file_name
			print np.min(CEC2), np.max(CEC2), np.min(CEC), np.max(CEC)
			
			savemat(file_name, {'F1':F1, 'epoch':epoch, 'class_err':class_err, 'err':err,'F2':F2,'F3':F3,'EPS':EPS})
			
			t_start = time.time()
		
		set_buffer(imgs_pad_cifar[s*N_IMGS:(s+1)*N_IMGS], IMGS_PAD, gpu=GPU_UNS)
		
		set_buffer(F1, F1_IND, filter_flag=1, gpu=GPU_UNS)
		set_buffer(F2, F2_IND, filter_flag=1, gpu=GPU_UNS)
		set_buffer(F3, F3_IND, filter_flag=1, gpu=GPU_UNS)
		
		# forward pass imgs
		conv_buffers(F1_IND, IMGS_PAD, CONV_OUTPUT1, gpu=GPU_UNS)
		max_pool_cudnn_buffers(CONV_OUTPUT1, MAX_OUTPUT1, gpu=GPU_UNS)
		conv_buffers(F2_IND, MAX_OUTPUT1, CONV_OUTPUT2, gpu=GPU_UNS)
		max_pool_cudnn_buffers(CONV_OUTPUT2, MAX_OUTPUT2, gpu=GPU_UNS)
		conv_buffers(F3_IND, MAX_OUTPUT2, CONV_OUTPUT3, gpu=GPU_UNS)
		max_pool_cudnn_buffers(CONV_OUTPUT3, MAX_OUTPUT3, gpu=GPU_UNS)
		
		max_output3 = return_buffer(MAX_OUTPUT3, gpu=GPU_UNS)
		FCm_output = np.einsum(FCm, range(4), max_output3, [4, 1,2,3], [4, 0])
		FCi_output = np.einsum(FCi, range(4), max_output3, [4, 1,2,3], [4, 0])
		FCo_output = np.einsum(FCo, range(4), max_output3, [4, 1,2,3], [4, 0])
		FCf_output = np.einsum(FCf, range(4), max_output3, [4, 1,2,3], [4, 0])
		
		FC_output = FCo_output*(CEC*FCf_output + FCi_output*FCm_output)
		pred = np.einsum(FL, [0,1], FC_output, [2, 1], [2,0])
		
		Ys = np.ascontiguousarray(Y_cifar[:,s*N_IMGS:(s+1)*N_IMGS])
		
		######## gradients:
		pred_m_Y = pred - Ys.T
		
		FL_pred = np.einsum(FL, [0,1], pred_m_Y, [2,0], [2,1])
		
		FLFC_pred = np.einsum(FL_pred*(CEC*FCf_output + FCi_output*FCm_output), [0,1], FCo, [1,2,3,4], [0, 2,3,4])
		FLFC_pred += np.einsum(FCo_output*(CEC*FL_pred), [0,1], FCf, [1,2,3,4], [0, 2,3,4])
		FLFC_pred += np.einsum(FCo_output*(FL_pred*FCm_output), [0,1], FCi, [1,2,3,4], [0, 2,3,4])
		FLFC_pred += np.einsum(FCo_output*(FL_pred*FCi_output), [0,1], FCm, [1,2,3,4], [0, 2,3,4])
		
		set_buffer(FLFC_pred, FL_PRED, gpu=GPU_UNS) # summing across categories
		
		###########
		max_pool_back_cudnn_buffers(MAX_OUTPUT3, FL_PRED, CONV_OUTPUT3, DPOOL3, gpu=GPU_UNS)
		conv_dfilter_buffers(F3_IND, MAX_OUTPUT2, DPOOL3, DF3, stream=3, gpu=GPU_UNS)
		conv_ddata_buffers(F3_IND, MAX_OUTPUT2, DPOOL3, DF3_DATA, gpu=GPU_UNS)
		max_pool_back_cudnn_buffers(MAX_OUTPUT2, DF3_DATA, CONV_OUTPUT2, DPOOL2, gpu=GPU_UNS)
		conv_ddata_buffers(F2_IND, MAX_OUTPUT1, DPOOL2, DF2_DATA, gpu=GPU_UNS)
		conv_dfilter_buffers(F2_IND, MAX_OUTPUT1, DPOOL2, DF2, stream=2, gpu=GPU_UNS)
		max_pool_back_cudnn_buffers(MAX_OUTPUT1, DF2_DATA, CONV_OUTPUT1, DPOOL1, gpu=GPU_UNS)
		conv_dfilter_buffers(F1_IND, IMGS_PAD, DPOOL1, DF1, stream=1, gpu=GPU_UNS)

		###
		dFL = np.dot(pred_m_Y.T, FC_output)
		dFCf = np.einsum(max_output3, range(4), FL_pred*FCo_output*CEC, [0,4], [4,1,2,3])
		dFCo = np.einsum(max_output3, range(4), FL_pred*(CEC*FCf_output + FCi_output*FCm_output), [0,4], [4,1,2,3])
		dFCm = np.einsum(max_output3, range(4), FCi_output*FL_pred*FCo_output, [0,4], [4,1,2,3])
		dFCi = np.einsum(max_output3, range(4), FCm_output*FL_pred*FCo_output, [0,4], [4,1,2,3])
		
		dF3 = return_buffer(DF3, stream=3, gpu=GPU_UNS)
		dF2 = return_buffer(DF2, stream=2, gpu=GPU_UNS)
		dF1 = return_buffer(DF1, stream=1, gpu=GPU_UNS)
		
		F1 -= dF1*EPS / N_IMGS
		F2 -= dF2*EPS / N_IMGS
		F3 -= dF3*EPS / N_IMGS
		
		FCf -= dFCf*EPS / N_IMGS
		FCo -= dFCo*EPS / N_IMGS
		FCm -= dFCm*EPS / N_IMGS
		FCi -= dFCi*EPS / N_IMGS
		
		FL -= dFL*EPS / N_IMGS
		
		CEC = CEC*FCf_output + FCi_output*FCm_output
		
		global_step += 1
		
	epoch += 1
sf()
