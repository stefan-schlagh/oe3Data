import sys,os,time,urllib
import traceback, json
import argparse
from operator import itemgetter

import requests


def main(argv):
    Oe3Crawler(argv)

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
        parser.add_argument("mode", help="the mode that should be used, modes:  extractSongTitles | extractSongs",type=str)
        args = parser.parse_args()

        mode = args.mode
        if(mode == "fetchData"):
            self.fetchData()
            self.deleteDuplicates()
            self.writeTracks()
        elif(mode == "analyze"):
            self.readTracks()
            self.deleteDuplicates()
            self.printTracks()
            self.writeIntoCSV("tracks.csv")
            #self.getInterpreters()
            #self.writeInterpretersIntoCSV("interpreters.csv")
    
    def writeTracks(self,fileName="tracks.txt"):
        f = open(fileName,"w")
        f.write(json.dumps(self.trackDays))
        f.close()

    def writeIntoCSV(self,fileName):
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
            fields[i + 1][0] = track["title"]
            fields[i + 1][1] = track["interpreter"]

        # write nums
        for i in range(len(self.tracks)):
            for j in range(len(self.trackDays)):
                trackDay = self.trackDays[j]
                track = self.tracks[i]
                fields[i + 1][j + 2] = self.getTrackNumFromTrackDay(track,trackDay)

        for fieldList in fields:
            for field in fieldList:
                f.write(str(field) + ";")
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
            f.write(str(interpreter["num"]) + ";" + interpreter["interpreter"] + "\n")
        
        f.close()
    
    def readTracks(self):
        f = open("tracks.txt","r")
        self.trackDays = json.loads(f.read())
        f.close()
    
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
        
        self.tracks = sorted(tracks, key=itemgetter('title')) 

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

        def isInTracksNew(track):
            for trackNew in tracksNew:
                if(track["title"] == trackNew["title"] and track["interpreter"] == trackNew["interpreter"]):
                    return True
            return False
        def getTrackNew(track):
            for trackNew in tracksNew:
                if(track["title"] == trackNew["title"] and track["interpreter"] == trackNew["interpreter"]):
                    return trackNew
        def incrementTrack(track):
            trackNew = getTrackNew(track)
            trackNew["num"] = trackNew["num"] + 1
        
        for track in tracks:
            if(isInTracksNew(track)):
                incrementTrack(track)
            else:
                tracksNew.append({
                    "interpreter": track["interpreter"],
                    "title": track["title"],
                    "num": 1
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
    
    def fetchData(self):

        self.trackDays = []

        broadcastDays = self.fetchBroadcasts()

        for broadcastDay in broadcastDays:
            day = broadcastDay["day"]
            self.Log(day)
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