nvcc -c sigma31_layers.c -I/usr/include/python2.7  -I/usr/include/numpy --compiler-options '-fPIC -std=gnu99 '
gcc -flat_namespace -o _sigma31_layers.so  sigma31_layers.o -lpython2.7 -shared