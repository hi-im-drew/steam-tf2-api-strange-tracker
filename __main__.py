from helpers import resolveVanity, getPlayerItems, createPlayerItemsDf
import os
import time
import math
import random

key               = '########'   
  
userVanityName    = 'drewk92'
steamId           = resolveVanity(key, userVanityName)

appName           = 'Team Fortress 2'
appId             = '440'

pollingRate       = 5 #every x minutes
repetitions       = int(1440/pollingRate) - math.ceil((1440/pollingRate)/24)

for x in range(repetitions):
    cacheRefresh = str(random.randint(1, 10000))
    
    playerItems  = getPlayerItems(cacheRefresh)
    df           = createPlayerItemsDf(playerItems)
    
    if not os.path.isfile('tf2items.csv'):
       df.to_csv('tf2items.csv', header='column_names')
       print("Couldn't find file, creating new file and adding item details.")
       print(f"╞═════╡Loop {x} out of {repetitions}╞═════╡")
    else: # else it exists so append without writing the header
       df.to_csv('tf2items.csv', mode='a', header=False)
       print("CSV file founded, adding new item details.")
       print(f"╞═════╡Loop {x} out of {repetitions}╞═════╡")
    time.sleep(60*pollingRate)
