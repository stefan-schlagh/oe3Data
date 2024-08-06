import sys,os,time,urllib,datetime
import traceback, json
import argparse
from operator import itemgetter

import requests
import pandas as pd

def main(argv):
    try:
        executeOptions()
    except Exception as e:
        traceback.print_exc()
        print("Exited with an error: " + str(e))

def executeOptions():
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", help="the mode that should be used",type=str)
    args = parser.parse_args()

    mode = args.mode
    if(mode == "fetchData"):
        fetchData()
    elif(mode == "analyze"):
        analyze()
    elif(mode == "all"):
        fetchData()
        analyze()

def fetchData():
    Oe3Crawler()

def analyze():
    trackAnalyzer = TrackAnalyzer()
    # getInterpretersCsv
    trackAnalyzer.getInterpretersCsv()
    # getTracksByWeek --> getTransposedTracks (works)
    trackAnalyzer.getTracksByWeek()
    # getInterpretersByWeek --> getTransposedInterpreters (does not work)
    # TODO fix
    #trackAnalyzer.getInterpretersByWeek()

csvSeparator = ","

# fetches data
# writes tracks to csv
class Oe3Crawler:
    def __init__(self):
        self.fetchData()
        self.deleteDuplicates()
        self.writeTracks()
        self.writeIntoCSV("tracks.csv")
    
    def Log(self,val):
        print(val)
    
    def getFormattedDate(self,date):
        return date[0:4] + "-" + date[4:6] + "-" + date[6:8]
    
    def writeTracks(self,fileName="tracks.json"):
        f = open(fileName,"w")
        f.write(json.dumps(self.trackDays))
        f.close()

    def writeIntoCSV(self,fileName):

        self.getTracks()

        f = open(fileName,"w",encoding="utf-8")
        
        rows, cols = (len(self.tracks) + 1, len(self.trackDays) + 2)
        fields = [[0 for i in range(cols)] for j in range(rows)]

        fields[0][0] = "track"
        fields[0][1] = "interpreter"

        # write days TODO: format
        for i in range(len(self.trackDays)):
            fields[0][i + 2] = self.getFormattedDate(self.trackDays[i]["day"])

        # write titles + interpreters
        for i in range(len(self.tracks)):
            track = self.tracks[i]
            fields[i + 1][0] = "\"" + track["title"] + "\""
            track["interpreter"] = track["interpreter"].replace("\"","")
            fields[i + 1][1] = "\"" + track["interpreter"] + "\""

        # write nums
        for i in range(len(self.tracks)):
            for j in range(len(self.trackDays)):
                trackDay = self.trackDays[j]
                track = self.tracks[i]
                fields[i + 1][j + 2] = self.getTrackNumFromTrackDay(track,trackDay)

        for fieldList in fields:
            for field in fieldList:
                f.write(str(field) + csvSeparator)
            f.write("\n")
        
        f.close()

    def getTrackNumFromTrackDay(self,track,trackDay):
        for trackDayTrack in trackDay["tracks"]:
            if(trackDayTrack["title"] == track["title"] and trackDayTrack["interpreter"] == track["interpreter"]):
                return trackDayTrack["num"]
        return 0

    def readTracks(self):
        fname = "tracks.json"
        # if file exists: load
        if(os.path.isfile(fname)):
            f = open(fname,"r")
            self.trackDays = json.loads(f.read())
            f.close()
        # else: create empty array
        else:
            self.trackDays = []
    
    def printTracks(self):
        self.getTracks()
        for track in self.tracks:
            self.Log(track)
    
    def getTracks(self):

        tracks = []

        for trackDay in self.trackDays:
            for track in trackDay['tracks']:
                if(not self.isInTracks(tracks,track) and not "Werbeblock" in track["title"]):
                    tracks.append(track)
        
        self.tracks = sorted(tracks, key=itemgetter('interpreter'))

    def isInTracks(self,tracks,_track):
        for track in tracks:
            if(track["title"] == _track["title"] and track["interpreter"] == _track["interpreter"]):
                return True
        return False

    def deleteDuplicates(self):
        # iterate through each day
        for trackDay in self.trackDays:

            trackDay["tracks"] = self.deleteTrackDayDuplicates(trackDay["tracks"])

    def deleteTrackDayDuplicates(self,tracks):
        
        tracksNew = []

        def getTrackNew(track):
            for trackNew in tracksNew:
                if(track["title"] == trackNew["title"] and track["interpreter"] == trackNew["interpreter"]):
                    return trackNew
        def incrementTrack(track):
            trackNew = getTrackNew(track)
            #self.Log(trackNew)
            trackNew["num"] = trackNew["num"] + 1
        
        for track in tracks:
            if(self.isInTracks(tracksNew,track)):
                incrementTrack(track)
            else:
                num = 1
                if("num" in track):
                    num = track["num"]
                tracksNew.append({
                    "interpreter": track["interpreter"],
                    "title": track["title"],
                    "num": num
                })
        return tracksNew
    
    def doesTrackDayExist(self,day):

        for trackDay in self.trackDays:
            if(trackDay["day"] == day):
                return True
        return False

    def fetchData(self):

        #self.trackDays = []

        self.readTracks()

        def formatted(date):
            return date.strftime("%Y%m%d")

        today = formatted(datetime.datetime.now())
        weekAgo = formatted(datetime.datetime.now() - datetime.timedelta(days=7))

        broadcastDays = self.fetchBroadcasts()

        for broadcastDay in broadcastDays:
            day = str(broadcastDay["day"])
            # if exactly 1 week ago or today, do not add
            # if already in trackDays, do not add
            if(day != today and day != weekAgo and not self.doesTrackDayExist(day)):
                # track array of day
                tracks = []

                for broadcast in broadcastDay["broadcasts"]:
                    #self.Log(broadcast["title"])

                    broadCastDataItems = self.fetchJson(broadcast["href"])["items"]
                    for broadCastData in broadCastDataItems:
                        #is a song?
                        if("songId" in broadCastData and broadCastData["songId"] != None):
                            songData = {
                                "interpreter": broadCastData["interpreter"],
                                "title": broadCastData["title"],
                                "description": broadCastData["description"]
                            }
                            #self.Log(songData)
                            tracks.append(songData)
                # append day
                self.trackDays.append({
                    "day": day,
                    "tracks": tracks
                })

    def fetchBroadcasts(self):
        r = requests.get('https://audioapi2.orf.at/oe3/json/4.0/broadcasts?_o=oe3.orf.at')
        if(r.status_code == 200):
            return r.json()
    
    def fetchJson(self,href):
        r = requests.get(href)
        if(r.status_code == 200):
            return r.json()

