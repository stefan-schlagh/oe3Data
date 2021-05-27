"use strict";
(async function(){

    const response = await fetch("./data/top15.csv")
    const topTracksRaw = CSVToArray(await response.text())
    const header = topTracksRaw[0]
    // remove first and last line
    topTracksRaw.shift()
    topTracksRaw.pop()

    const topTracks = []
    for(const track of topTracksRaw){
        topTracks.push({
            name: track[1] + " " + track[2],
            items: track.slice(3)
        })
    }

    const chartData = []
    for(let i = 2;i<header.length;i++){
        chartData.push([moment(header[i]).week()])
    }
    // for each day and track
    for(let i = 0;i < header.length - 2;i++){
        for(const track of topTracks){
            chartData[i].push(parseInt(track.items[i]))
        }
    }

    google.charts.load('current', {packages: ['corechart', 'line']});
    google.charts.setOnLoadCallback(drawBasic);

    function drawBasic() {

        const data = new google.visualization.DataTable();
        data.addColumn('number', 'X');
        
        for(const track of topTracks){
            data.addColumn('number', track.name);
        }

        data.addRows(chartData)

        const options = {
            hAxis: {
              title: 'Week'
            },
            vAxis: {
              title: 'Frequency'
            },
            height: 800,
            width: 1600
          };
    
          var chart = new google.visualization.LineChart(document.getElementById('topTracks-chart'));
    
          chart.draw(data, options);
    }
})(this)