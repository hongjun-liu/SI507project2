#################################
##### Name: Hongjun Liu
##### Uniqname: hongjunl
#################################

from bs4 import BeautifulSoup
import requests
import json
import secret_data as secrets # file that contains your API key
from requests_oauthlib import OAuth1

CACHE_FILENAME = "project2.json"
CACHE_DICT = {}
client_key=secrets.API_KEY
oauth=OAuth1(client_key)

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, cate="no category", name="no name", address="no address",
                 zip="no zipcode", phone="no phone"):
        self.category=cate
        self.name=name
        self.address=address
        self.zipcode=zip
        self.phone=phone

    def info(self):
        return self.name+" ("+self.category+")"+": "+self.address+" "+self.zipcode


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME, "w")
    fw.write(dumped_json_cache)
    fw.close()


def request_with_cache(url):
    ''' If URL in cache, retrieve the corresponding values from cache. Otherwise, connect to API again and retrieve from API.

    Parameters
    ----------
    url: string
        a URL

    Returns
    -------
    a string containing values of the URL from cache or from API
    '''
    cache_dict = open_cache()
    if url in cache_dict.keys():
        print("Using Cache")
        response = cache_dict[url]
    else:
        print("Fetching")
        response = requests.get(url).text  # need to append .text, otherwise, can't save a Response object to dict
        cache_dict[url] = response  # save all the text on the webpage as strings to cache_dict
        save_cache(cache_dict)
    return response

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    nps_base_url="https://www.nps.gov"
    response = request_with_cache(nps_base_url)
    soup = BeautifulSoup(response, 'html.parser')

    state_link_dict = {}
    allstates = soup.find(class_="dropdown-menu SearchBar-keywordSearch").find_all('a')
    for i in allstates:
        state_name = i.text.strip()
        state_link = "https://www.nps.gov" + i.get('href')
        state_link_dict[state_name.lower()] = state_link

    return state_link_dict
       

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    global addressa
    global addressb
    global zipcode
    response = request_with_cache(site_url)
    soup = BeautifulSoup(response, 'html.parser')
    # html = requests.get(site_url).text
    # soup = BeautifulSoup(html, 'html.parser')
    instance=NationalSite()
    instance.name = soup.find(class_="Hero-titleContainer clearfix").find("a").text.strip()
    instance.category=soup.find(class_="Hero-designationContainer").find("span").text.strip()
    search_foot=soup.find(id="ParkFooter")
    addresslist=search_foot.find_all("span")
    for i in addresslist:
        if i.find(itemprop="addressLocality") is not None:
            addressa = i.find(itemprop="addressLocality").text.strip()
        if i.find(itemprop="addressRegion") is not None:
            addressb = i.find(itemprop="addressRegion").text.strip()
        if i.find(itemprop="postalCode") is not None:
            zipcode = i.find(itemprop="postalCode").text.strip()

    instance.address=addressa+", "+addressb
    instance.zipcode=zipcode
    search_foot = soup.find(id='ParkFooter')
    phonelist= search_foot.find_all('span', itemprop="telephone")
    instance.phone=phonelist[0].text.strip()

    return instance

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    response = request_with_cache(state_url)
    soup = BeautifulSoup(response, 'html.parser')
    park_list=list()
    search_div = soup.find_all('div', class_="col-md-9 col-sm-9 col-xs-12 table-cell list_left")
    for i in search_div:
        parklist=i.find_all("a")
        parkurl="https://www.nps.gov"+parklist[0]["href"]+"index.htm"
        instance=get_site_instance(parkurl)
        park_list.append(instance)

    return park_list



def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    endpoint_url = 'http://www.mapquestapi.com/search/v2/radius'
    params = {"key": client_key, "origin": site_object.zipcode, "radius": 10,
              "maxMatches": 10, "ambiguities": "ignore", "outFormat": "json"}

    cache_dict=open_cache()
    if site_object.zipcode in cache_dict.keys():
        print("Using Cache")
        result = cache_dict[site_object.zipcode]
    else:
        print("Fetching")
        response=requests.get(endpoint_url, params=params, auth=oauth)
        result=response.json()# need to append .text, otherwise, can't save a Response object to dict
        cache_dict[site_object.zipcode] = result  # save all the text on the webpage as strings to cache_dict
        save_cache(cache_dict)



    name=list()
    category=list()
    street=list()
    city=list()
    j=0

    print("----------------------------------")
    print("Places near "+site_object.name)
    print("----------------------------------")
    for i in result["searchResults"]:
        name.append(i["name"])
        category.append(i["fields"]["group_sic_code_name_ext"])
        street.append(i["fields"]["address"])
        city.append(i["fields"]["city"])
        if category[j] == "":
            category[j]="no category"
        if street[j] == "":
            street[j]="no address"
        if city[j] == "":
            city[j]="no city"
        print("- "+name[j]+" ("+category[j]+"): "+street[j]+", "+city[j])
        j=j+1
    return result
    

if __name__ == "__main__":

    statesurl=build_state_url_dict()
    print('''Enter a state name (e.g. Michigan, michigan) or "exit"''')
    statename=input(":")
    temp=0

    while True:
        while True:
            if statename=="exit":
                print("Bye!")
                temp=1
                break

            try:
                intemp=0
                stateurl=statesurl[statename.lower()]
                parklist = get_sites_for_state(stateurl)
                order = 0
                orderlist=list()
                print("----------------------------------")
                print("List of national sites in "+statename.lower())
                print("----------------------------------")
                for i in parklist:
                    order =order + 1
                    orderlist.append(order)
                    print("[" + str(order) + "] " + i.info())
                print("")

                while True:
                       print('''Choose the number for detail search or "exit" or "back"''')
                       number=input(":")
                       if number=="exit":
                           print("Bye!")
                           temp = 1
                           intemp=1
                           break
                       if number=="back":
                           print('''Enter a state name (e.g. Michigan, michigan) or "exit"''')
                           statename = input(":")
                           break
                       if int(number) not in orderlist:
                           print("[Error] Invalid input")
                           print("")
                           print("----------------------------------")
                       if int(number) in orderlist:
                           get_nearby_places(parklist[int(number)-1])

                if intemp==1:
                    break

            except:
                print('[ERROR] Enter proper state name')
                print('''\nEnter a state name (e.g. Michigan, michigan) or "exit"''')
                statename = input(":")

        if temp==1:
            break





