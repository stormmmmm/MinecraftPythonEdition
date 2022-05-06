from random import randint as rand
import math
from numba import njit
import numpy as np
import cv2

def m(w,h,mh):
    mas = np.zeros((h,w,3),np.uint8)
    for i in range(h):
        for z in range(w):
            c = rand(0,mh)
            mas[i,z] = (c,c,c)
    mas = cv2.resize(mas,None,fx=2,fy=2,interpolation=cv2.INTER_LINEAR)
    return mas

@njit(fastmath=True)
def spl(mas1,mas2):
    h1 = mas1.shape[0]
    h2 = mas2.shape[0]
    w1 = mas1.shape[1]
    w2 = mas2.shape[1]
    rh = h1//h2
    rw = w1//w2
    for i1 in range(h2):
        for z1 in range(w2):
            for i2 in range(rh):
                for z2 in range(rw):
                    c1 = mas1[i1*rh+i2,z1*rw+z2,0]
                    c2 = mas2[i1,z1,0]
                    c = np.uint8((np.uint16(c1)+np.uint16(c2)*8)//9)
                    mas1[i1*rh+i2,z1*rw+z2] = (c,c,c)
    return mas1

def generate(n,mh):
    if n < 50:
        n = 50
    w,h = n,n
    mas1 = m(w,h,mh)
    mas2 = m(w//10,h//10,mh)
    mas3 = m(w//50,h//50,mh)

    mas2 = spl(mas2, mas3)
    mas1 = spl(mas1, mas2)

    mas1 = cv2.resize(mas1,None, fx=5, fy=5, interpolation=cv2.INTER_LINEAR)
    cv2.imwrite("mas.png",mas1)

    return mas1

class NoiseGen:
    def __init__(self,mas):
        self.mas = mas

    def getHeight(self,x,z):
        return self.mas[x][z][0]
