"""

7/6/2020
    To-do:

    Create an interface for querying for specific data.
    Should allow you to filter for quests that have specific combos of materials.

    What about the optimal path suggestion for a given amount of resources?
    4 dragon fangs, 3 phoenix feathers, 3 hearts of the foreign god, and 16 pages?
    Should be able to calculate this for you based on the currently available free quests.

    Modify Servant Class so it also calculates and caches the total AP costs for farming all the mats.
    Add a function to calculate to AP costs for teh remaining mats you need to get skills and ascensions to where you wnat them.
    Migth be easy enough to do based on existing function for doing such calculations.



"""
from bs4 import BeautifulSoup
import bs4
import requests
import re
import sys
import json
import cPickle as pickle #first time this runs it should save the servants to file
import os.path

base_url     = 'https://gamepress.gg/grandorder/item/'
test_item = 'evil-bone'
#item_filename = "evil-bone.pkl"
scrape   = False #os.path.isfile(servants_filename) #whether or not we need to download the servants
runQuery = False

if len(sys.argv) > 1:
    test_item = sys.argv[1]


def save_object(obj, filename):
    """ Written by martineau of StackExchange """
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        try:
            pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
        except IOException as e:
            print e.strerror
        except:
            print "Unexpected error"


def load_object(filename):
    with open(filename, 'rb') as input:
        try:
            temp = pickle.load(input)
        except IOException as e:
            print e.strerror
            exit()
        except:
            print "Unexpected error"
            exit()
    return temp

class Enemy:

    #are we going to go the URL route, or naw?
    #hmmm naw, I don't think so.
    #extract attack and stuff on our own.
    #we don't really need any
    #methods either
    #hmm but then, do we really need a class??
    #the only reason for a class would be like, calculations and stuff right? hm not sure yet
    def __init__(self, url, hp, name, class_type, lvl, rarity):
        print "Working on: " + url
        self.url        = url
        self.soup       = BeautifulSoup(requests.get(url).content, "html5lib") #parser doesn't work properly without html5lib in python2
        self.hp         = hp
        self.name       = name
        self.class_type = class_type
        self.lvl        = lvl
        self.rarity     = rarity
        self.attributes = []
        self.setAttributes()
        self.soup.decompose()

    def setAttributes(self):
        #won't work if the enemy is a servant, since they have different structured pages
        enemy_traits = self.soup.find(class_="view-enemy-traits")
        if enemy_traits: #normal enemy
            attribute_table = enemy_traits.find("table")
            #can probably just do .find(class_="views-table") but have to check special enemeis like servants etc
            tds = attribute_table.find_all("td")
            for td in tds:
                self.attributes.append(td.get_text().lower())
        else: #SErvant probably
            #lvl doesn't apply (Do nothing?) what is here, like "weak to man, etc
            attr_align = [ a.get_text() for a in self.soup.find(class_='attri-align-table').find_all('a')]
            for attr in attr_align:
                self.attributes.append(attr)
            traits = [ a.get_text().replace("\n", "") for a in self.soup.find(class_="traits-list-servant").find_all("a")]
            for trait in traits:
                self.attributes.append(trait)
            self.class_type = self.soup.find(class_='class-title').get_text().replace("\n", "").lower()
            self.rarity        = self.soup.find(class_='class-rarity').find(class_="field--label-hidden").get_text().replace("\n", "")

