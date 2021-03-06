command_template = """python extractnet.py --test-range=0-44 --train-range=0 --data-provider=general-cropped --checkpoint-fs-port=29101 --checkpoint-fs-name=models --checkpoint-db=reference_models --load-query='{"experiment_data.experiment_id": "nyu_model"}' --feature-layer=fc6 --data-path=/home/ardila/batches/ripple_filter%s --dp-params='{"crop_border": 16, "meta_attribute": "obj", "preproc": {"normalize": false, "dtype": "float32", "resize_to": [256, 256], "mode": "RGB", "mask": null, "crop":null, "ripple_filter":{"amplitude":%s, "waves_per_column":4}}, "batch_size": 128, "dataset_name": %s}' --write-db=1 --write-disk=0"""
import os
for dataset_name in ['["dldata.stimulus_sets.hvm", "HvMWithDiscfade"]',
                     '["dldata.stimulus_sets.semi_synthetic", "FoveatedHvM"]']:
    for ripple_filter_val, ripple_filter_folder_ind in zip([0.04, 0.03, 0.02, 0.01], [4,3,2,1]):
        cmd = command_template%(str(ripple_filter_folder_ind), str(ripple_filter_val) , str(dataset_name))
        print cmd
        os.system(cmd)