class TrackAnalyzer:
    def __init__(self):
        self.readTracks()

    def readTracks(self):
        self.dfTracks = pd.read_csv('tracks.csv')
        # drop last column
        self.dfTracks.drop(self.dfTracks.columns[len(self.dfTracks.columns)-1], axis=1, inplace=True)

        print("\nself.dfTracks")
        print(self.dfTracks)

    def getInterpretersCsv(self):
        # group by interpreter
        self.dfInterpreters = self.dfTracks.groupby("interpreter").sum()

        print("\nself.dfInterpreters")
        print(self.dfInterpreters)

        self.dfInterpreters.to_csv("interpreters.csv")

    def getTransposedTracks(self):
        df = self.dfTracks.transpose()
        # set col header: https://stackoverflow.com/questions/55283790/how-to-turn-multiple-rows-into-multiple-headers-headers-in-pandas-dataframe
        df.columns = [df.iloc[0].values, df.iloc[1].values]
        df = df.iloc[2:].reset_index(drop=False)
        # change name of coumn 1
        new_columns = df.columns.values
        new_columns[0] = 'date'
        df.columns  = new_columns

        # create date index column
        # src: http://blog.josephmisiti.com/group-by-datetimes-in-pandas
        df["date"] = pd.to_datetime(df["date"])
        df["date_"] = df["date"].apply( lambda df : 
            datetime.datetime(year=df.year, month=df.month, day=df.day))
        # set index column	
        df.set_index(df["date_"],inplace=True)
        # drop column "date"
        df.drop(df.columns[[0]], axis=1, inplace=True)

        return df

    # TODO fix
    def getTransposedInterpreters(self):
        df = self.dfInterpreters.transpose()
        # rename index column
        df.index.name = "date_"

        #print(df)
        #print(df.head(n=10).iloc[:, : 5].to_string(index=False))

        # create date index column
        # src: https://stackoverflow.com/questions/40815238/python-pandas-convert-index-to-datetime
        df.index = pd.to_datetime(df.index)

        return df

    def getTracksByWeek(self):
        fileName="tw2.csv"
        # top x is evaluated
        topx = 15
        self.tracksTopX = []

        df = self.getTransposedTracks()

        # set index
        df = df.set_index('date_')

        print("\ntransposed tracks")
        print(df)

        # group by week
        #df = df.resample('W', on='date_')[df.columns].sum()
        df = df.resample('W').sum()

        print("\ngrouped by week")
        print(df)

        # set dates
        self.dates = []
        for date in df.index:
            self.dates.append(date)

        # transpose back
        df_t = df.transpose()
        # write to csv
        df_t.to_csv(fileName)

        # read again
        df = pd.read_csv(fileName)
        # delete first and last column
        firstDate = self.dates[0]
        df.drop(str(firstDate.date()), axis=1, inplace=True)
        self.dates.remove(firstDate)
        lastDate = self.dates[len(self.dates) - 1]
        df.drop(str(lastDate.date()), axis=1, inplace=True)
        self.dates.remove(lastDate)

        # sort
        tracksTopTitles = []
        print(self.dates)
        for date in self.dates:

            df.sort_values(by=str(date.date()), inplace=True, ascending=False)
            df = df.reset_index(drop=True)

            # add track if not already here
            for i in range(topx):
                track = df.loc[i].values
                # if not already in top 10, add
                #trackTitle = track[0] + " " + track[1]
                trackTitle = f"{track[0]} {track[1]}"

                if(not trackTitle in tracksTopTitles):
                    tracksTopTitles.append(trackTitle)
                    self.tracksTopX.append(track)

        # does not work if only one week is looked at
        if len(self.tracksTopX) > 0:

            dfNew = pd.DataFrame(self.tracksTopX)
            dfNew.columns = df.columns.values

            dfNew.to_csv("topt" + str(topx) + ".csv")
        
    def getInterpretersByWeek(self):
        fileName="iw2.csv"
        # top x is evaluated
        topx = 15
        self.interpretersTopX = []

        df = self.getTransposedInterpreters()
        # group by week
        df = df.resample('W')[df.columns].sum()

        # set dates
        self.dates = []
        for date in df.index:
            self.dates.append(date)

        # transpose back
        df_t = df.transpose()
        # write to csv
        df_t.to_csv(fileName)
        
        # read again
        df = pd.read_csv(fileName)
        # delete first and last column
        firstDate = self.dates[0]
        df.drop(str(firstDate.date()), axis=1, inplace=True)
        self.dates.remove(firstDate)
        lastDate = self.dates[len(self.dates) - 1]
        df.drop(str(lastDate.date()), axis=1, inplace=True)
        self.dates.remove(lastDate)
        # sort
        interpretersTopTitles = []
        for date in self.dates:

            df.sort_values(by=str(date.date()), inplace=True, ascending=False)
            df = df.reset_index(drop=True)

            # add track if not already here
            for i in range(topx):
                iRow = df.loc[i].values
                # if not already in top 10, add
                interpreter = iRow[0]

                if(not interpreter in interpretersTopTitles):
                    interpretersTopTitles.append(interpreter)
                    self.interpretersTopX.append(iRow)

        # does not work if only one week is looked at
        if len(self.interpretersTopX) > 0:
            dfNew = pd.DataFrame(self.interpretersTopX)
            dfNew.columns = df.columns.values

            dfNew.to_csv("topi" + str(topx) + ".csv")

if __name__ == "__main__":
   main(sys.argv[1:])