class Quest:
    def __init__(self, url, quest_name, quest_location, quest_singularity):
        print "Working on: " + url
        self.url               = url
        self.soup              = BeautifulSoup(requests.get(url).content, "html5lib") #parser doesn't work properly without html5lib in python2
        self.quest_name        = quest_name
        #self.quest_cost        = quest_cost
        self.quest_location    = quest_location
        self.quest_singularity = quest_singularity
        self.drops  = {} #maybe redesign this later, depending on how Comparator integration works
        self.quest_info = {}
        self.waves = {

        }
        self.setQuestInfo()
        self.setDrops()
        print "about to do enemies"
        self.setEnemies()
        print "done with enemies"
        self.soup.decompose()

    def __getitem__(self, key):
        query_chain = key.split('.')
        # [passive_skills, skills, Territory_Creation]
        if len(query_chain) > 1:
            value = getattr(self, query_chain[0]) #grab the base object
            if value: #if the base request exists, try to get next requests
                for i in range(1, len(query_chain)): #drill down into subparts of that object (dict, whatever)
                    if query_chain[i] in value:
                        value = value[query_chain[i]] #this allows us to get down into the noble_phantasms dictionary
                    else:
                        value = None
                        break
            return value
        else:
            return getattr(self, key)

    def printInfo(self):
        print self.quest_name + "\n"
        print self.quest_location + " - " + self.quest_singularity + "\n"
        print "AP cost: "   +  self.quest_info["ap_cost"]     + "\n"
        print "Bond Points" +  self.quest_info["bond_points"] + "\n"
        print "QP"          +  self.quest_info["qp"]          + "\n"
        print "Quest EXP"   +  self.quest_info["quest_exp"]   + "\n"
        print "Quest Type"  +  self.quest_info["quest_type"]  + "\n"  + "\n"

    def setQuestInfo(self):
        """
        gets us these paramaters:
            AP Cost	4
            Bond Points	35
            QP	780
            Quest EXP	14
            Quest Type	Free
        """

        table = self.soup.select("article table")[0]
        trs   = table.find_all("tr")

        #we only really want free quests soooo
        #maybe we should explicitly skip main quests? drop rates make no sense for main quests after all
        #hmm no, Quest as a class can't be biased against main quests. even if you can only run them once
        for i in range(len(trs)):
            tr = trs[i]
            th = tr.find("th")
            td = tr.find("td")

            tag_name = th.get_text().replace(" ", "_").lower()
            value    = td.get_text()
            self.quest_info[tag_name] = value

    def setEnemies(self):
        """
            .view-enemy-details-for-quest table tbody tr

            name (Skeleton - Bronze Lancer) .enemy-details-unit
            .views-field-field-quest-enemy-hp
            .views-field views-field-field-quest-enemy-level

            Maybe do .replace("\n", "") for a good measure, idk
        """
        tables = self.soup.select(".view-enemy-details-for-quest table tbody")

        self.waves = {}
        for i in range(len(tables)):
            self.waves["wave" + str(i + 1)] = {
                "enemies" : []
            }

        for i in range(len(tables)):
            table = tables[i]
            trs = table.find_all("tr")
            for tr in trs:
                url  = "https://gamepress.gg" + tr.find(class_="enemy-details-unit").find("a")["href"]
                enemy_name = url.split("/")[-1]
                file_name = "enemies/" + enemy_name + ".pkl" #folder for enemies
                file_exists = os.path.isfile(file_name)
                if not file_exists:
                    name = tr.find(class_="enemy-details-unit").find("a").get_text().replace(" ", "_").replace("\n", "").lower() #to make small or to not make small...
                    hp   = tr.find(class_="views-field-field-quest-enemy-hp").get_text().replace(" ", "").replace(",", "") #to make small or to not make small...

                    #some quests don't list the class, specifically if the enemies are randomized. although their class should be the same
                    class_img = tr.find(class_="views-field-field-class-rarity-image-1").find("img")
                    if class_img:
                        class_type_img_src = class_img["src"]

                        class_rarity_type_string = class_type_img_src.split("class_")[1].split(".png")[0]
                        rarity_number     = class_rarity_type_string[-1]
                        class_type_number = class_rarity_type_string[0:2] #grab first two bits

                        if rarity_number == "1":
                            rarity = "bronze"
                        elif rarity_number == "3":
                            rarity = "silver"
                        elif rarity_number == "4" or rarity_number == "5":
                            rarity = "gold"

                        #if class_type_number == "un":
                        #    class_type = "unknown" #probably???? beast, demon god pillar, etc
                        #else:
                        #    class_type = class_types[int(class_type_number) - 1] #this will work fine unless we get a 00 or something
                        if class_type_number == "un":
                            class_type = "unknown" #probably???? beast, demon god pillar, etc
                        elif int(class_type_number) == 1:
                            class_type = "saber"
                        elif int(class_type_number) == 2:
                            class_type = "lancer"
                        elif int(class_type_number) == 3:
                            class_type = "archer"
                        elif int(class_type_number) == 4:
                            class_type = "rider"
                        elif int(class_type_number) == 5:
                            class_type = "caster"
                        elif int(class_type_number) == 6:
                            class_type = "assassin"
                        elif int(class_type_number) == 7:
                            class_type = "berserker"
                        elif int(class_type_number) == 8:
                            class_type = "ruler"
                        elif int(class_type_number) == 10:
                            class_type = "avenger"
                        else:
                            class_type = "UNABLE_TO_FIND" #pendragon
                    else:
                        class_type = "???"
                        rarity     = "???"

                    #saber-training-ground-expert
                    #THIS QUEST HAS NO class icon for Saber (Altria Pendragon)
                    #wtf why gamepress whyyy I can grab it from her page, but why should I have to?
                    #"ArcherRandom" etc also exist

                    lvl  = tr.find(class_="views-field-field-quest-enemy-level").get_text().replace("\n", "").replace(" ", "") #to make small or to not make small...
                    enemy = Enemy(url, hp, name, class_type, lvl, rarity)
                    save_object(enemy, file_name)
                else:
                    enemy = load_object(file_name)
                    #if "random" in enemy_name:
                    #hp is kind a randomish, and saving different units under teh same file messes things up. only one hp value can be saved, and impossible to differentiate
                    hp   = tr.find(class_="views-field-field-quest-enemy-hp").get_text().replace(" ", "").replace(",", "") #to make small or to not make small...
                    enemy.hp = hp
                self.waves["wave" + str(i + 1)]["enemies"].append(enemy)

    def getHighestEnemyHP(self):
        highest_hp = 0
        for wave_name in self.waves:
            enemy_dict = self.waves[wave_name]
            enemies = enemy_dict["enemies"]
            for enemy in enemies:
                #print enemy.hp
                if int(enemy.hp) > highest_hp:
                    highest_hp = int(enemy.hp)

        return highest_hp

    def setDrops(self):
        """
            div.view-quest-drops table

            hmm https://gamepress.gg/grandorder/quest/massive-cavern
            does not list the drop rate for the Saber Monument...
            in that case.. do we just not include it?
            or how do we handle the drop_rate and runs_per_drop...
            knowing it can drop it is nice, but not knowing the drop rate is lame.

            For now, we will skip it.
        """
        trs = self.soup.find(class_="view-quest-drops").find("table").find_all("tr")

        for tr in trs:
            #should be two anchors, second one should have the item name and link
            a_s = tr.find_all("a")
            if len(a_s) == 0: #if the row is empty (basically)
                continue

            item_name = a_s[1].get_text().replace(" ", "_").lower()
            #print item_name
            #print "tr.get_text() before .split( ): " + tr.get_text()
            pieces = tr.get_text().split("%")
            if len(pieces) != 2: #if there is no drop rate information for the item (see above massive-cavern concern)
                continue
            item_rate = pieces[0].split(" ")[-1] #sneaky, hopefully works fine

            self.drops[item_name] = {}
            self.drops[item_name]["drop_rate"]     = item_rate
            #print "item_rate: " + item_rate
            self.drops[item_name]["runs_per_drop"] = str(100.0 / float(item_rate))

    def getDropRate(self, item_name):
        for item in self.drops:
            if item == item_name:
                return self.drops[item]["drop_rate"]

        return "-1" #will kill the process if we return 0, because division by zero is a no no

    def getRunsPerDrop(self, item_name):
        for item in self.drops:
            if item == item_name:
                return self.drops[item]["runs_per_drop"]
        return 0

    def printQuestRunDrops(self, objective=5):
        """
            Could have it color all the drops based on good, decent, and terrible

        Config 1: pretty good
            quest_name_color = u"\u001b[43;1m"
            great    = u"\u001b[42;1m\u001b[34m" #Background Cyan #text color Blue
            okay     = u"\u001b[46m\u001b[37;1m" #background yellow #text color green
            terrible = u"\u001b[41m\u001b[33;1m" #background red   #text color Magenta
            reset    = u"\u001b[0m"

        Config 2: okay ish, but gold is more attractive than blue, so have to change.. maybe do silver and gold? and black
            quest_name_color     = u"\u001b[42;1m"
            quest_location_color = u"\u001b[47;1m"
            great    = u"\u001b[46;1m\u001b[34m" #Background Cyan #text color Blue
            okay     = u"\u001b[43;1m\u001b[37;1m" #background yellow #text color green
            terrible = u"\u001b[41m\u001b[33;1m" #background red   #text color Magenta
            reset    = u"\u001b[0m"

        Config 3: decent, but not quite there. best doesn't look better than
            quest_name_color     = u"\u001b[42;1m"
            quest_location_color = u"\u001b[42m"
            great    = u"\u001b[43;1m\u001b[37;1m"
            okay     = u"\u001b[47;1m\u001b[33;1m"
            terrible = u"\u001b[41;1m\u001b[33;1m" #background red   #text color Magenta
            reset    = u"\u001b[0m"


        """
        quest_name_color     = u"\u001b[48;5;107m"
        quest_location_color = u"\u001b[48;5;107m"
        great    = u"\u001b[48;5;229m\u001b[30m"
        okay     = u"\u001b[48;5;220m\u001b[30m"
        terrible = u"\u001b[48;5;209m\u001b[30m" #background red   #text color Magenta
        reset    = u"\u001b[0m"

        print quest_name_color     + self.quest_name + reset
        print quest_location_color + self.quest_location + " - " + self.quest_singularity + reset

        best_drops = []
        okay_drops = []
        worst_drops = []
        for item_name in self.drops:
            #drops[item] is a percentage, like 19.9 (%) so need to divide by 100 first
            #print "item_name is: " + item_name + ", drop percentage is: " + self.drops[item_name]
            runs_per_drop = self.drops[item_name]["runs_per_drop"]

            runs = float(runs_per_drop)
            if runs < objective:
                temp = {}
                temp["text"] = great + item_name + ": " + runs_per_drop + " runs per drop" + reset
                temp["runs_per_drop"] = runs_per_drop
                best_drops.append(temp)
            elif runs > objective and runs < 2*objective:
                temp = {}
                temp["text"] = okay + item_name + ": " + runs_per_drop + " runs per drop" + reset
                temp["runs_per_drop"] = runs_per_drop
                okay_drops.append(temp)
            else:
                temp = {}
                temp["text"] = terrible + item_name + ": " + runs_per_drop + " runs per drop" + reset
                temp["runs_per_drop"] = runs_per_drop
                worst_drops.append(temp)

            #great = u"\u001b[46m\u001b[34m" if float(runs_per_drop) <= objective else ""
            #tearg = u"\u001b[0m" if great != "" else ""
            #print great + item_name + ": " + runs_per_drop + " runs per drop" + tearg

        #sort the respective lists
        #sorted(self.quests, key=lambda quest_dict: float(quest_dict["apd"]) / int(quest_dict["quest"].quest_info["ap_cost"])  )
        best_drops  = sorted(best_drops, key=lambda drop_dict: float(drop_dict["runs_per_drop"]) )
        okay_drops  = sorted(okay_drops, key=lambda drop_dict: float(drop_dict["runs_per_drop"]) )
        worst_drops = sorted(worst_drops, key=lambda drop_dict: float(drop_dict["runs_per_drop"]) )

        for item in best_drops:
            print item["text"]

        for item in okay_drops:
            print item["text"]

        for item in worst_drops:
            print item["text"]

        print ""

    def printQuestEnemyWaves(self, cutoffs=[40000,80000]):
        wave_name_color      = u"\u001b[48;5;109m"
        #enemy_name_color     = u"\u001b[48;5;107m"
        #enemy_class_color = u"\u001b[48;5;107m"
        great    = u"\u001b[48;5;229m\u001b[30m"
        okay     = u"\u001b[48;5;220m\u001b[30m"
        terrible = u"\u001b[48;5;209m\u001b[30m" #background red   #text color Magenta
        reset    = u"\u001b[0m"

        for wave_name in self.waves:
            print wave_name_color + wave_name + ":" + reset

            enemy_dict = self.waves[wave_name]
            enemies = enemy_dict["enemies"]
            wave_str = ""
            for enemy in enemies:
                hp = int(enemy.hp)
                if hp < cutoffs[0]:
                    wave_str += great + enemy.name + " " + enemy.class_type + "(" + enemy.hp + ")" + reset + "  "
                elif hp < cutoffs[1]:
                    wave_str += okay + enemy.name + " " + enemy.class_type + "(" + enemy.hp + ")" + reset + "  "
                else:
                    wave_str += terrible + enemy.name + " " + enemy.class_type + "(" + enemy.hp + ")" + reset + "  "
            print wave_str


    def getAPCost(self):
        return self.quest_info["ap_cost"]

    def isFreeQuest(self):
        quest_type = self.quest_info["quest_type"].lower()
        return quest_type == "free"

    def isDailyQuest(self):
        quest_type = self.quest_info["quest_type"].lower()
        return quest_type == "daily"

