from __future__ import print_function
import httplib2
import os
import datetime
from dateutil import parser
import json
import sqlite3
import csv
import plotly.plotly as py
import plotly
import plotly.graph_objs as go

plotly.tools.set_credentials_file(username='laurentahari', api_key='lvdgiNRmFQFlQFc09cQd')

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

CACHE_FILE = "gmail.json"

conn = sqlite3.connect('finalProject.db')
cur = conn.cursor()

# GMAIL DATA (input- gmail information)
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

# From Google starter code
def get_credentials():
	home_dir = os.path.expanduser('~')
	credential_dir = os.path.join(home_dir, '.credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir,
								   'gmail-python-quickstart.json')

	store = Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

# Initial load of cache
try:
	file = open(CACHE_FILE, "r")
	data = json.loads(file.read())
	file.close()
except:
	data = {}

# Gmail message caching getter
def getMessage(message_id):
	if message_id in data:
		return data[message_id]
	else:
		message = service.users().messages().get(userId="me", id=message_id).execute()
		data[message_id] = message
		file = open(CACHE_FILE, "w")
		file.write(json.dumps(data))
		file.close()
		return message

# count messages by day of week and time of day
# input last 100 gmail messages, output = bins of when each email what recieved
interaction_count = {}
for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
	interaction_count[day] = {"dawn": 0,
	"early": 0,
	"afternoon": 0,
	"evening": 0}

credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('gmail', 'v1', http=http)
messages = service.users().messages().list(userId='me', maxResults=100).execute().get("messages", [])

#access the date of each message. assign variables for each day of week and time of day
#input = time of day. output = bins of what time I recieved each each email
for msg in messages:
   message = getMessage(msg['id'])
   dateOfMessage = datetime.datetime.fromtimestamp(int(message["internalDate"])/1000)
   dayOfWeek = dateOfMessage.strftime('%A')
   timeofDay = int(dateOfMessage.strftime('%H'))

   if timeofDay >= 0 and timeofDay < 6:
	   interaction_count[dayOfWeek]["dawn"] += 1
   elif timeofDay >= 6 and timeofDay < 12:
	   interaction_count[dayOfWeek]["early"] += 1
   elif timeofDay >= 12 and timeofDay < 18:
	   interaction_count[dayOfWeek]["afternoon"] += 1
   elif timeofDay >= 18 and timeofDay <= 24:
	   interaction_count[dayOfWeek]["evening"] += 1

# Initial Report in Terminal
print(json.dumps(interaction_count, indent=4))

# Database Set Up and Saving (input = time of recieved emails- output = saved in SQL database)
cur.execute('DROP TABLE IF EXISTS GmailMessages')
#this creates table structure
table_spec = 'CREATE TABLE IF NOT EXISTS '
table_spec += 'GmailMessages (dayOfWeek TEXT, binName TEXT, count INTEGER)'
cur.execute(table_spec)

for day in interaction_count:
	for binName in interaction_count[day]:
		insert = 'INSERT OR IGNORE INTO GmailMessages VALUES (?, ?, ?)'
		cur.execute(insert, (day, binName, interaction_count[day][binName]))
conn.commit()

# Creates CSV Report (input = day, time of bin, number of messages)
with open('gmailReport.csv', 'w') as csvfile:
	writer = csv.writer(csvfile, delimiter=",")
	fieldnames = ['dayOfWeek', 'binName', 'emailCount']
	writer.writerow(fieldnames)
	for day in interaction_count:
		for binName in interaction_count[day]:
			writer.writerow([day, binName, interaction_count[day][binName]])

# Plotly for GmailMessages (input 100 emails, time of email and day of email. Output is visualization)

layout = go.Layout(
    title='My Last 100 Gmail Messages by Time Window',
    xaxis=dict(
        title='Day of Week',
        titlefont=dict(
            family='Courier New, monospace',
            size=18,
            color='pink'
        )
    ),
    yaxis=dict(
        title='Hour Window',
        titlefont=dict(
            family='Courier New, monospace',
            size=18,
            color='blue'
        )
    )
)
trace = {
  "x": [],
  "y": [],
  "marker": {
    "size": [],
    "sizemode": "area",
    "sizeref": 0.01,
	 "color": "rgb(255, 127, 14)",
  },
  "mode": "markers",
  "name": "binName",
  "type": "scatter",
}

for day in interaction_count:
	for binName in interaction_count[day]:
		trace["x"].append(day)
		trace["y"].append(binName)
		trace["marker"]["size"].append(interaction_count[day][binName])

data = go.Data([trace])
fig = go.Figure(data=data, layout=layout)
plot_url = py.plot(fig)


# YOUTUBE data (input: youtube info. Output = bins with each day and its relative video upload count)
youtube = discovery.build("youtube", "v3", developerKey="AIzaSyD2D13OgNCA56kl6ejr71Cudr3xJDYkhKA")
#set up bints for days of week
youtube_day_count = {}
for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
	youtube_day_count[day] = 0

# Prompt user for YouTube input search and plot color
youtubeSearchTerm = input("Type in a YouTube search: ")
ytPlotColor = input("Type in a color for the YouTube bar chart: ")
#from Youtube API setup
vid_list = youtube.search().list(type="video", q=youtubeSearchTerm, part="id,snippet", maxResults=50).execute()["items"]
for video in vid_list:
	vidDate = parser.parse(video['snippet']["publishedAt"])
	dayOfWeek = vidDate.strftime('%A')
	youtube_day_count[dayOfWeek] += 1 #add to bin

cur.execute('DROP TABLE IF EXISTS YoutubeUploads')
#this creates table structure
table_spec = 'CREATE TABLE IF NOT EXISTS '
table_spec += 'YoutubeUploads (dayOfWeek TEXT, count INTEGER)'
cur.execute(table_spec)

for day in youtube_day_count:
	insert = 'INSERT OR IGNORE INTO YoutubeUploads VALUES (?, ?)'
	cur.execute(insert, (day, youtube_day_count[day]))
conn.commit()

# CSV Report
with open('youtubeReport.csv', 'w') as csvfile:
	writer = csv.writer(csvfile, delimiter=",")
	fieldnames = ['dayOfWeek', 'videoCount']
	writer.writerow(fieldnames)
	for day in youtube_day_count:
		writer.writerow([day, youtube_day_count[day]])

# Plotly for YouTube

trace1 = {
  "x": [count for count in youtube_day_count.values()],
  "y": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
  "name": "YouTube Views by Day",
  "type": "bar",
  "orientation": "h",
  "marker" : {
  	"color" : ytPlotColor
  }
}


data = go.Data([trace1])
layout = {
"title":'Uploads by Day for Last 50 Videos for Search: {}'.format(youtubeSearchTerm),
"showlegend": True,
"hovermode": "closest",
    "autosize": True,
    "showlegend": True,
    "xaxis": {
      "type": "linear",
      "autorange": True,
      "title": "Count Uploaded"
    },
    "yaxis": {
      "type": "category",
      "autorange": True,
      "title": "Day of the Week"
    }
}
fig = go.Figure(data=data, layout=layout)
plot_url2 = py.plot(fig)

print(plot_url)
print(plot_url2)
