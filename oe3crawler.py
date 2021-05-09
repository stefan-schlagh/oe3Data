import sys,os,time,urllib,datetime
import traceback, json
import argparse
from operator import itemgetter

import requests


def main(argv):
    Oe3Crawler(argv)

csvSeparator = ","

class Oe3Crawler:
    def __init__(self,argv):
        try:
            self.executeOptions()
        except Exception as e:
            traceback.print_exc()
            self.Log("Exited with an error: " + str(e))
    
    def Log(self,val):
        print(val)
    
    def executeOptions(self):
        # parse args
        parser = argparse.ArgumentParser()
        parser.add_argument("mode", help="the mode that should be used",type=str)
        args = parser.parse_args()

        mode = args.mode
        if(mode == "fetchData"):
            self.fetchData()
            self.deleteDuplicates()
            self.writeTracks()
        elif(mode == "analyze"):
            self.readTracks()
            self.deleteDuplicates()
            #self.printTracks()
            self.writeIntoCSV("tracks.csv")
            #self.getInterpreters()
            #self.writeInterpretersIntoCSV("interpreters.csv")
        elif(mode == "all"):
            self.fetchData()
            self.deleteDuplicates()
            self.writeTracks()
            self.writeIntoCSV("tracks.csv")
    
    def writeTracks(self,fileName="tracks.json"):
        f = open(fileName,"w")
        f.write(json.dumps(self.trackDays))
        f.close()

    def writeIntoCSV(self,fileName):

        self.getTracks()

        f = open(fileName,"w")
        
        rows, cols = (len(self.tracks) + 1, len(self.trackDays) + 2)
        fields = [[0 for i in range(cols)] for j in range(rows)]

        fields[0][0] = "track"
        fields[0][1] = "interpreter"

        # write days TODO: format
        for i in range(len(self.trackDays)):
            fields[0][i + 2] = self.trackDays[i]["day"]

        # write titles + interpreters
        for i in range(len(self.tracks)):
            track = self.tracks[i]
            fields[i + 1][0] = "\"" + track["title"] + "\""
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

    def writeInterpretersIntoCSV(self,fileName):
        f = open(fileName,"w")
        
        for interpreter in self.interpreters:
            f.write(str(interpreter["num"]) + csvSeparator + interpreter["interpreter"] + "\n")
        
        f.close()
    
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
                if(not self.isInTracks(tracks,track)):
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
            self.Log(trackNew)
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
        #return sorted(tracksNew, key=itemgetter('num'), reverse=True)

    def getInterpreters(self):

        interpreters = []

        def isInInterpreters(_interpreter):
            for interpreter in interpreters:
                if(interpreter["interpreter"] == _interpreter):
                    return True
            return False
        def getInterpreter(_interpreter):
            for interpreter in interpreters:
                if(interpreter["interpreter"] == _interpreter):
                    return interpreter
        def incrementInterpreter(track):
            interpreter = getInterpreter(track["interpreter"])
            interpreter["num"] = interpreter["num"] + track["num"]

        for track in self.trackDays:
            if(isInInterpreters(track["interpreter"])):
                incrementInterpreter(track)
            else:
                interpreters.append({
                    "interpreter": track["interpreter"],
                    "num": track["num"]
                })
        self.interpreters = sorted(interpreters, key=itemgetter('num'), reverse=True) 
    
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
                    self.Log(broadcast["title"])

                    broadCastDataItems = self.fetchJson(broadcast["href"])["items"]
                    for broadCastData in broadCastDataItems:
                        #is a song?
                        if("songId" in broadCastData and broadCastData["songId"] != None):
                            songData = {
                                "interpreter": broadCastData["interpreter"],
                                "title": broadCastData["title"],
                                "description": broadCastData["description"]
                            }
                            self.Log(songData)
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

if __name__ == "__main__":
   main(sys.argv[1:])