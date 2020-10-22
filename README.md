# Twitter-Bot-
Sentimental Analysis Bot for Twitter

The bot utilizes machine learning on the IMDB movie reviews as training and test data. Using this prediction data, the program is able to analyze a string of sentences to determine the chance of a positive or negative message.

Implementation with Twitter: Using a live twitter client, the bot connects to the twitter account and listens for tweets. As the designated account is tweeted at, the hashtag following the tweet will be used as the parameter for analyzation. The applicaction then fetches the last 100 tweets and calculates the average positivity related to the hashtag.

Libraries: tweepy, tensorflow