class DropList:
    ''' class designed to store all the data on a servant

        22 AP / Drop
        40 AP / Run
        40 AP * 1 drop
        --------------
        22 AP * 1 RUN

        = drops / run
    '''


    #constructor - downloads the servants profile upon being created and starts the chain of extraction

    def __init__(self, url):
        self.profile_url = url
        self.soup = BeautifulSoup(requests.get(url).content, "html5lib") #parser doesn't work properly without html5lib in python2
        self.quests = [] #list of Quest objects
        print "Working on item: " + url
        self.setDropLocations()
        self.soup.decompose() #handle memory

    def __getitem__(self, key):
        query_chain = key.split('.')
        # [passive_skills, skills, Territory_Creation]
        if len(query_chain) > 1:
            value = getattr(self, query_chain[0]) #grab the base object
            if value: #if the base request exists, try to get next requests
                for i in range(1, len(query_chain)): #drill down into subparts of that object (dict, whatever)
                    if query_chain[i] in value:
                        value = value[query_chain[i]] #this allows us to get down into the noble_phantasms dictionary
                    else:
                        value = None
                        break
            return value
        else:
            return getattr(self, key)

    def getQuests(self):
        return self.quests #although, this should just work with getitem i..e droplist["quests"]

    def setDropLocations(self):
        #locations = trs
        trs = self.soup.select(".view-best-drop-location table tr")


        #LANCER SECRET GEM PAGE HAS AN EMPTY ROW omg lol
        for i in range(1,len(trs)): #skip the header of the table
            tr = trs[i]
            empty_row = tr.find("a")
            if empty_row == None:
                continue
            quest_url      = "https://gamepress.gg" + tr.find("a")["href"]
            file_name = "quests/" + quest_url.split("/")[-1]
            file_exists = os.path.isfile(file_name)
            if not file_exists:
                quest_name     = tr.find("a").get_text()
                quest_singularity_info = tr.find("small").get_text().split(" - ")

                #commented out bits match gamepress way of doing it
                #quest_location = tr.find("small").find("a").get_text()
                if len(quest_singularity_info) == 3 and quest_singularity_info[0] == quest_singularity_info[2]:
                    quest_location    = quest_singularity_info[1]
                    quest_singularity = quest_singularity_info[0] #0 or 2 should work
                else:
                    quest_location = tr.find("small").find("a").get_text()
                    quest_singularity = quest_singularity_info[-1] #0 or 2 should work

                #the below will match exactly what is listed in gamepress. But I don't like it so I am doing the above
                #quest_singularity = tr.find("small").get_text().split(" - ")[-1] #oh boy, hope this works
                quest = Quest( quest_url, quest_name, quest_location, quest_singularity)
                save_object(quest, file_name)
            else:
                quest = load_object(file_name)
            #views-field views-field-field-ap-per-drop
            apd   = tr.find(class_="views-field-field-ap-per-drop").get_text()
            temp = {
                "quest" : quest,
                "apd"   : apd
            }
            self.quests.append( temp )
            #this doesnt store the APD anywhere... #nvm, fixed it
            #(self, url, quest_name, quest_location, quest_singularity):

    def printByDropPerRun(self, waves=False, objective=5):
        """
            22 AP / Drop
            40 AP / Run

            40 AP * 1 drop
            --------------
            22 AP * 1 RUN

            = drops / run

            thus we want
            ap_cost / apd = drop / run
            (ap_cost is really ap / run
                so we have (ap / run) / (ap / drop) and the aps cancel out
            )

            ACTUALLY We want the opposite.
            How many runs / 1 drop
        """
        sorted_quests = sorted(self.quests, key=lambda quest_dict: float(quest_dict["apd"]) / int(quest_dict["quest"].quest_info["ap_cost"])  )

        for quest_dict in sorted_quests:
            #will this actually go in order I wonder? or kinda randomish hmm
            #runperap = float(quest_dict["apd"]) / int(quest_dict["quest"].quest_info["ap_cost"])
            #print quest_dict["quest"].quest_name + " " + quest_dict["quest"].quest_location + " " + str(runperap) + "\n"
            #print "Printing Free Quest Drop Rates"
            if quest_dict["quest"].isFreeQuest() or quest_dict["quest"].isDailyQuest(): #only print free quests (cuz main quests tend to not have drop rates listed, and cannot be farmed)
                quest_dict["quest"].printQuestRunDrops(objective)
                if waves:
                    quest_dict["quest"].printQuestEnemyWaves()
                    print "" #give space between the quests

