import tweepy , json, sys, time,re
from tweepy import API
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import twitter_creds


#tensorflow
import numpy as np
from tensorflow import keras as K
import tensorflow as tf
import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'


FILE_NAME= 'last_id.txt'

class TwitterClient():
    def __init__(self, twitter_user= None):
        #Authenticates the user information
        self.auth= Authenticator().authenticate()
        self.twitter_client=API(self.auth)
        self.twitter_user= twitter_user
    
    def get_mentions(self, tweet_ID):
        mentions= self.twitter_client.mentions_timeline(tweet_ID)
        if(len(mentions)==0):
            return None
        else:
            for mention in reversed(mentions):
                if '#' in mention.text:
                    tweet= mention.text.lower()
                    tweet= tweet.replace('@sentanalysisbot', '')
                    tweet= tweet.replace('#', '')
                    file= open(FILE_NAME, 'w')
                    file.write(str(mention.id))
                    file.close()
                    return tweet, mention.id
    def get_reply_id(self):
        mentions=self.twitter_client.mentions_timeline()
        REPLY_ID= mentions[0].user._json["screen_name"]
        return REPLY_ID
    def update_status(self, message):
        self.twitter_client.update_status(message)
        
class Authenticator():
    def authenticate(self):
        auth =OAuthHandler(twitter_creds.ConsumerKey, twitter_creds.ConsumerSecret)
        auth.set_access_token(twitter_creds.AccessToken,twitter_creds.AccessSecret)
        return auth 
        
class listen(StreamListener):
    def __init__(self, fetched, wanted):
        self.fetched_tweets_filename= fetched
        self.num_tweets=0
        self.wanted_tweets=wanted

    def on_data(self,data):
        try:
            self.num_tweets+=1
            if(self.num_tweets-1<self.wanted_tweets):
                with open(self.fetched_tweets_filename, 'a') as tf:
                    json_load= json.loads(data)
                    text={'text': json_load['text']}
                    print(text)
                    tf.write(json.dumps(text))
                    tf.write('\n')
                return True
            else:
                return False
        except BaseException as be:
            print("Error on data: %s" %str(be))
        return True
        
    def on_error(self,status):
        if status ==420:
            #Twitter Rate Limiting Control
            return False
        print(status)

class streamer():
    def __init__(self):
        self.twitter_authenticator= Authenticator()
        
    def stream_tweets(self, fetched_tweet_file, hash_tag_list, wanted):
        #This handles twitter authentication and connection to twitter stream API
        listener= listen(fetched_tweet_file, wanted)
        auth= self.twitter_authenticator.authenticate()
 
        stream= Stream(auth, listener)
        stream.filter(track=hash_tag_list)


