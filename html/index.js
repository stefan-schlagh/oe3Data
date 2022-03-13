"use strict";
(async function(){

    // TODO mit react und recharts
    async function drawChart(path,id,indexLength,getName){
        const response = await fetch(path)
        const csv = CSVToArray(await response.text())
        const header = csv[0]
        // remove first and last line
        csv.shift()
        csv.pop()
        
        const top = []
        for(const item of csv){
            top.push({
                name: getName(item),
                items: item.slice(indexLength)
            })
        }
        console.log(top)

        const chartData = []
        for(let i = indexLength;i < header.length;i++){
            chartData.push([new Date(header[i])])
        }
        // for each day and item
        for(let i = 0;i < header.length - indexLength;i++){
            for(const item of top){
                chartData[i].push(parseInt(item.items[i]))
            }
        }

        google.charts.load('current', {packages: ['corechart', 'line']});
        google.charts.setOnLoadCallback(drawBasic);

        function drawBasic() {

            const data = new google.visualization.DataTable();
            data.addColumn('date','Date')
            
            for(const item of top){
                data.addColumn('number', item.name);
            }

            console.log(chartData)
            data.addRows(chartData)

            console.log(data)
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
        
            var chart = new google.visualization.LineChart(document.getElementById(id));
        
            chart.draw(data, options);
    }
    }
    // draw tracks chart
    drawChart("./data/topt15.csv","topTracks-chart",3,track => (track[1] + " " + track[2]))
    // draw interpreters chart
    drawChart("./data/topi15.csv","topInterpreters-chart",2,interpreter => (interpreter[1]))
})(this)