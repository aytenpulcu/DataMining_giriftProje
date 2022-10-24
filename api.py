import proje
from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS

import os
import pickle
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
app = Flask(__name__)
CORS(app)
api = Api(app)

df = pd.read_excel('C:/Users/ayten/OneDrive/Belgeler/Python Scripts/mylist.xlsx')
from sklearn.feature_extraction.text import CountVectorizer
cv = CountVectorizer()
vectorizer_train = cv.fit_transform(df.sent)

# post isteğini çözümle
parser = reqparse.RequestParser()
parser.add_argument("search_text")
# kullanılan modeli al
if os.path.isfile("./model"):
  model = pickle.load(open("./model", "rb"))
"""else:
  raise FileNotFoundError"""

class Predict(Resource):
  def post(self):
    args = parser.parse_args()
    input=args["search_text"]
    output=findResult(input)
    urls=output[150:]
    output=output[:150]
    vectorizer_test = CountVectorizer(vocabulary=cv.vocabulary_)
    X_test = vectorizer_test.transform(output)
    text=""
    size=0
    print(len(output))
    for i in range(len(output)):
      sent=output[i]
      if( model.predict(X_test[i])==0):
        text=text+"\n"+sent
      else:
        size=size+1
    text=text+"\n KAYNAKLAR \n"+proje.convert_list_to_string(urls)
    print("sınıflandırma ile ",size," adet cümle elendi.")
    return text

def findResult(str):
  classList=[]
  n=10
  all_text=proje.searchText(str,n,0)
  corpus=proje.text_tokenize(all_text)
  while len(corpus)<150 and n<100:
        text=proje.searchText(str,5,n) 
        n+=5
        all_text=all_text+"\n"+text     
        corpus=proje.text_tokenize(all_text)
  all_text,corpus,classList=proje.preprocess(all_text)
  proje.bagOfword(all_text)
  Tlist=proje.CountSkor(corpus,classList)
  return Tlist

api.add_resource(Predict, "/search")
if __name__ == "__main__":
  app.run(debug=True)