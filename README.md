# ThreatParser
Warrior tank threat parser for classic wow

Requires python 3 and some packages at this time.

To start, run "python ThreatParser.py".  
Enter your Warcraftlogs report ID, press Fetch.  
Select the options and the tank and boss to parse.  
Voilá.  

**Notes:** 
Only threat on the actual boss counts, ie not on adds.
Only top ranks of abilities are registered.

TODO:
 - More optimized GET from warcraftlogs
 - Filter non warrior tanks from player list
 - Manual selection input, button for snug fit
 - Graph granularity option(s)
 - Dragging selection out of data should update table
 - Clear output when a new fetch is done