class SentimentAnalysis():
    def __init__(self):
        # 0. get started
        print("\nIMDB sentiment analysis using Keras/TensorFlow ")
        np.random.seed(1)
        # 1. load data
        max_words = 20000
        print("Loading data, max unique words = %d words\n" % max_words)
        (train_x, train_y), (test_x, test_y) = K.datasets.imdb.load_data(seed=1, num_words=max_words)
        self.max_review_len = 80
        train_x = K.preprocessing.sequence.pad_sequences(train_x,
                                                         truncating='pre', padding='pre', maxlen=self.max_review_len)  # pad and chop!
        test_x = K.preprocessing.sequence.pad_sequences(test_x,
                                                        truncating='pre', padding='pre', maxlen=self.max_review_len)
        # 2. define model
        print("Creating LSTM model")
        e_init = K.initializers.RandomUniform(-0.01, 0.01, seed=1)
        init = K.initializers.glorot_uniform(seed=1)
        simple_adam = K.optimizers.Adam()
        embed_vec_len = 32  # values per word -- 100-500 is typical
        self.model = K.models.Sequential()
        self.model.add(K.layers.Embedding(input_dim=max_words,
                                     output_dim=embed_vec_len, embeddings_initializer=e_init,
                                     mask_zero=True))
        self.model.add(K.layers.LSTM(units=100, kernel_initializer=init,
                                dropout=0.2, recurrent_dropout=0.2))  # 100 memory
        self.model.add(K.layers.Dense(units=1, kernel_initializer=init,activation='sigmoid'))
        self.model.compile(loss='binary_crossentropy', optimizer=simple_adam,
        metrics=['acc'])

        print(self.model.summary()) 

        # ==================================================================

        # 3. train model
        bat_size = 32
        max_epochs = 3
        print("\nStarting training ")
        self.model.fit(train_x, train_y, epochs=max_epochs,
                  batch_size=bat_size, shuffle=True, verbose=1) 
        print("Training complete \n")

        # 4. evaluate model
        loss_acc = self.model.evaluate(test_x, test_y, verbose=0)
        


    def use_model(self,sentence):
        print(sentence)
        d = K.datasets.imdb.get_word_index()
        review = sentence
        words = review.split()
        review = []
        for word in words:
            if word not in d:
                review.append(2)
            else:
                review.append(d[word]+3)
        review = K.preprocessing.sequence.pad_sequences([review],
        truncating='pre',  padding='pre', maxlen=self.max_review_len)

        prediction = self.model.predict(review)
        print("Prediction (0 = negative, 1 = positive) = ", end="")
        print("%0.4f" % prediction[0][0])
        return(float(prediction[0][0]))

if __name__=="__main__":
    #Default 1243672848251654144 tweet
    TWEETS_WANTED=10
    fetched_tweets_filename= "tweets.json"
    TwitterClient= TwitterClient()
    twitterstream= streamer()
    SA=SentimentAnalysis()
    while True:
        try:
            COUNTER=0
            POSITIVE_TOTAL=0
            hash_tag_list=[]
            filename=open(FILE_NAME,'r')
            PREVIOUS_ID= int(filename.read().strip())
            filename.close()
            #Use Try/Except if you want to read all the tweets
            #To keep the bot online, revove sys.exit() and change time interval to how often the bot should check for tweets
            time_interval= 15
            open(fetched_tweets_filename, 'w').close()
            hashtag, id1= TwitterClient.get_mentions(PREVIOUS_ID)
            hash_tag_list.append(hashtag)
            twitterstream.stream_tweets(fetched_tweets_filename, hash_tag_list, TWEETS_WANTED)

            ReplyFile= open(fetched_tweets_filename, 'r')
            string=ReplyFile.readline()
            while string:
                string = re.sub(r"http\S+", "", string)
                string= string.replace('{', '')
                string= string.replace('"', '')
                string= string.replace('}', '')
                string= string.replace('\n','')
                string= string.split(':')
                result= string[len(string)-1]
                for letter in result:
                    if(letter.isalpha()== False and letter.isspace()==False):
                        result= result.replace(letter, '')
                result= result.split(' ')
                finalstring=''
                for x in result:
                    if ('uc' in x) or ('ud' in x) or ('ua' in x) or ('ub' in x) or ('ue' in x):
                        pass
                    else:
                        finalstring+=x + ' '
                try:
                    PositivityIdx= SA.use_model(finalstring)
                    POSITIVE_TOTAL+= PositivityIdx
                    COUNTER+=1
                except:
                    print("Error analyzing text from tweets")
                string=ReplyFile.readline()
            ReplyFile.close()
            Final_Positivity= (POSITIVE_TOTAL/COUNTER) *100
            print(Final_Positivity)
            if(Final_Positivity >= 50):
                print("Positive Result")
            elif(Final_Positivity< 50):
                print("Negative or Not Enough Data/Tweets")
            USER_ID= TwitterClient.get_reply_id()
            TwitterClient.update_status("@"+ USER_ID + ' '+ Tweeted)
            time.sleep(time_interval)
        except:
            print("There is no more tweets. Bot will sleep for 1 minute.")
            time.sleep(60)

    
    
        
    
    

