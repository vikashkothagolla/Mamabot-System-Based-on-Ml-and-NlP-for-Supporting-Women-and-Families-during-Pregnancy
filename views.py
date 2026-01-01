from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
import pymysql
from django.http import HttpResponse
import numpy
import tflearn
import tensorflow
import random
import json
import pickle
import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

with open("dataset/question.json") as file:
    data = json.load(file)

try:
    with open("data.pickle", "rb") as f:
        words, labels, training, output = pickle.load(f)
except:
    words = []
    labels = []
    docs_x = []
    docs_y = []

    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"]
    words = sorted(list(set(words)))
    labels = sorted(labels)
    training = []
    output = []
    out_empty = [0 for _ in range(len(labels))]
    for x, doc in enumerate(docs_x):
        bag = []
        wrds = [stemmer.stem(w.lower()) for w in doc]
        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)
        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1
        training.append(bag)
        output.append(output_row)
    training = numpy.array(training)
    output = numpy.array(output)    
    with open("data.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f)
    f.close()    

tensorflow.reset_default_graph()

print(str(len(training[0]))+" "+str(len(output[0])))
net = tflearn.input_data(shape=[None, len(training[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
net = tflearn.regression(net)

model = tflearn.DNN(net)

#try:
 #   model.load("model/model.tflearn")
#except:
#model.fit(training, output, n_epoch=1000, batch_size=8, show_metric=True)
model.load("model/model.tflearn")

def checkResponse(response,inputs,patterns):
    arr = response.lower().split(" ")
    status = 0
    temp = inputs.lower().split(" ")
    for i in range(len(temp)):
        if temp[i] in arr:
            status = 1
            break
    if status == 0:
        for i in range(len(patterns)):
            arr = patterns[i].lower().split(" ")
            for j in range(len(temp)):
                if temp[j] in arr:
                    status = 1
                    j = len(temp)
                    i = len(patterns)
                    break
    return status    


def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1
            
    return numpy.array(bag)

def MyChatBot(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def User(request):
    if request.method == 'GET':
       return render(request, 'User.html', {})

def Logout(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def test(request):
    if request.method == 'GET':
       return render(request, 'test.html', {})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})

def ChatData(request):
    if request.method == 'GET':
        question = request.GET.get('mytext', False)
        results = model.predict([bag_of_words(question, words)])
        results_index = numpy.argmax(results)
        tag = labels[results_index]
        output = ''
        for tg in data["intents"]:
            if tg['tag'] == tag:
                responses = tg['responses']
                patterns = tg['patterns']
        value = random.choice(responses)
        status = checkResponse(value,question,patterns)
        if status == 1:
            output = value
        else:
            output = "Sorry! I am not trained to answer above question"
        
        print(question+" "+output)
        return HttpResponse(output, content_type="text/plain")

def UserLogin(request):
    if request.method == 'POST':
      username = request.POST.get('username', False)
      password = request.POST.get('password', False)
      index = 0
      con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'chatbot',charset='utf8')
      with con:    
          cur = con.cursor()
          cur.execute("select * FROM register")
          rows = cur.fetchall()
          for row in rows: 
             if row[0] == username and password == row[1]:
                index = 1
                break		
      if index == 1:
       context= {'data':'welcome '+username}
       return render(request, 'UserScreen.html', context)
      else:
       context= {'data':'login failed'}
       return render(request, 'User.html', context)

def Signup(request):
    if request.method == 'POST':
      username = request.POST.get('username', False)
      password = request.POST.get('password', False)
      contact = request.POST.get('contact', False)
      email = request.POST.get('email', False)
      address = request.POST.get('address', False)
      db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'chatbot',charset='utf8')
      db_cursor = db_connection.cursor()
      student_sql_query = "INSERT INTO register(username,password,contact,email,address) VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"')"
      db_cursor.execute(student_sql_query)
      db_connection.commit()
      print(db_cursor.rowcount, "Record Inserted")
      if db_cursor.rowcount == 1:
       context= {'data':'Signup Process Completed'}
       return render(request, 'Register.html', context)
      else:
       context= {'data':'Error in signup process'}
       return render(request, 'Register.html', context)
