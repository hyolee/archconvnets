import random
import time
import numpy as np
from archconvnets.unsupervised.cudnn_module import cudnn_module as cm
import archconvnets.unsupervised.sigma31_layers.sigma31_layers as sigma31_layers
from archconvnets.unsupervised.sigma31_layers.sigma31_layers import max_pool_locs
from scipy.io import savemat, loadmat
from scipy.stats import zscore

N_INDS_KEEP = 10000

conv_block_cuda = cm.conv
F1_scale = 0.01 # std of init normal distribution
F2_scale = 0.01
F3_scale = 0.01
FL_scale = 0.3

POOL_SZ = 3
POOL_STRIDE = 2
STRIDE1 = 1 # layer 1 stride
N_IMGS = 256 # batch size
IMG_SZ_CROP = 28 # input image size (px)
IMG_SZ = 32 # input image size (px)
img_train_offset = 2
PAD = 2

N = 8
n1 = N # L1 filters
n2 = N
n3 = N

s1 = 5
s2 = 5
s3 = 3

N_C = 10 # number of categories

output_sz1 = len(range(0, IMG_SZ - s1 + 1, STRIDE1))
max_output_sz1  = len(range(0, output_sz1-POOL_SZ, POOL_STRIDE)) + 2*PAD

output_sz2 = max_output_sz1 - s2 + 1
max_output_sz2  = len(range(0, output_sz2-POOL_SZ, POOL_STRIDE)) + 2*PAD

inds_keep = range(n1*3*s1*s1*n2*s2*s2*n3*s3*s3*2*2)
random.seed(666)
random.shuffle(inds_keep)
inds_keep = inds_keep[:N_INDS_KEEP]

s31 = np.zeros((N_IMGS, N_INDS_KEEP), dtype='single')

np.random.seed(6666)
F1 = np.single(np.random.normal(scale=F1_scale, size=(n1, 3, s1, s1)))
F2 = np.single(np.random.normal(scale=F2_scale, size=(n2, n1, s2, s2)))
F3 = np.single(np.random.normal(scale=F3_scale, size=(n3, n2, s3, s3)))

F1 = zscore(F1,axis=None)/500
F2 = zscore(F2,axis=None)/500
F3 = zscore(F3,axis=None)/500

imgs_mean = np.load('/home/darren/cifar-10-py-colmajor/batches.meta')['data_mean']
z = np.load('/home/darren/cifar-10-py-colmajor/data_batch_6')

################### compute train err
# load imgs
x = z['data'] - imgs_mean
x = x.reshape((3, 32, 32, 10000))
x = x[:,:,:,:N_IMGS]

labels = np.asarray(z['labels'])[:N_IMGS].astype(int)

imgs_pad = np.zeros((3, IMG_SZ, IMG_SZ, N_IMGS),dtype='single')
imgs_pad[:,PAD:PAD+IMG_SZ_CROP,PAD:PAD+IMG_SZ_CROP] = x[:,img_train_offset:img_train_offset+IMG_SZ_CROP,img_train_offset:img_train_offset+IMG_SZ_CROP]
imgs_pad = np.ascontiguousarray(imgs_pad.transpose((3,0,1,2)))

# forward pass
t_forward_start = time.time()
conv_output1 = conv_block_cuda(F1, imgs_pad)
max_output1t, output_switches1_x, output_switches1_y = max_pool_locs(np.single(conv_output1))

max_output1 = np.zeros((N_IMGS, n1, max_output_sz1, max_output_sz1),dtype='single')
max_output1[:,:,PAD:max_output_sz1-PAD,PAD:max_output_sz1-PAD] = max_output1t

conv_output2 = conv_block_cuda(F2, max_output1)
max_output2t, output_switches2_x, output_switches2_y = max_pool_locs(np.single(conv_output2), PAD=2)

max_output2 = np.zeros((N_IMGS, n2, max_output_sz2, max_output_sz2),dtype='single')
max_output2[:,:,PAD:max_output_sz2-PAD,PAD:max_output_sz2-PAD] = max_output2t

conv_output3 = conv_block_cuda(F3, max_output2)
max_output3t, output_switches3_x, output_switches3_y = max_pool_locs(np.single(conv_output3), PAD=2)

output_switches2_x -= PAD
output_switches2_y -= PAD

output_switches3_x -= PAD
output_switches3_y -= PAD

print time.time() - t_forward_start

for img in range(N_IMGS):
	t_start = time.time()
	s31[img] = sigma31_layers.s31_full_gpu(output_switches3_x[img][np.newaxis], output_switches3_y[img][np.newaxis], output_switches2_x[img][np.newaxis], output_switches2_y[img][np.newaxis], output_switches1_x[img][np.newaxis], output_switches1_y[img][np.newaxis], s1, s2, s3, labels[img][np.newaxis], imgs_pad[img][np.newaxis], N_C, warn=False)[labels[img]].ravel()[inds_keep]
	print img, time.time() - t_start

np.save('/home/darren/sigma31_8_single_imgs_labels.npy', labels)
np.save('/home/darren/sigma31_8_single_imgs.npy', s31)


