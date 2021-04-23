import sys,os,time,urllib
import traceback, json
import argparse
from operator import itemgetter

import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


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
        if(mode == "crawlData"):
            self.crawlData()
        elif(mode == "fetchData"):
            self.fetchData()
            self.writeTracks()
        elif(mode == "analyze"):
            self.readTracks()
            self.deleteDuplicates()
            self.printTracks()
            self.writeIntoCSV("tracks.csv")
    def crawlData(self):

        self.tracks = []

        chrome_options = Options()    
        #chrome_options.add_argument("--user-data-dir=chrome-data")
        driver = webdriver.Chrome('chromedriver.exe',options=chrome_options)
        
        driver.get("https://oe3.orf.at/player")
        # wait for searchbox
        firstTitleSelector = "li.broadcast-item:nth-child(4) > div:nth-child(2)"
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, firstTitleSelector)))

        cookieAcceptElems = driver.find_elements(By.CSS_SELECTOR, "#ds-accept")
        if(len(cookieAcceptElems) > 0):
            cookieAcceptElems[0].click()
            time.sleep(1)

        daysSelector = ".tabs li.tab:not(.highlights)"
        daysElems = driver.find_elements(By.CSS_SELECTOR, daysSelector)

        for daysElem in daysElems:
            dateWeekdayElem = daysElem.find_elements(By.CSS_SELECTOR, ".date-weekday")[0]
            weekday = dateWeekdayElem.get_attribute("title")
            monthDayElem = daysElem.find_elements(By.CSS_SELECTOR, ".date-day")[0]
            monthDay = int(monthDayElem.text.replace(".",""))

            print(weekday)
            print(monthDay)

            #click on dayElem
            #WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".tabs li.tab:not(.highlights)")))
            daysElem.click()
            #driver.execute_script("arguments[0].click();", daysElem)

            #wait for first broadcast
            broadcastsSelector = ".broadcasts li.broadcast.available"
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, broadcastsSelector)))

            # get list of broadcasts  
            broadcastElems = driver.find_elements(By.CSS_SELECTOR, broadcastsSelector)

            for broadcastElem in broadcastElems:
                timeElem = broadcastElem.find_elements(By.CSS_SELECTOR,"time")[0]
                broadcastTime = timeElem.get_attribute("datetime")
                titleElem = broadcastElem.find_elements(By.CSS_SELECTOR,".title")[0]
                broadcastTitle = titleElem.text

                print(broadcastTime)
                print(broadcastTitle)

                #click on broadcastElem
                #WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".broadcasts li.broadcast.available")))
                broadcastElem.click()
                #driver.execute_script("arguments[0].click();", broadcastElem)
                time.sleep(1)

                #wait for first broadCastDetail
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".broadcast-detail")))

                # get list of tracks
                trackSelector = ".broadcast-detail .broadcast-item .track"
                trackElems = driver.find_elements(By.CSS_SELECTOR, trackSelector)

                for trackElem in trackElems:
                    try:   
                        interpreter = trackElem.find_elements(By.CSS_SELECTOR,".interpreter span")[0].text
                        title = trackElem.find_elements(By.CSS_SELECTOR,".title")[0].text
                        track = {
                            "interpreter": interpreter,
                            "title": title
                        }
                        self.Log(track)
                        self.tracks.append(track)
                    except Exception as e:
                        self.Log("Error: " + str(e) + " continuing...")

        driver.close()
    
    def writeTracks(self):
        f = open("tracks.txt","w")
        f.write(json.dumps(self.tracks))
        f.close()
    
    def writeTracks(self,fileName):
        f = open(fileName,"w")
        f.write(json.dumps(self.tracks))
        f.close()

    def writeIntoCSV(self,fileName):
        f = open(fileName,"w")
        
        for track in self.tracks:
            f.write(str(track["num"]) + ";" + track["title"] + ";" + track["interpreter"] + "\n")
        
        f.close()
    
    def readTracks(self):
        f = open("tracks.txt","r")
        self.tracks = json.loads(f.read())
        f.close()
    
    def printTracks(self):
        for track in self.tracks:
            self.Log(track)

    def deleteDuplicates(self):
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
        
        for track in self.tracks:
            if(isInTracksNew(track)):
                incrementTrack(track)
            else:
                tracksNew.append({
                    "interpreter": track["interpreter"],
                    "title": track["title"],
                    "num": 1
                })
        self.tracks = sorted(tracksNew, key=itemgetter('num'), reverse=True) 
    
    def fetchData(self):

        self.tracks = []

        broadcastDays = self.fetchBroadcasts()

        for broadcastDay in broadcastDays:
            self.Log(broadcastDay["day"])

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
                        self.tracks.append(songData)

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