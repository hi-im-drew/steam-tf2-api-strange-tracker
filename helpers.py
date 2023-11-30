#═══╡packages╞═══════════════════════════════╗
import requests
from urllib.parse import urlencode
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import random
import time
#════════════════════════════════════════════╝

#═══╡key╞════════════════════════════════════╗
key = 'E7799FE7DDAA7246995F8D4C26F0A994'     
#════════════════════════════════════════════╝

#═══╡user input╞═════════════════════════════╗
userVanityName    = 'drewk92'
appName           = 'Team Fortress 2'
appId           = '440'
#════════════════════════════════════════════╝



#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡
url_resolveVanity = 'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/'
params_resolveVanity = {
    'key'       : key,
    'vanityurl' : userVanityName
    }

def resolveVanity(key, userVanityName):
    if not userVanityName:
        userVanityName = input('Input your Vanity URL Name. This is the text following "https://steamcommunity.com/id/": ')
        
    try:
        response = requests.get(url_resolveVanity, params=urlencode(params_resolveVanity))
        response.raise_for_status()
        if response.json()['response']['success'] != 1:
            print("Response Code: " + str(response.json()['response']['success']))
            print("Response Message: " + str(response.json()['response']['message']))
        elif response.json()['response']['success'] == 1:
            return response.json()['response']['steamid']
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
        print('Exception occured during resolveVanity function.')
steamId = resolveVanity(key, userVanityName)
#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡



#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡
''' Commented out for now because TF2 not showing on App List
url_getAppId = 'http://api.steampowered.com/ISteamApps/GetAppList/v2/'
params_getAppId = {
    'key' : key
    }

def getAppId(key, appName):
    if not appName:
        appName = input('Input the application name: ')

    try:
        response = requests.get(url_getAppId, params=urlencode(params_getAppId))
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
        
    try:  
        df_appList = pd.DataFrame(response.json()['applist']['apps'])
        df_appList.to_csv('appList.csv', header='column_names')
    except ValueError as e:
        print('Value error. This typically means that the app was not found on the app list from Steam. Please ensure it is spelled correctly.')
        raise SystemExit(e)
        
    return df_appList[df_appList['name']==appName]['appid'].item() 
appId = getAppId(key, appName)
'''
#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡



#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡
url_getPlayerItems = f'http://api.steampowered.com/IEconItems_{appId}/GetPlayerItems/v0001/'
cacheRefresh       = str(random.randint(1, 10000))
params_getPlayerItems = {
    'key'       : key,
    'SteamID'   : steamId
    }

def getPlayerItems(cacheRefresh):
    try:
        response = requests.get(url_getPlayerItems, params=urlencode(params_getPlayerItems, cacheRefresh)).json()
        while response == {}:
            print('Empty backpack returned. Trying again in 5 seconds.')
            time.sleep(5)
            response = requests.get(url_getPlayerItems, params=urlencode(params_getPlayerItems, cacheRefresh)).json()
        
        return response['result']['items']
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except ValueError:
        print('Error calling API. Skipping this iteration.')
        pass
    print('Strange counter: ' + str(response['result']['items'][194]['attributes'][1]['value']))
playerItems = getPlayerItems(cacheRefresh)
#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡



#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡
def flattenJson(nested_json, exclude=[]):

    out = {}

    def flatten(x, name='', exclude=exclude):
        if type(x) is dict:
            for a in x:
                if a not in exclude: flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(nested_json)
    return out
#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡



#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡
def createPlayerItemsDf(playerItems):
    # Flattens the json file while excluding certain fields
    df_playerItems = pd.DataFrame([flattenJson(x, exclude=['float_value', 'equipped', 'account_info']) for x in playerItems])
    
    # Extract columns with 'attributes_x_defindex' and 'attributes_x_value'
    attribute_columns_defindex = [col for col in df_playerItems.columns if 'attributes_' in col and '_defindex' in col]
    attribute_columns_value = [col.replace('_defindex', '_value') for col in attribute_columns_defindex]
    
    # Melt the DataFrame to combine 'attributes_x_defindex' and 'attributes_x_value'
    df_playerItems = pd.melt(df_playerItems, 
                             id_vars=df_playerItems.columns.difference(attribute_columns_defindex + attribute_columns_value).tolist(),
                             value_vars=attribute_columns_defindex + attribute_columns_value,
                             var_name='attribute_name',
                             value_name='attribute_value')
    
    # Drop the pre-melt columns
    df_playerItems = df_playerItems.drop(columns=attribute_columns_defindex + attribute_columns_value, errors='ignore')
    
    # Create two separate tables from 'attribute_name' col in df_playerItems
    df_defindex = df_playerItems[df_playerItems['attribute_name'].str.endswith('defindex')]
    df_value = df_playerItems[df_playerItems['attribute_name'].str.endswith('value')]
    
    # Normalize value names in both tables 'attribute_name' col
    df_defindex['attribute_name'] = df_defindex['attribute_name'].str.replace('_defindex', '').str.replace('_value', '')
    df_value['attribute_name'] = df_value['attribute_name'].str.replace('_defindex', '').str.replace('_value', '')
    
    # Left join tables on 'id' and 'attribute_name'
    df_playerItemsFinal = pd.merge(df_defindex, df_value, how='left', left_on=['id','attribute_name'], right_on=['id','attribute_name'])
    
    # Renaming some columns
    df_playerItemsFinal = df_playerItemsFinal.rename(columns={'attribute_name': 'attribute_number','attribute_value_x': 'attribute_defindex','attribute_value_y': 'attribute_value'})
    
    # Drop extra right table extra columns from join
    df_playerItemsFinal = df_playerItemsFinal.drop(df_playerItemsFinal.filter(regex='_y$').columns, axis=1)
    
    # Rename left table columns
    df_playerItemsFinal = df_playerItemsFinal.rename(columns=lambda x: x[:-2] if x.endswith('_x') else x)
    
    # Add timestamp to dataframe
    df_playerItemsFinal['timestamp'] = pd.Timestamp("now")
    
    # Filter
    df_playerItemsFinal = df_playerItemsFinal.loc[df_playerItemsFinal['quality']==11]
    df_playerItemsFinal = df_playerItemsFinal.loc[df_playerItemsFinal['attribute_defindex']==214]
    
    return df_playerItemsFinal

df_playerItemsFinal = createPlayerItemsDf(playerItems)
#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡



#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡
url_getSchemaItems    = f'https://api.steampowered.com/IEconItems_{appId}/GetSchemaItems/v0001/'
url_getSchemaOverview = f'https://api.steampowered.com/IEconItems_{appId}/GetSchemaOverview/v0001/'
params_getSchema = {
    'key' : key,
    'language' : 'en'
    }

def getSchemaItems(key, appId):
    try:
        response = requests.get(url_getSchemaItems, params=urlencode(params_getSchema))
        return response.json()['result']['items']
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
schemaItems = getSchemaItems(key, appId)

def getSchemaOverview(key, appId): 
    try:
        response = requests.get(url_getSchemaOverview, params=urlencode(params_getSchema))
        return response.json()['result']
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
schemaOverview = getSchemaOverview(key, appId)
#════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