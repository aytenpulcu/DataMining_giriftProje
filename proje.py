from googlesearch import search
import requests     
from bs4 import BeautifulSoup
from collections import Counter
from zemberek_python import main_libs as ml
import math
import json
import pandas as pd
zemberek_api = ml.zemberek_api(libjvmpath="C:/Program Files/Java/jre1.8.0_301/bin/server/jvm.dll", zemberekJarpath="C:/Users/ayten/OneDrive/Belgeler/Python Scripts/zemberek_python/zemberek-tum-2.0.jar").zemberek()

headers_param={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"}

class Sent:
    def __init__(self, stype, numOfword, numerik, conj):
        self.type=stype
        self.numOfword = numOfword
        self.numerik = numerik
        self.conj = conj  
    def Skor(self,x): # cümle puanı olusturur
        self.skor = x

all_url=[]
topic_words=[]
all_docs=[]
classList=[]

def searchText(str,num,st):
    all_text=" "
    try:
        count=st
        urls=search(str,tld='co.in',lang='tr',num=num,start=st,stop=st+num,pause=2.0)
        for url in urls:
            source = requests.get(url,headers=headers_param)
            all_url.append(url)
            if source.status_code == 200:
                content = source.content
                html = BeautifulSoup(content,"html.parser",from_encoding="utf-8")
                one_page= html.find_all("p")  
                page=""      
                for p in one_page:
                    page += p.text
                    page=page.lower()
                all_docs.append(page)
                all_text+=page 
                count+=1
                print(count,". site tarandı")
        return all_text
    except:
        print("aramada hata oluşu!")
        return all_text

def preprocess(text):
    #metinde ki karakterleri sınıflandırma ve baglaç kullanımını inceleme işlemi yapar
    sentList=[]
    corpus=text_tokenize(text) #metni cümlelelere ayırır
    corpus=text_control(corpus) # metin içerisinde tekrar eden cümleleri siler
    text=""
    for sentnc in corpus:
        alnum=0
        conj=0
        sent=sent_tokenize(sentnc) #cümleyi kelimelere ayır
        #cümle türünü belirlemek için yükleme bakar, devrik cümlelelerde çalısmaz
        if sent==0:
            sentnc=""
            continue
        pre=sent[len(sent)-1]
        dic = ml.ZemberekTool(zemberek_api).ogelere_ayir(pre)
        if dic!=None:
            stem=dic["tip"]
            if stem=="FIIL":
                typ=False
            elif stem=="ISIM":
                typ=True
            else:
                typ=False
        else:
            continue
        for w in sent:
            if w.isalnum()==True:
                alnum+=1
            elif w=="ve" or w=="veya" or w=="ya" or w=="hem": #sıralama,esdegerli,karsılastırma
                conj+=1
            elif w=="ama" or w=="fakat" or w=="ancak" or w=="yalnız" : #karsıtlık
                conj+=1
            elif w=="oysa" or w=="halbuki" or w=="lakin": 
                conj+=1
            elif w=="çünkü" or w=="madem" or w=="zira" or w=="yoksa": #gerekce
                conj+=1
            elif w=="kısacası" or w=="açıkçası" or w=="yani": #ozetleme
                sent=sent[w:]
            elif w=="özetle" or w=="halde" or w=="öyleyse": #ozetleme
                sent=sent[w:]
            elif w=="hatta" or w=="ayrıca" or w=="başka": #pekistirme
                sent=sent[:w]
            elif w=="bile" or w=="dahi" or w=="üstelik" : #pekistirme
                sent=sent[:w]
            elif w.isalpha()==False:
                w=""
        
        sentList.append(Sent(typ,len(sent),alnum,conj))
        text=text+convert_list_to_string(sent)+"\n"
    
    return text,corpus,sentList

def text_control(sentList):
    n=len(sentList)-1
    for i in range(0,n-1):
        for  j in range(i+1,n):
            if len(sentList[i])==len(sentList[j]):
                if sentList[i]==sentList[j]:
                    sentList[j]=""
    return sentList

def convert_list_to_string(mix_list):
    full_str = ' '.join([str(elem) for elem in mix_list])
    return full_str

def convert_dic_to_string(mix_list):
    full_str =""
    for i in range(1,len(mix_list)-1,2):
        full_str=full_str + mix_list[i]
    return full_str

def printFile(text,file_name):
    try:
        f = open(file_name, "w",encoding="utf-8")
        f.write(text)
    except:
        print("metin dosyaya yazılamadı!")
    finally:
        f.close()
    
def writeUrl(str):
    s=str+".json"
    with open(s, 'w') as json_dosya:
        json.dump(all_url, json_dosya)

def bagOfword(text):
    print("Metin özetleme başlatıldı") 
    corpus = ml.ZemberekTool(zemberek_api).metinde_gecen_kokleri_bul(text)                    
    # BagofWord hazırlanır
    len_word = Counter(corpus)
    corpusLen=len(corpus)
    corpus.clear()
    rawFreq ={}
    max=0
    sum=0
    # En sık kullanılan kelimelere bir fonksiyon ile bakabiliyoruz.
    # terimlerin metindeki önemini hesaplayabilmek için raw freq değerlerini buluyoruz
    for w in len_word.most_common(len(len_word)):
        temp=w[0] #tuple tipinde oldugu icin kelimeyi alıyoruz
        dic = ml.ZemberekTool(zemberek_api).ogelere_ayir(temp)
        if dic!=None and len(temp)>=2:
            stem=dic["tip"]
            if stem!="FIIL":
                corpus.append(temp)
                rfreq=w[1]/corpusLen
                rawFreq[temp]=rfreq
                if max < rfreq:
                    max=rfreq
        elif len(temp)<=2: #metinde gecen yabancı kelimeleri de terim olarak alıyoruz
            corpus.append(temp)
            rfreq=w[1]/corpusLen
            rawFreq[temp]=rfreq
            if max < rfreq:
                max=rfreq
        # buldugumuz raw freq degerlerini kullanarak double normalization yöntemini uygulayıp,
        #  idf fonksiyonunu cagırıyoruz ve iki degerin carpımı kelimenin degerini veriyor
    
    for w in corpus:
        dNormalization=0.5+(0.5*(rawFreq[w]/max))
        value=tf_ıdf(w)
        value=int(value*dNormalization*10)
        rawFreq[w]=value
        if value>0:
            sum=sum+value
    
    #aritmetik ortalama hesaplanır ve ortalamadan yüksek olan değerler terim olarak alınır
    
    avg=int(sum/len(corpus))
    print("tf-idf değerlerinin ortalaması,",avg)
    if avg==0.0:
        avg=3
    while len(topic_words)==0 and avg>0:
        for w in corpus:
            if value>avg:
                topic_words.append(value) 
                topic_words.append(w)
        avg-=1
    print("terim sayısı:",len(topic_words)/2)
    return 
    
def tf_ıdf(word):
     #|log(10/10)| , len(docs)
    count=0
    value2=math.log10(len(all_docs))
    for d in all_docs:
        result=d.find(word)
        if result>0:
            count+=1
    if count>0:
        value1=math.log10(count)
        return abs((value1-value2))
    else:
        return 0

def sort_clist(clist,corpus):
    for i in range(len(clist)-1):
        for j in range(i+1,len(clist)-1):
            if clist[i].skor < clist[j].skor:
                temp=clist[i]
                clist[i]=clist[j]
                clist[j]=temp

                stemp=corpus[i]
                corpus[i]=corpus[j]
                corpus[j]=stemp

    return corpus


def text_tokenize(text):
    corpus=[]
    temp=""
    for ch in text:
        if ch=='.' and len(temp)>6:
            temp=temp+ch
            corpus.append(temp)
            temp=""
        else:
            temp=temp+ch
    print("İlk metindeki cümle sayısı",len(corpus))
    return corpus

def sent_tokenize(sents):
    words=[]
    temp=""
    for ch in sents:
        if ch==' ':
            if temp.isalpha() and len(temp)>=2:
                words.append(temp)
            elif temp.isnumeric():
                words.append(temp)
            temp=""
        else:
            temp=temp+ch
    words.append(temp)#son kelimeyi ekleme
    if len(words)>0:
        return words
    else:
        return 0

def CountSkor(corpus,clist):
    for i in range(len(clist)):
        words = ml.ZemberekTool(zemberek_api).metinde_gecen_kokleri_bul(corpus[i])
        sum=0 
        for word in words:
            for k in range(1,len(topic_words)-1,2):
                if topic_words[k]==word:
                    sum+=topic_words[k-1]
        if clist[i].numOfword<20:
            sum+=2
        else:
            sum-=2
        if clist[i].numerik>0:
            sum+=1
        if clist[i].type==True:
            sum+=2
        clist[i].Skor(sum+clist[i].conj)
    
    size=150

    corpus=sort_clist(clist,corpus)

    """for i in range(size):
        result=result+"\n"+corpus[i]"""
    
    result=corpus[:size]
    result.append([item for item in all_url])
    all_url.clear()
    return result


def clean(list):
    df=pd.DataFrame(list)
    with pd.ExcelWriter('mylist1.xlsx') as writer:
        df.to_excel(writer)       

def main():
    print("Aramak istediğiniz konu:") 
    s=input()
    fname=s+".txt"
    fname2=s+"_n"+".txt"
    n=10
    
    all_text = searchText(s,n,0)
    corpus=text_tokenize(all_text)
    while len(corpus)<300 and n<100:
        text=searchText(s,5,n) 
        n+=5
        all_text=all_text+"\n"+text     
        corpus=text_tokenize(all_text)  
    clean(corpus)
    """all_text,corpus,classList=preprocess(all_text)
    printFile(all_text,fname)
    writeUrl(s)

    bagOfword(all_text)
    text=CountSkor(corpus,classList)
    printFile(text,fname2)"""
        
      
if __name__ == "__main__":
    main()