"""

"""

class Comparator:
    """
        Designed to allow us to test a servant (or probably any object)
        with multiple queries

        Currently handles special notation like noble_phantasms.np1.np_gain etc
        But the logic for that special handling should be moved inside the class itself.
        You should just be able to do:
            exampleServant['noble_phantasms.np1.np_gain']

        In a perfect world this would be unnecessary.
        However, due CasGil having gimped NP gain on his NP, only he has a difference between his normal np_gain
        and his NP np gain.
        So if you were to query AOE arts NPS with np gain >= 0.32 he would come up as valid, even though he is not.
        (0.16 np gain on NP)

        But inside of the class itself it can check if that field exists (only exists for casgil)
        and if it does return it, else return normal np_gain
    """
    def __init__(self):
        self.matches = [] #instance variables : means we can pickle some default settings if we so desire
        self.doGreaterOrLeast = False;
        self.doGreatest = False
        #self.#if doGreaterOrLeast is true then doGreatest tells us which

        self.greatest_query = {
            'attribute_name' : ""
        }
        self.least_query = {
            'attribute_name' : ""
        }
        self.queries = {
            'greater' : {

            },
            'exists' : [], #only one which is a list (cuz we are only checking for existance, can deal with or too)
            'less' :{

            },
            'contains' : {

            },
            'containsAny' : {

            },
            'containsAll' : {

            },
                #either can make use of containsAny
            'either' : [], #either attr 1 has what we want, or attr 2, or attr 3... has what we want

            'eitherAny' : { #either attr 1 has any of the ones we want for it, or attr 2 has any of the ones we want for it

            },
            'eitherAll' : { #either attr 1 has all of the ones we want, or attr 2 has all the ones we want

            },

        }

    def greatest(self, attr_name):
        self.greatest_query['attribute_name'] = attr_name
        doGreaterOrLeast = True
        doGreatest       = True
        return self

    def least(self, attr_name):
        self.least_query['attribute_name'] = attr_name
        doGreaterOrLeast = True
        doGreatest       = False
        return self

    def containsAny(self, attr_name, *targets):
        """
        used to check if a given element contains any strings that would be considered a match
        this is necessary becasue we store the classificatino of hte NP instead of the status (AOE versus SINGLE)
        Although.... might be a tag.
        Ex:
        containsAny("noble_phantasms.np1.classification|noble_phantasms.np2.classification", "Anti-Army", "Anti-World" )
        I guess we deal with the | or & later in the check method???
        """
        self.queries['containsAny'][attr_name] = targets #not sure if this works or not tbh
        return self

    def contains(self, attr_name, target):
        """
        used to check if the given attribute contains the given text
        """
        self.queries['contains'][attr_name] = target
        return self

    def containsAll(self, attr_name, *targets):
        self.queries['containsAll'][attr_name] = targets #not sure if this works or not tbh
        return self

    def either(self, attr_name):
        """
        """
        self.queries['either'].append(attr_name) #modified this for nicer syntax, although its a little weird
        return self

    def eitherAny(self, attr_name):

        """
            eitherAny (either of them can have any of their individuals)
            eitherAll (either of them must have all of their individuals )
            allAny? (i.e. we want all of them to have any of their individuals)
            allAll (i.e. we want all of them to have all of their individuals)
            What about eitherAny with > < = built in??? OH dang son
            we could use regular expressions and capture groups or some such to grab them..
            or we could use normal splits and then we can tell for sure
            eitherAny({
                "np_gain"             : ["8%", "10%", "15%"],
                "passive_skills.skills.Independent_Action.skill_desc" : ["8%", "10%", "15%"],
            })
        """
        self.queries['either'].append(attr_name) #modified this for nicer syntax, although its a little weird
        return self

    def clear(self):
        self.matches = []

    def greater(self, attr_name, target):
        self.queries['greater'][attr_name] = target
        return self

    def exists(self, attr_name):
        self.queries['exists'].append(attr_name)
        return self

    def less(self, attr_name, target):
        self.queries['less'][attr_name] = target
        return self

    def handleGreaterQuery(self, query, servant):
        """
            worst case has multiple slots to check with dots for
            noble_phantasms.np1.hit_count|noble_phantasms.np2.hit_count, "5"

            query = {

                "noble_phantasms.np1.hit_count|noble_phantasms.np2.hit_count" : "5",
                "np_gain" : "45"

            }

            query_attributes = [
                ['noble_phantasms', 'np1', 'hit_count'],
                ['noble_phantasms', 'np2', 'hit_count'],
            ]
        """
        passedAll = True
        for real_query in query.keys():
            target_value = query[real_query]

            query_attributes = [ chain for chain in real_query.split('|')  ]

            passedLocal = False
            for query_chain in query_attributes:
                value = servant[query_chain] #the servant __getitem__ method will handle the descent into dictionaries, etc
                if value == None:
                    continue
                else:
                    passedLocal |= (float(value) >= float(target_value))
            passedAll &= passedLocal
        return passedAll

    def handleLessQuery(self, query, servant):
        passedAll = True
        for real_query in query.keys():
            target_value = query[real_query]

            query_attributes = [ chain for chain in real_query.split('|')  ]

            passedLocal = False
            for query_chain in query_attributes:
                value = servant[query_chain] #the servant __getitem__ method will handle the descent into dictionaries, etc
                if value == None:
                    continue #since we use or here, will default to False if we query 1, else will match whatever else we query
                else:
                    passedLocal |= (float(value) <= float(target_value))
            passedAll &= passedLocal
        return passedAll

    def handleContainsQuery(self, query, servant):
        passedAll = True
        for real_query in query.keys():
            target_value = query[real_query]

            query_attributes = [ chain for chain in real_query.split('|')  ]

            passedLocal = False
            for query_chain in query_attributes:
                value = servant[query_chain] #the servant __getitem__ method will handle the descent into dictionaries, etc
                passedLocal |= (target_value in value)
            passedAll &= passedLocal
        return passedAll

    def handleContainsAnyQuery(self, query, servant):
        passedAll = True
        for real_query in query.keys():
            target_values = query[real_query]

            query_attributes = [ chain for chain in real_query.split('|')  ]

            passedLocal = False
            for query_chain in query_attributes:
                value = servant[query_chain] #the servant __getitem__ method will handle the descent into dictionaries, etc
                for target_value in target_values:
                    passedLocal |= (target_value in value)
            passedAll &= passedLocal
        return passedAll

    def handleContainsAllQuery(self, query, servant):
        return False


    def handleEitherQuery(self, query, servant):
        """
            handleEitherQuery is simple (contains or does not contain) kind of style
            teian:
            We could make this super robust using regular expressions.
            make a new function call it
            handleEitherREQuery
            for RegularExpressions
            ex:
                question is what do we put in there... as the argument, because REs can contain all the special keys we use to split
                {
                    "passive_skills.skills.Riding.skill_desc" : {
                        re : "([\d.]{1,5})%",
                        op : ">",
                        target : "15"
                    },
                    "passive_skills.skills.Independent_Action.skill_desc" : {
                        re : "([\d.]{1,5})%",
                        op : "<",
                        target : "10"
                    },
                    "noble_phantasms.np1.overcharge_effect_description" : {
                        re : "(special|Special)", #check for special attack damage (Gilgamesh, Oui, Jack)
                        op : "="
                        #no target for = types
                    }
                }
                either("passive_skills.skills.Riding.skill_desc([\d.]{1,5}%)>15%|passive_skills.skills.Independent_Action.skill_desc=(10%)")_
                then this would extract out the data
                or simply tell us if there is a match.
                If a match, then

                = is normal contains
                > is greater than
                < is less than



            #either("passive_skills.skills.Riding.skill_desc|passive_skills.skills.Independent_Action.skill_desc", "8%", "10%")_
            This is probably better:
                either("passive_skills.skills.Riding.skill_desc=8%|passive_skills.skills.Independent_Action.skill_desc=10%")_
            parallel dictionaries (basic idea)

        either("passive_skills.skills.Riding.skill_desc=8%|passive_skills.skills.Independent_Action.skill_desc=10%")_
        [
            "passive_skills.skills.Riding.skill_desc=8%|passive_skills.skills.Independent_Action.skill_desc=10%",
            "passive_skills.skills.Territory_Creation.skill_desc=15%|passive_skills.skills.Independent_Action.skill_desc=10%"
        ]

        New idea: not just equals,but

        """
        passedAll = False
        for queries in query: #since its a list
            real_queries = queries.split('|')

            passedLocal = False
            for real_query in real_queries:
                query_chain_val = real_query.split("=")
                query_chain     = query_chain_val[0]
                target_value    = query_chain_val[1]

                value = servant[query_chain] #the servant __getitem__ method will handle the descent into dictionaries, etc
                if value == None:
                    passedLocal |= False
                    continue
                passedLocal |= (target_value in value)
            passedAll |= passedLocal
        return passedAll

    def handleExistsQuery(self, query, servant):
        """
            exists("noble_phatasms.np1")
            exists("passive_skills.skills.Territory_Creation")
            query = ""
        """
        passedAll = True
        for attr in query:
            exists = servant[attr]
            print exists
            print "\n"
            passedAll &= (exists != None)
        return passedAll

    def handleQueryType(self, queryType, query, servant):
        #print(self.queries)
        if queryType == "greater":
            return self.handleGreaterQuery(query, servant)
        elif queryType == "less":
            return self.handleLessQuery(query, servant)
        elif queryType == "contains":
            return self.handleContainsQuery(query, servant)
        elif queryType == "containsAll":
            return self.handleContainsAllQuery(query, servant)
        elif queryType == "containsAny":
            return self.handleContainsAnyQuery(query, servant)
        elif queryType == "exists":
            return self.handleExistsQuery(query, servant)
        elif queryType == "either":
            return self.handleEitherQuery(query, servant)
        else:
            return False #something went wrong

    def check(self, servant):
        #greater = self.queries['greater']
        #least   = self.queries['least']
        #really ought to check exists first.
        # cuz we might get issues if we try to grab something that doesn't exist.
        # nonetype >= " " nontype <= "" etc. Hopefully these are null
        passed = True;
        for queryType in self.queries.keys():
            if len(self.queries[queryType]) > 0:
                passed &= self.handleQueryType(queryType, self.queries[queryType], servant)

        if passed:
            self.matches.append(servant)

    def getPassed(self):
        #here is where we implement the filter and only get the servant who matches everything
        #at the end we filter to do the greatest or least.
        return self.matches




#my_quest = Quest("https://gamepress.gg/grandorder/quest/crystal-palace-ruins", "Test Name", "Test Location", "Test Singularity")
#my_quest.printQuestEnemyWaves()
#print my_quest.waves
objective = 7 #anything that drops within seven runs
droplist_file_name = "droplists/" + test_item + ".pkl" #folder to hold all the droplists
droplist_exists = os.path.isfile(droplist_file_name)
if droplist_exists:
    droplist = load_object( droplist_file_name)
else:
    droplist = DropList(base_url + test_item)
    save_object(droplist, droplist_file_name)

droplist.printByDropPerRun(True, objective)
#droplist.printByDropPerRun(objective)

"""

query = Comparator().less("drops.evil_bone.runs_per_drop", "5").less("drops.void's_dust.runs_per_drop", "12")
for quest_dict in droplist.getQuests():
    query.check(quest_dict["quest"])

passed = query.getPassed()
for quest in passed:

        would be better to be able to pass in a parameter to printQuestRunDrops like so:
        {
            "evil_bone" : "5",
            "proof_hero" : "7"
        }
        to have it highlight those two things if they match those specific criteria

    quest.printQuestRunDrops(5)

if len(passed) == 0:
    print "Nothing matches your criteria :("
"""



