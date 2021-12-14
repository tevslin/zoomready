# zoomready
Beta release of free app to determine and track the quality of your internet connection on a continuous basis, especially the connection's suitability for teleconferencing. 

## Uses
1. determine whether it is your connection or someone else's which is causing freezes and disconnects
2. measure whether your Internet Service Provider (ISP) is delivering the level of service you were promised including during peak periods
3. find which rooms in your house have the best WiFi connections
4. determine whether a hotel connection or other temporary connection is good enough for teleconferencing

## Description
Adesktop app designed to be run continuously to monitor the quality of your Internet connection. Tracks current and average latency, jitter, and speed up and down. Indicator lights show suitability for teleconferencing. Latency must be less than 75 ms (milliseconds), jitter less than 15 ms, download speed more than 5Mbps (megabits per second), and upload more than 3Mbps to be considered fully zoomready (green). If these criteria are not met but latency is less 100ms, jitter less than 25ms, download faster than 2Mbps, and upload more than 1Mbps, the zoomready status is "iffy" (yellow). Anything else including inability to connect is status red - not usable for teleconferencing. You will usually find yourself freezing on Zoom and other teleconferencing platforms if your zoomready status is red.

## Installation

### Windows

To download the Windows executable, click [here](https://zoomready.s3.amazonaws.com/zoomready.exe). You may have to contend with virus blockers or Windows itself warning that the software is from an unknown publisher (me). The software has so far only been tested on Windows 10.

### Mac and Linux

There are currently no Linux or Mac versions. 

## Python source

The Python source is available from [this Github repository](https://github.com/tevslin/zoomready). It is not yet on PyPi.

## Use - Windows only

### Startup

Use File Explorer to navigate to whereever you saved zoomready.exe during download and double click on the name of the program or right click the name and select open. There is no need to run as administrator. Note that zoomready is currently very slow to start running; be patient. If you don't see its window after a while, look for a feather icon (temporary) in the taskbar and click it to bring the window to the front. It will be running and monitoring whether it is the front window or not. You can also minimize  zoomready and it will continue monitoring,

Bring the window to the front by clicking on the icon whenever you want to see the current state of your connection.

***Caution: zoomready sends test packets. It shoud NOT be run continuously on a metered connection.

### Pause/Resume

The Pause button causes zoomready to stop testing your connection. If your connection is iffy but you want to continue your teleconference, you may want to pause zoomready so that its test packets don't compete with your conference for bandwidth which is in short supply. Click Resume to restart monitoring.

### Quit

Click the Quit button.

## How it works

Tests for latency are done by sending ping packets to Google, Cloudflare, and OpenDNS. This is a good selection for testing in the US but may not be in other countries. Currently this selection cannot be changed. Eventually there will be an opportunity to set preferences. Zoomready makes Python requests to various subaddresses of [speed.cloudflare.com](https://speed.cloudflare.com). Their API is not documented, as far as I know; and so that is a vulnerability for this code. There is also a request to [ipdatabase.com](http://www.ipdatabase.com/ip) and the return is screen-scraped for your actual ISP name.

Mirroring the performance of the Cloudflare webpage, the CLI does multiple uploads and downloads with different block sizes and the 90th percentile of all these tests is used for calculating up and download times. Results are similar to those obtained from the webpage.

Unlike Ookla's speedtest CLI, Cloudflare does not require downloading a licensed exe. Cloudflare uses test sites from its own network of caching and hosting centers. This is useful because much of the content users would be retrieving is actually coming from these centers. On the other hand, coverage may be thin in some parts of the world.

## Bug reports and suggestions for improvement

Pleas click 

## Privacy

No identifying information is sent to any website other than the IP address which servers can see in an HTTP request. Cloudflare can probably deduce something from the tests it runs and Google, Cloudflare, and OpenDNS will know from where (but not from whom) they are being pinged. No results are sent anywhere. Because this is an application and not running in a browser, there are no cookies.

## Background

Teleconferencing, as with Zoom, is an essential part of modern American life. It's needed not only for work from home but also for remote schooling and telemedicine. We have a need to know which connections we can use for teleconferencing. Moreover, billions of US federal dollars are being disbursed to improve broadband availability and quality, especially in rural areas. Tools are needed to assure that ISPs deliver the quality they promise. This software is a *pro bono* contribution to getting those tools written. 

## Disclaimers

No claims of any sort are made for this software. It has been lightly tested on Windows 10. Use and/or redistribute solely at your own risk. No commitemnt is made to maintain this software. As noted above, changes made by Cloudflare or ipdatabase.com might breeak the functionality.

##note: zoomready used to be zoombuddy but there is another app by that name.

I have no affiliation with Cloudflare, Zoom, any teleconferencing or hosting service, or any ISP (except as a customer).

