# Shaposhnik Vladislav 09.10.22
import sys
import tkinter
import cv2

import numpy as np
import scipy
import matplotlib.pyplot as plt
from scipy.fftpack import fft
from scipy.io import wavfile # get the api
import scipy.io.wavfile as waves

import PIL  # MODULO PARA PROCESAR IMAGENES
from PIL import Image
import os  # MODULO PARA HACER COSAS EN EL DIRECTORIO
import fnmatch  # MODULO PARA COMPARAR EXTENSIONES EN EL DIRECTORIO
import tarfile # MODULO PARA COMPRIMIR

from scipy import misc
import pywt

#1. TRANSMISOR
fs, data = wavfile.read(sys.argv[1]) # load the data
a = data # this is a two channel soundtrack, I get the first track
result_fft = fft(a)
result_len = int(len(result_fft)/2)  # you only need half of the fft list (real signal symmetry)
#solo necesitaria entonces ir hasta result_len -1 para obviar los conjugados


#xr=parte real del result_fft
xr = np.real(result_fft[:result_len])
#xi=parte imaginaria del result_fft
xi = np.imag(result_fft[:result_len])
#Calculando conversion a formato de imagen
# aux1 = xr.astype(np.uint8)
# aux2 = xi.astype(np.uint8)
max_xr = xr[::].max()
max_xi = xi[::].max()
min_xr = xr[::].min()
min_xi = xi[::].min()
print("max_xr ",max_xr)
print("max_xi ",max_xi)
print("min_xr ",min_xr)
print("min_xi ",min_xi)

if min_xr != max_xr:
    xrn = ((xr - min_xr) / (max_xr - min_xr))*255        #auxiliar para normalizar parte real de fft_result
else:
    xrn = np.zeros(shape = xr.shape)
if min_xi != max_xi:
    xri = ((xi - min_xi) / (max_xi - min_xi))*255        #auxiliar para normalizar parte imaginaria de fft_result
else:
    xri = np.zeros(shape = xi.shape)

#agregando a cada imagen el minimo y maximo para la hora de descomprimir
fila = np.zeros((1,xrn.shape[1]))

fila[0] = min_xr
xrn = np.concatenate((xrn, fila), 0)

fila[0] = min_xi
xri = np.concatenate((xri,fila), 0)

fila[0] = max_xr
xrn = np.concatenate((xrn, fila), 0)

fila[0] = max_xi
xri = np.concatenate((xri,fila), 0)

xrn = xrn.astype(np.uint8)
xri =xri.astype(np.uint8)
print(xrn)
print(xri)


#PARA VER LAS IMAGENES
# plt.rcParams['image.cmap'] = 'gray'
# plt.imshow(xrn,vmin=0,vmax=1)
# plt.figure()
# plt.imshow(xri,vmin=0,vmax=1)

imgr = Image.fromarray(xrn, mode="L")
imgr.save("real.jpg")
imgi = Image.fromarray(xri, mode="L")
imgi.save("imag.jpg")

# plt.show()







 #2.RECEPTOR

 #Algoritmo de descompresion de imagenes en formato .jpg
real2 = cv2.imread("real.jpg", cv2.IMREAD_GRAYSCALE)
imag2 = cv2.imread("imag.jpg", cv2.IMREAD_GRAYSCALE)

imag = imag2.astype(np.double)
real =real2.astype(np.double)
print("real: ", real.shape)

min_xr = real[real.shape[0] - 2][0]
min_xi = imag[imag.shape[0] - 2][0]
max_xr = real[real.shape[0] - 1][0]
max_xi = imag[imag.shape[0] - 1][0]
print("max_xr ",max_xr)
print("max_xi ",max_xi)
print("min_xr ",min_xr)
print("min_xi ",min_xi)

#hay que desnormalizar los valores:
res_imag = np.zeros((imag.shape[0]-2, imag.shape[1]))
res_real = np.zeros((real.shape[0]-2, real.shape[1]))

for i in range(imag.shape[0] - 2):
    if min_xi != max_xi:
        res_imag[i] = (imag[i] * (max_xi - min_xi) / 255) + min_xi
    else:
        res_imag[i] = np.full(imag.shape[1], min_xi)

for i in range(real.shape[0] - 2):
    for j in range(real.shape[1]):
        if min_xr != max_xr:
            res_real[i][j] = (real[i][j] * (max_xr - min_xr) / 255) + min_xr
        else:
            res_real[i][j] = min_xr

matriz = np.empty(shape = res_real.shape, dtype = complex)
for i in range(res_real.shape[0]):
    for j in range(res_real.shape[1]):
        matriz[i][j] = np.complex(res_real[i][j], res_imag[i][j])

print(matriz.shape)
print(matriz)

total_matriz = np.empty(shape = (res_real.shape[0]*2, res_real.shape[1]), dtype = complex)
cong_matriz = matriz.conjugate()

def unir(positivo, negativo, matriz_final):
    for i in range(positivo.shape[0]):
        for j in range(positivo.shape[1]):
            matriz_final[i][j] = positivo[i][j]
            matriz_final[matriz_final.shape[0] - 1 - i][j] = negativo[i][j]

unir(matriz, cong_matriz, total_matriz)

print("total_matriz ",total_matriz)
print(total_matriz.shape)

#Aplicar a eso la ifft
final = np.fft.ifft(total_matriz)
print("final ", final)

#Aplicar Wavelet para quitar ruido: (funcion wden de matlab, filtro deb3, umbral: minimaxi, opcion de escala: sln, nivel de descoposicin: maximo
sin_ruido = pywt.wavedec(final,'db3')
print("SIN RUIDO", sin_ruido)

#Exportar Audio
sonidofinal=np.array(sin_ruido[0], dtype='int8')
wavfile.write('salida_' + sys.argv[1], fs, sonidofinal)