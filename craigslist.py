import boto3
import feedparser
import logging
import os
import pandas as pd
import urllib
from flask import Flask

app = Flask(__name__)
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
TO_EMAILS = "postelrich@gmail.com,amy.postelnik@gmail.com"
PAST_HOURS = "6"
CRAIGSLIST_URL = "https://newyork.craigslist.org/search/que/abo?sort=date&availibilityMode=0&query=astoria&format=rss&max_price=2800"

def recent_apartments():
    logger.info("Querying: %s", CRAIGSLIST_URL)
    feed = feedparser.parse(CRAIGSLIST_URL)
    apartments = pd.DataFrame(feed['entries'])
    apartments['published'] = pd.to_datetime(apartments.published.str[:-6])
    logger.info("Latest date found: %s", str(apartments.published.max()))
    apartments = apartments.set_index('published')
    now = pd.Timestamp.now()
    hour_ago = now - pd.Timedelta(hours=int(PAST_HOURS))
    logger.info("Hour ago: %s", str(hour_ago))
    recent_apts = apartments.loc[apartments.index > hour_ago]
    return recent_apts


def format_links(apartments):
    return '\n'.join('<a href="{}">{}</a>'.format(urllib.unquote(u).encode('utf-8'), urllib.unquote(t).encode('utf-8')) for t, u in apartments[['title','link']].values.tolist())


def email_apartments(apartments):
    ses = boto3.client('ses')
    to_emails = TO_EMAILS.split(',')
    response = ses.send_email(Source="postelrich@gmail.com",
                              Destination={'ToAddresses': to_emails},
                              Message={'Subject': {'Data': "{} New Apartments Found".format(len(apartments))},
                                       'Body': {'Text': {'Data': format_links(apartments)}}})


def apartments():
    apts = recent_apartments()
    logger.info("Found {} apartments.".format(len(apts)))
    if not apts.empty:
        email_apartments(apts)
    return format_links(apts)


@app.route('/', methods=['GET', 'POST'])
def lambda_handler(event=None, context=None):
    logger.info('Lambda function invoked')
    apartments()
    return "Craigslist"


if __name__ == '__main__':
    app.run(debug=True)
