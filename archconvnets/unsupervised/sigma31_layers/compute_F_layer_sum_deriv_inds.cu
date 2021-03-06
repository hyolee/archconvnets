//N_C * n1 *3 * s1 * s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3
#define P_IND(A,B)((B) + (A)*(n_inds))

#define F1S_IND(A, B, C, D)((D) + (C)*s1 + (B)*s1*s1 + (A)*s1*s1*3)
#define F2S_IND(A, B, C, D)((D) + (C)*s2 + (B)*s2*s2 + (A)*s2*s2*n1)
#define F3S_IND(A, B, C, D)((D) + (C)*s3 + (B)*s3*s3 + (A)*s3*s3*n2)
#define FLS_IND(A, B, C, D)((D) + (C)*max_output_sz3 + (B)*max_output_sz3*max_output_sz3 + (A)*max_output_sz3*max_output_sz3*n3)

// layer_ind defines which layer to keep
static PyObject *compute_F_layer_sum_deriv_inds(PyObject *self, PyObject *args){
	PyArrayObject *F1_in, *F2_in, *F3_in, *FL_in, *inds_in, *sigma11_in;
	PyArrayObject *FL321_in, *F_sum_in, *F_partial_in; // F_partial: FL321 sans the layer the deriv. is take wrt
	
	int dims[14];
	int layer_ind;
	IND_DTYPE *inds;
	float *FL321, *F_partial, *F_sum, *sigma11;
	
	if (!PyArg_ParseTuple(args, "O!O!O!O!O!O!O!O!i",  &PyArray_Type, &FL321_in, &PyArray_Type, &F_partial_in, &PyArray_Type, &sigma11_in, 
		&PyArray_Type, &F1_in, &PyArray_Type, &F2_in, &PyArray_Type, &F3_in, &PyArray_Type, &FL_in, 
		&PyArray_Type, &inds_in, &layer_ind)) return NULL;

	if (NULL == FL321_in || NULL == F_partial_in || NULL == sigma11_in ||
		NULL == F1_in || NULL == F2_in || NULL == F3_in || NULL == FL_in)  return NULL;

	inds = (IND_DTYPE *) inds_in -> data;
	FL321 = (float *) FL321_in -> data;
	F_partial = (float *) F_partial_in -> data;
	sigma11 = (float *) sigma11_in -> data;
	
	IND_DTYPE N_C = PyArray_DIM(FL_in, 0);
	IND_DTYPE max_output_sz3 = PyArray_DIM(FL_in, 2);
	IND_DTYPE n3 = PyArray_DIM(F3_in, 0);
	IND_DTYPE n2 = PyArray_DIM(F2_in, 0);
	IND_DTYPE n1 = PyArray_DIM(F1_in, 0);
	IND_DTYPE s1 = PyArray_DIM(F1_in, 2);
	IND_DTYPE s2 = PyArray_DIM(F2_in, 2);
	IND_DTYPE s3 = PyArray_DIM(F3_in, 2);
	IND_DTYPE n_inds = PyArray_DIM(inds_in, 0);
	IND_DTYPE n0 = 3;
	
	if(layer_ind == 1){ // F1 inds
		dims[0] = n1;
		dims[1] = 3;
		dims[2] = s1;
		dims[3] = s1;
	}else if(layer_ind == 2){
		dims[0] = n2;
		dims[1] = n1;
		dims[2] = s2;
		dims[3] = s2;
	}else if(layer_ind == 3){
		dims[0] = n3;
		dims[1] = n2;
		dims[2] = s3;
		dims[3] = s3;
	}else if(layer_ind == 4){
		dims[0] = N_C;
		dims[1] = n3;
		dims[2] = max_output_sz3;
		dims[3] = max_output_sz3;
	}else{
		printf("layer index (%i) not supported\n", layer_ind);
		return NULL;
	}
	
	F_sum_in = (PyArrayObject *) PyArray_FromDims(4, dims, NPY_FLOAT);
	F_sum = (float *) F_sum_in -> data;
	
	int f1_i, channel_i, a1_x_i, a1_y_i, f2_i, a2_x_i, a2_y_i, f3_i, a3_x_i, a3_y_i, z1_i, z2_i, cat, img, ind_i, ind_j;
	int f1_j, channel_j, a1_x_j, a1_y_j, f2_j, a2_x_j, a2_y_j, f3_j, a3_x_j, a3_y_j, z1_j, z2_j;
	
	IND_DTYPE r;
	
	IND_DTYPE max_output_sz3_max_output_sz3_s3_s3_n3_s2_s2_n2_s1_s1_3_n1 = max_output_sz3*max_output_sz3*s3*s3*n3*s2*s2*n2*s1*s1*3*n1;
	IND_DTYPE max_output_sz3_max_output_sz3_s3_s3_n3_s2_s2_n2_s1_s1_3 = max_output_sz3*max_output_sz3*s3*s3*n3*s2*s2*n2*s1*s1*3;
	IND_DTYPE max_output_sz3_max_output_sz3_s3_s3_n3_s2_s2_n2_s1_s1 = max_output_sz3*max_output_sz3*s3*s3*n3*s2*s2*n2*s1*s1;
	IND_DTYPE max_output_sz3_max_output_sz3_s3_s3_n3_s2_s2_n2_s1 = max_output_sz3*max_output_sz3*s3*s3*n3*s2*s2*n2*s1;
	IND_DTYPE max_output_sz3_max_output_sz3_s3_s3_n3_s2_s2_n2 = max_output_sz3*max_output_sz3*s3*s3*n3*s2*s2*n2;
	IND_DTYPE max_output_sz3_max_output_sz3_s3_s3_n3_s2_s2 = max_output_sz3*max_output_sz3*s3*s3*n3*s2*s2;
	IND_DTYPE max_output_sz3_max_output_sz3_s3_s3_n3_s2 = max_output_sz3*max_output_sz3*s3*s3*n3*s2;
	IND_DTYPE max_output_sz3_max_output_sz3_s3_s3_n3 = max_output_sz3*max_output_sz3*s3*s3*n3;
	IND_DTYPE max_output_sz3_max_output_sz3_s3_s3 = max_output_sz3*max_output_sz3*s3*s3;
	IND_DTYPE max_output_sz3_max_output_sz3_s3 = max_output_sz3*max_output_sz3*s3;
	IND_DTYPE max_output_sz3_max_output_sz3 = max_output_sz3*max_output_sz3;
	
	IND_DTYPE max_output_sz3_max_output_sz3_n3 = max_output_sz3*max_output_sz3*n3;
	
	IND_DTYPE F_sum_ind;
	char matching;
	
	for(ind_i = 0; ind_i < n_inds; ind_i++){
		////////////////////////////////////////////// unravel inds
		
		f1_i = inds[ind_i] / (3 * s1 * s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		r = inds[ind_i] % (3 * s1 * s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		
		channel_i = r / (s1 * s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		r = r % (s1 * s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		
		a1_x_i = r / (s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		r = r % (s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		
		a1_y_i = r / (n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		r = r % (n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		
		f2_i = r / (s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		r = r % (s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		
		a2_x_i = r / (s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		r = r % (s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		
		a2_y_i = r / (n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		r = r % (n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
		
		f3_i = r / (s3 * s3 * max_output_sz3 * max_output_sz3);
		r = r % (s3 * s3 * max_output_sz3 * max_output_sz3);
		
		a3_x_i = r / (s3 * max_output_sz3 * max_output_sz3);
		r = r % (s3 * max_output_sz3 * max_output_sz3);
		
		a3_y_i = r / (max_output_sz3 * max_output_sz3);
		r = r % (max_output_sz3 * max_output_sz3);
		
		z1_i = r / (max_output_sz3);
		z2_i = r % (max_output_sz3);
		
		if(layer_ind == 1){
			F_sum_ind = F1S_IND(f1_i, channel_i, a1_x_i, a1_y_i);
		}else if(layer_ind == 2){
			F_sum_ind = F2S_IND(f2_i, f1_i, a2_x_i, a2_y_i);
		}else if(layer_ind == 3){
			F_sum_ind = F3S_IND(f3_i, f2_i, a3_x_i, a3_y_i);
		}
		
		for(ind_j = 0; ind_j < n_inds; ind_j++){
			////////////////////////////////////////////// unravel inds		
			f1_j = inds[ind_j] / (3 * s1 * s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			r = inds[ind_j] % (3 * s1 * s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			
			channel_j = r / (s1 * s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			r = r % (s1 * s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			
			a1_x_j = r / (s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			r = r % (s1 * n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			
			a1_y_j = r / (n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			r = r % (n2 * s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			
			f2_j = r / (s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			r = r % (s2 * s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			
			a2_x_j = r / (s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			r = r % (s2 * n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			
			a2_y_j = r / (n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			r = r % (n3 * s3 * s3 * max_output_sz3 * max_output_sz3);
			
			f3_j = r / (s3 * s3 * max_output_sz3 * max_output_sz3);
			r = r % (s3 * s3 * max_output_sz3 * max_output_sz3);
			
			a3_x_j = r / (s3 * max_output_sz3 * max_output_sz3);
			r = r % (s3 * max_output_sz3 * max_output_sz3);
			
			a3_y_j = r / (max_output_sz3 * max_output_sz3);
			r = r % (max_output_sz3 * max_output_sz3);
			
			z1_j = r / (max_output_sz3);
			z2_j = r % (max_output_sz3);
			
			matching = 0;
			if(layer_ind == 1 && f1_i == f1_j && channel_i == channel_j && a1_x_i == a1_x_j && a1_y_i == a1_y_j){
				matching = 1;
			}else if(layer_ind == 2 && f2_i == f2_j && f1_i == f1_j && a2_x_i == a2_x_j && a2_y_i == a2_y_j){
				matching = 1;
			}else if(layer_ind == 3 && f3_i == f3_j && f2_i == f2_j && a3_x_i == a3_x_j && a3_y_i == a3_y_j){
				matching = 1;
			}else if(layer_ind == 4 && f3_i == f3_j && z1_i == z1_j && z2_i == z2_j){
				matching = 1;
			}
			
			if(matching == 1){
				for(cat = 0; cat < N_C; cat++){
					if(layer_ind == 4)
						F_sum_ind = FLS_IND(cat, f3_i, z1_i, z2_i);
					F_sum[F_sum_ind] += FL321[P_IND(cat, ind_i)] * F_partial[P_IND(cat, ind_j)] * sigma11[ind_i + ind_j*n_inds];
				} // cat
			} // matching
		} // ind_j
	} // ind_j
		
	return PyArray_Return(F_sum_in);
}
