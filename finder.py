from PyQt5 import QtWidgets
import os
import sys
import numpy as np #matris işlemleri için kullandığımız kütüphanedir
from imageio import imread #görüntü verilerini okumak ve yazmak için kolay bir arayüz sağlayan kütüphanedir.
import cv2 #görüntü işleme kütüphanesidir.
from hashlib import md5 # verilerimizi farklı algoritmalarda şifrelememizi sağlayan bir kütüphanedir.
from scipy.spatial import distance # Numpy uzantısına dayanan matematiksel algoritmalar ve kolaylık işlevlerinin bir koleksiyonudur. 
import itertools #tekrarlanan veriler için  belleği verimli kullanan fonksiyonlar sunan bir modüldür.
from GUI import Ui_FINDER as gui
import time

start = time.time()#Sure Baslatma
#Arayuz basltma
app = QtWidgets.QApplication(sys.argv)
Finder = QtWidgets.QWidget()
ui =gui()
ui.setupUi(Finder)
Finder.show()
#Fotograf bulunmasi ve kaldirilmasi

resim_dosyalari= gui.dizi('self')
print("Secilen Dosya Sayisi:"+ str(len(resim_dosyalari)))
imread(resim_dosyalari[0]).shape#imread ile görüntüyü okuma işlemini gerçekleştirdik

def img_gray(resim):#resmi griye çeviriyoruz.  
    resim=imread(resim)
    return np.average(resim,axis=2,weights=[0.299, 0.587, 0.114])#belirtilen eksen boyunca ağırlıklı ortalamayı hesapladık.

def goruntu_filtrele(resimler):
    resim_list=[]
    for resim in resimler:
        try:
            assert imread (resim).shape[2]==3
            resim_list.append(resim)
        except AssertionError as e:
            print(e)
    return resim_dosyalari

def resize(resim,yukseklik=60,genislik=60):#resmi yeniden boyutlandırıyoruz
     row_res = cv2.resize(resim,(yukseklik,genislik),interpolation = cv2.INTER_AREA).flatten()#düz şekilde boyutlandırıyoruz
     col_res = cv2.resize(resim,(yukseklik,genislik), interpolation = cv2.INTER_AREA).flatten('F')#burda fortran tarzıyla boyutlandırıyoruz.
     
     return row_res, col_res
 
def intensity_diff(row_res, col_res):#resim piksellerini tek tek karşılaştıtı
    difference_row = np.diff(row_res)#np.diff ile verilen eksen boyunca n'inci sıradaki ayrık farkı hesaplar.
    difference_col = np.diff(col_res)
    difference_row = difference_row > 0
    difference_col = difference_col > 0   
    return np.vstack((difference_row, difference_col)).flatten()#vstack ile tek bir dizi oluşturmak için dikey olarak istifler ve flatten ile düzleştiririz

def file_hash(dizi):
    return md5(dizi).hexdigest()#kodlanmış veriyi 16lık sayı formatında döndürür.

def difference_score(resim,yukseklik=60,genislik=60):
    gri=img_gray(resim)
    row_res, col_res = resize(gri, yukseklik, genislik)#griye çevrilen resmi girilen değerlere göre boyutlandırıyoruz.
    difference = intensity_diff(row_res, col_res)#Piksellerdeki yoğunluk farkını alıyoruz
    
    return difference #yoğunluk farkını dönderiyoruz.

def difference_score_dict_hash(resim_list):
    ds_dict = {}
    duplicates = []#kopyaları kontrol etmek için oluşturduk.
    hash_ds = []#farkları eklemek için oluşturduk.
    for resim in resim_list:
        ds = difference_score(resim)#her görüntü için ne kadar farklı olduğunu hesaplıyoruz.
        hash_ds.append(ds)
        filehash = md5(ds).hexdigest()
        if filehash not in ds_dict:
            ds_dict[filehash] = resim
        else:
            duplicates.append((resim, ds_dict[filehash]) )
    
    return  duplicates, ds_dict, hash_ds   
 
resim_dosyalari = goruntu_filtrele(resim_dosyalari) #resimlerin hepsini filtrele fonksiyonuna gönderiyoruz.
duplicates, ds_dict, hash_ds =difference_score_dict_hash(resim_dosyalari)

def hamming_distance(resim, resim2): #iki resmi karşılaştırıp ne kadar benzediğine dair bi puan dönderiyoruz.
    score =distance.hamming(resim, resim2)
    return score

def difference_score_dict(resim_list):
    ds_dict = {}
    duplicates = []
    for resim in resim_list:
        ds = difference_score(resim)
        
        if resim not in ds_dict: #resim oluşturduğumuz sözlükte yok ise resmin fark puanını sözlüğe atıyoruz
            ds_dict[resim] = ds
        else:
            duplicates.append((resim, ds_dict[resim]))
            
    return  duplicates, ds_dict
 
    
resim_dosyalari =goruntu_filtrele(resim_dosyalari)
duplicates, ds_dict =difference_score_dict(resim_dosyalari)

for k1,k2 in itertools.combinations(ds_dict, 2):#oluşturulan sözlüğün ikili kombinasyonlarını oluşturur.
    if hamming_distance(ds_dict[k1], ds_dict[k2])< .10:#mesafe on noktadan az ise yinelenen adlı diziye ekliyoruz.
        duplicates.append((k1,k2))
        
sayac=0

for file_names in duplicates[:32]:
    try:
        os.remove(file_names[0])#benzer veya aynı fotoğrafı silme işlemini yaptık
        sayac=sayac+1

    except OSError as e:
        continue
    
print("Silenen Dosya Sayisi:" + str(sayac) )
end = time.time()
print("Time:" + str(end - start))
