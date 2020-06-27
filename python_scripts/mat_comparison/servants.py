"""
3/3/2020
To-do:
    To-DO:
    Add coloring for displaying skills, NP, passives, etc.
    like how we did with the drop lists

    menu for doing queries and such
    NP gain for noble phantasm fix so we can move the code for descension into objects
    back into Comparator

    Kinda done
    (!!!) store each servant in their own respective .pkl in their folder

    GET SKILL TOTALS done
    GET ASCENS TOTALS done
        this will allow us to calculate the most efficient path to max skilldom
        but we should also allow for the ? of how many skills to what levels.

        i.e.
        calculateEfficientPath([10,9,10]) #take 1 skill to 9, 2 to 10
        should also accept:
        calculateEfficientPath([10]) #take 1 skill to 9, 2 to 10
            #if we only care about taking one skill to 10

        but if we do this we should also have a way to set which we want:
        least runs total
        or
        least AP total
        prob AP ?? runs is faster theoretically though

    probably should make it so
    other functions handle None gracefully, like containsAll containsAny
    look at handleEitherQuery to see what I am talking about

    NOTE: idea: add in an asterisk * to our notation to allow for looping through
        objects whose names we do not know.
        Such as things like:

        ""

        "Passive_Skill1" : { details },
        "Passive_SKill2" : { details },

        This would allow us to check against all of them without knowing any of their names.
        We could search for anything with an effect containing arts and 15% or some such.

        Regular expressions should be implemented in several versions too,
        and we could also just have an advanced version that handles
        > < = as we wish without separating them into 3 different functions

    1.) grab class (DONE)
    2.) grab rarity (DONE)
    3.) grab passive skills (DONE)
    4.) mYBE GRAB asc reqs and mats (DONE)
        4.1) Get total asc reqs and total mat reqs DONE
    5.) write rest of comparator's (WORKING ON IT)
        5.1) eitherAny
        5.2) eitherAll
        5.3) containsAll
        5.4) handleEitherREQuery (description inside of handleEitherQuery)
            eitherAny (either of them can have any of their individuals)
                unique because current implementation of
            eitherAll (either of them must have all of their individuals )
            allAny? (i.e. we want all of them to have any of their individuals)
                same as containsAny multiple times (so easy to implement if we want)
            allAll (i.e. we want all of them to have all of their individuals)
                same as containsAll multiple times.


    NAME DOESN"T WORK FOR PEOPLE LIKE ARCHER OF SHINJUKU

    !!!!
    LOOKING INTO NP GAIN IN CONJUNCTION WITH NP DOESNT WORK FOR CASGIL CUZ HIS NP HAS DIFFERENT RATE
    COULD THEORETICALLY ACCOUNT FOR THIS IN THE Getter, but then how do we know if they are asking for NP gain or normal gain?
    OHHH noble_phantasms.np1.np_gain for np_gain, and if they have the same np gain as normal cards then just grab that instead
    wait, this doesn't work because we do the handling within the comparator class... hmm..
    we can move the logic (AND SHOULD) into the getter inside of servants.
    Then we can deal with the above case rather easily


    get all of the effect_types of all the servants
    and figure out appropriate tags to map them to
    like Quick + gets mapped to self_quick_up
    all the logic for storing the information in a server can be done automatically
    once we get those maps worked out

    look into storing objects in files
    as this would allow us to save and reload servant data from file
    (obviously we aim to store it all in a database eventually, but that is in due time)

    maybe create a command line interface that allows you to answer basic queries

    "Find servants with np gain above xyz and star generation above lmp"
    and and and and and and....
    you should be able to string together as many criteria as you want
    figure out how to design something like that.

    Before that, implement the attributes and tags that servants have
    including NP type, AOE, etc.
    NP stuff should be easy now that we have done skills

    Also need to figure out how to link skill upgrades to old skills.
    Maybe can use regex to do something like
        Replaces Collector EX after Interlude 3
        "Replaces ([\w\s]+) after"
        to extract the name of the one it is linked to, and then maybe
        store that,
        maybe add a "upgrade_to" attribute to the skills, idk.
        think of the best way to link them, considering backend stuff too

"""
from bs4 import BeautifulSoup
import bs4
from bs4.diagnose import diagnose
import requests
import re
import sys
import json
import cPickle as pickle #first time this runs it should save the servants to file
import os.path

base_url     = 'https://gamepress.gg'
test_servant = '/grandorder/servant/'
servants_filename = "servants/servants.pkl"
scrape   = True #os.path.isfile(servants_filename) #whether or not we need to download the servants
runQuery = False

if len(sys.argv) > 1:
    test_servant += sys.argv[1]
else:
    test_servant += 'edmond-dantes'


def filterMatTds(td):
    id = td["id"]
    return id == "ascension-total" or id == "skill-total" or id == "total-total"


class Servant:
    ''' class designed to store all the data on a servant

        TO DO:
        NEED TO GRAB CLASS, passives, etc
        ALSO NEED TO GRAB class skills / passives
        ALSO skill mats, ascension materials, and their QP costs, etc

        All the ids and things associated with the servant for pulling data:

        servant name
        div id='page-title'
            <h1>First Last</h1>


    '''


    #constructor - downloads the servants profile upon being created and starts the chain of extraction

    def __init__(self, url):
        #self.url = url #"https://gamepress.gg/grandorder/servant/altria-pendragon"
        #self.soup = "<h1>empty</h1>"
        #self.#html = "" #don't need if we have SOUP
        self.full_name       = "Archer of McMaster"
        self.first_name      = "Servant"
        self.last_name       = "McServant"
        self.attribute       = "earth"
        self.alignment       = "lawful_good"
        self.traits          = ["weak_to_enuma_elish"] #what about the ids associated with the traits hmm
        self.tags            = ["Atk Support"]
        self.base_attack     = 1734
        self.max_attack      = 11221
        self.grail_attack    = 12283
        self.base_hp         = 2222
        self.max_hp          = 15150
        self.grail_hp        = 16597
        self.growth_type     = 'Linear'
        self.servant_class   = "Default Class"
        self.noble_phantasms = {}
        self.ascension_mats  = {}
        self.skill_mats      = {}
        self.total_mats      = {}
        self.rarity          = "1"
        self.np_gain                 = 0.0
        self.defensive_np_gain       = 0.0
        self.star_absorption         = 104
        self.star_generation_per_hit = 10 #this is a percent

        self.card_hits = {
            'noble_phantasm' : 0,
            'buster' : 0,
            'arts'   : 0,
            'quick'  : 0,
        }
        self.card_numbers = {
            'buster' : 0,
            'arts'   : 0,
            'quick'  : 0,
        }
        self.bond_ce_name = "Default Bond CE"
        self.bond_ce_description = "Default Bond CE Description"
        self.bond_ce_effect_types = ["attack_up", "max_hp_up"] #etc

        self.skills = {
            'skill1' : {
                'name'   : "Default Skill 1",
                'effect' : "Increase all allies Attack by 20% for 3 turns",
                'cd'     : [],
                'types'  : ["party_attack_up", "self_crit_damage_up"],
                'values' : {
                    "party_attack_up"     : [],
                    "self_crit_damage_up" : []
                }#[ ['20%', '21%', '22%', '23%', '24%', '25%', '26%', '27%', '28%', '30%'],  ['30%', '32%', '34%', '36%', '38%', '40%', '42%', '44%', '46%', '50%']  ]
            },
            'skill2' : {
                'name'   : "Default Skill 2",
                'effect' : "Increase all allies Defense by 20% for 3 turns",
                'cd'     : [],
                'types'  : ["party_defense_up", "self_defense_up"],
                'values' : {
                    "party_defense_up"  : [],
                    "self_defense_up"   : []
                }#[ ['20%', '21%', '22%', '23%', '24%', '25%', '26%', '27%', '28%', '30%'],  ['30%', '32%', '34%', '36%', '38%', '40%', '42%', '44%', '46%', '50%']  ]
            },
            'skill3' : {
                'name'   : "Default Skill 3",
                'effect' : "Increase NP Gauge by 10% every turn for 3 turns",
                'cd'     : [],
                'types'  : ["self_np_gen_up"],
                'values' : {
                    "self_np_gen_up"     : []
                }#[ ['20%', '21%', '22%', '23%', '24%', '25%', '26%', '27%', '28%', '30%'],  ['30%', '32%', '34%', '36%', '38%', '40%', '42%', '44%', '46%', '50%']  ]
            }

        }
        self.passive_skills = {
            "count"  : 0,
            "skills" : {}
        }
        self.profile_url = url
        self.soup = BeautifulSoup(requests.get(url).content, "html5lib") #parser doesn't work properly without html5lib in python2
        print "Working on servant: " + url
        self.setServantName() #done
        self.setServantClassRarity()
        self.setServantNoblePhantasm()
        self.setServantCards() #partway done
        self.setServantNPGainAndStarGen() #done
        self.setServantAttackDefense()    #done
        self.setServantSkills() #basically done, aside from linking upgrades to their prior versions
        self.setServantPassives() #almost done
        self.setServantTraits() #this should also include attribute 'earth, heaven' etc and alignment
        self.setAscensionMats() #ascension-materials-table
        self.setSkillMats()
        self.setTotalMats()
        #self.setServantHitCounts()
        #partway done
        self.soup.decompose() #handle memory

    def __getitem__(self, key):
        query_chain = key.split('.')
        # [passive_skills, skills, Territory_Creation]
        if len(query_chain) > 1:
            if "noble_phantasms" in key and "np_gain" in key:
                #noble_phantasms.np1.np_gain

                gimped_np_gain = self.noble_phantasms[query_chain[1]]["np_gain"]
                if gimped_np_gain:
                    return gimped_np_gain
                else:
                    return self.np_gain
            else:
                #what if the thing they request doesn't exist (i.e. passive_skills.skills.Territory_Creation)
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

    def printServantInfo(self):
        print(self.getServantName())
        print(self.getServantClassRarity())
        print(self.getServantAttributes())
        print(self.getServantCards())
        print(self.getServantNPGainAndStarGen())
        print(self.getServantAttackDefense())
        print(self.getServantSkills())
        print(self.getServantPassives())
        #print(self.noble_phantasms)
        #print( json.dumps(self.getServantNoblePhantasm(), sort_keys=True, indent=4) )
        print( self.getServantNoblePhantasm() )
        print( self.getServantTraits() )
        print( self.getServantTags() )
        #print (self.getSkillMats())
        #print (self.getAscensionMats())

    def printSkillMats(self):
        """
            self.skill_mats = {
                "1" : {
                    "archer-piece" : "5"
                    "dragon-fang"  : "6"
                },
                "2" : {
                    "archer-piece" : "5"
                    "dragon-fang"  : "6"
                }
            }
        """
        #probably could / should switch skill_mats to a list
        # in order to enforce the ordering we want when printing we are going to do it manually ish
        # / in order, the keys are not in the order we want
        print "Skill Materials:"
        for i in range(1,10):
            text = str(i) + "->" + str(i + 1) + ": "
            mats = self.skill_mats[str(i)]
            for mat_name in mats:
                number_needed = mats[mat_name]
                text += mat_name + "(" + number_needed + ") "
            print text

    def printAscensionMats(self):
        """
            self.ascension_mats = {
                "1" : {
                    "archer-piece" : "5"
                    "dragon-fang"  : "6"
                },
                "Max" : {
                    "archer-piece" : "5"
                    "dragon-fang"  : "6"
                }
            }
        """
        #probably could / should switch skill_mats to a list
        print "Ascension Materials:"
        for i in range(2,5): #excludes 5
            level = str(i)
            text = level + ": "
            mats = self.ascension_mats[level]
            for mat_name in mats:
                number_needed = mats[mat_name]
                text += mat_name + "(" + number_needed + ") "
            print text

        #handle the max case
        mats = self.ascension_mats["Max"]
        text = "Max: "
        for mat_name in mats:
            number_needed = mats[mat_name]
            text += mat_name + "(" + number_needed + ") "
        print text



    def getServantName(self):
        return self.first_name + " " + self.last_name

    def getServantClassRarity(self):
        return "Class: " + self.servant_class + "\nRarity: " + self.rarity

    def getServantAttributes(self):
        return self.attribute + "\n" + self.alignment

    def getServantCards(self):
        cards = "Buster: " + str(self.card_numbers['buster']) + "\nQuick: " + str(self.card_numbers['quick']) + "\nArts: " + str(self.card_numbers['arts'])
        return cards

    def getServantNPGainAndStarGen(self):
        stats  = "NP Per Hit(%): "            + self.np_gain                  + "\n"
        stats += "NP When Attacked(%): "      + self.defensive_np_gain        + "\n"
        stats += "Star Absorption: "          + self.star_absorption          + "\n"
        stats += "Star Generation Per Hit: "  + self.star_generation_per_hit  + "\n"
        return stats

    def getServantAttackDefense(self):
        stats  = "Base Attack: "  + self.base_attack  + "  Base HP: "   + self.base_hp  + "\n"
        stats += "Max  Attack: "  + self.max_attack   + "  Max  HP: "   + self.max_hp   + "\n"
        stats += "Grail Attack: " + self.grail_attack + "  Grail  HP: " + self.grail_hp + "\n"
        return stats;

    def getServantSkills(self):
        #keys = ['skill1', 'skill2', 'skill3'] #we should use a method to grab the keys, but whatever
        skills = ""
        for i in range(len(self.skills.keys())):
            key = 'skill' + str(i + 1)
            skills += self.skills[key]['name'] + ":\n"
            skills += self.skills[key]['effect'] + "\n"
            for type in self.skills[key]['types']:
                skills += type + ": "
                for value in self.skills[key]['values'][type]:
                    skills += str(value) + " "
                skills += "\n"
            skills += "--------------------------\n"
            skills += "--------------------------\n\n"
        skills += "\n"
        return skills

    def getServantPassives(self):
        passives = ""
        for skill_generic_name in self.passive_skills["skills"].keys():
            skill_name = self.passive_skills["skills"][skill_generic_name]['skill_name']
            skill_desc = self.passive_skills["skills"][skill_generic_name]['skill_desc']
            passives += skill_name + ":\n"
            passives += skill_desc + "\n"
            passives += "--------------------------\n"
            passives += "--------------------------\n\n"
        return passives

    def getServantNoblePhantasm(self):
        text = ""
        nobles = self.noble_phantasms
        for np in self.noble_phantasms.keys(): #np1, np2, etc
            noble = nobles[np]
            text += noble["name"] + " " + noble["rank"] + " " + noble["hit_count"] + "\n"
            text += noble["classification"] + "\n"
            text += noble["lore"] + "\n"
            text += noble["effect"] + "\n"
            for effect in noble["effect_scale"].keys():
                text += effect + ": "
                text += " ".join(noble["effect_scale"][effect]) + "\n"
            for overcharge_effect in noble["overcharge_effect_description"]:
                text += "Overcharge effects:\n"
                text += overcharge_effect.replace("\n", "") + "\n"
            for overcharge_effect_type in noble["overcharge_effect_scale"].keys():
                text += overcharge_effect_type + " " + " ".join(noble["overcharge_effect_scale"][overcharge_effect_type])
            text += "\n\n"
        return text

    def simpleListDisplayText(self, title, lst, width=5):
        text = ""
        max_len = 0;

        for i in range(len(lst)):
            trait = lst[i]
            max_len += len(trait) + 3 #account for < > and space

            if i % width == 0:
                if i != 0:
                    text += "-\n"
                text += "-"
            text += "<" + trait + "> "
        text += "-\n"

        #create the table border
        front  = "-" * (max_len + 2) + "\n"
        #extra = len(title) % 2 == 1 ? 1 : 0
        #can add in one extra space if needed (check Merlin for verification)
        front += "-" + " " *((max_len - len(title))/2) + title + " " *((max_len - len(title))/2) + "-\n"
        front += "-" * (max_len + 2) + "\n"
        back   = "-" * (max_len + 2) + "\n"
        return front + text + back

    def prettyPrintDictionary(self, dict):
        print( json.dumps(dict, sort_keys=True, indent=4) )


    def getServantTraits(self):
        return self.simpleListDisplayText("Servant Traits:", self.traits)

    def getServantTags(self):
        return self.simpleListDisplayText("Servant Tags:", self.tags)

    def setServantName(self):
        '''
            servant name
            div id='page-title'
                <h1>First Last</h1>
        '''
        names = self.soup.find(id='page-title').find_all('h1')[0].get_text().split()
        if len(names) > 2:
            self.first_name = " ".join(names[0:-1])
            self.last_name  = names[-1]
        elif len(names) == 2:
            self.first_name = names[0]
            self.last_name  = names[1]
        else:
            self.first_name = names[0]
            self.last_name  = "" #none, like Gilgamesh

    def setServantClassRarity(self):
        self.servant_class = self.soup.find(class_='class-title').get_text().replace("\n", "")
        self.rarity        = self.soup.find(class_='class-rarity').find(class_="field--label-hidden").get_text().replace("\n", "")


    def servantNoblePhantasmHelper(self, np_name, np_number=0):
        """
            This will work, but will probably have to be tweaked when they release
            a second upgrade for any servant
        """

        #initialize the data structure
        # i.e. "base", "upgrade1", etc
        self.noble_phantasms[np_name] = {}

        #get name of NP
        name      = self.soup.select(".stats-np-table")[np_number].select(".sub-title")[0].get_text().replace("\n", "")
        lore      = self.soup.select(".stats-np-table")[np_number].find("p").get_text().replace("\n", "")
        np_tables = self.soup.select('.stats-np-table')[np_number].find_all('table');

        #card_type
        card_type_url = np_tables[0].find("img")['src']
        #card_type_match = re.search( r"Command_Card_([\w]+).png" ,np_tables[0].find("img")['src'])
        #card_type       = card_type_match.group(1)
        card_type = "default"
        if "Quick" in card_type_url:
            card_type = "Quick"
        elif "Buster" in card_type_url:
            card_type = "Buster"
        elif "Arts" in card_type_url:
            card_type = "Arts"

        #first table is rank classification hitcount
        rank_class_hitcount = [td.get_text() for td in np_tables[0].find_all('tr')[1].find_all('td')]

        #second table is the effect
        effect = np_tables[1].find('td').get_text().replace("\n", "") #hopefully there is only one td in every single one of these...

        #third table is effects scaling (although... what about Osakabehime and Merlin hmm..)
        # first row is Lvl 1 2 3 4 5
        # second row is effect_type 1 : scaling
        effects_rows = np_tables[2].find_all('tr')
        effect_scale = {} #temporary variable to store what we will put into the same named variable in the class

        for i in range(1, len(effects_rows)): #skip the first one, becasue it's just "Lvl 1 2 3 4 5"
            row = effects_rows[i]
            effect_type               = row.find('th').get_text().replace("\n", "")
            effect_type_scale         = [td.get_text() for td in row.find_all('td')]
            effect_scale[effect_type] = effect_type_scale

        #fourth table is overcharge effect
        #had to change from grabbing p.text to td.text because Mephistopheles doesn't have a p in his NP2 table overcharge area
        overcharge_effect_ps = [td.get_text() for td in np_tables[3].select("td.oc-effect")]

        #fifth table is overcharge effects scaling
        overcharge_effects_rows = np_tables[4].find_all('tr')
        overcharge_effect_scale = {} #temporary variable to store what we will put into the same named variable in the class
        for i in range(1, len(overcharge_effects_rows)):
            row = overcharge_effects_rows[i]
            overcharge_effect_type               = row.find('th').get_text().replace("\n", "")
            overcharge_effect_type_scale         = [td.get_text() for td in row.find_all('td')]
            overcharge_effect_scale[overcharge_effect_type] = overcharge_effect_type_scale

        #maybe should grap paragraphs separately hmm..

        self.noble_phantasms[np_name]['name']                          = name
        self.noble_phantasms[np_name]['lore']                          = lore
        self.noble_phantasms[np_name]['rank']                          = rank_class_hitcount[0]
        self.noble_phantasms[np_name]['effect']                        = effect
        self.noble_phantasms[np_name]['hit_count']                     = rank_class_hitcount[2]
        self.noble_phantasms[np_name]['card_type']                     = card_type
        self.noble_phantasms[np_name]['effect_scale']                  = effect_scale
        self.noble_phantasms[np_name]['classification']                = rank_class_hitcount[1]
        self.noble_phantasms[np_name]['overcharge_effect_scale']       = overcharge_effect_scale
        self.noble_phantasms[np_name]['overcharge_effect_description'] = overcharge_effect_ps

        #if there is gimped NP gain (cough CasGil) deal with it
        gimped_np_table = self.soup.find(class_="per-hit-table")
        if gimped_np_table and len(gimped_np_table) > 0:
            #we have gimped NP gain boys aww yeah
            #modify this if we get a servant with different NP gain on different cards
            #right now we ignore all cards except NP
            #grab gimp np for noble phantasm
            gimped_np = gimped_np_table.find_all("td")[-1].get_text().replace("\n", "")
            self.noble_phantasms[np_name]['np_gain'] = gimped_np

    def setServantNoblePhantasm(self):
        tables = self.soup.select(".stats-np-table")
        for i in range(len(tables)):
            self.servantNoblePhantasmHelper("np" + str(i + 1), i)

    def setServantCards(self):
        '''
        field field--name-field-command-cards field--type-entity-reference field--label-hidden field__items
        taxonomy-term vocabulary-command-card <div>
        about=/grandorder/quick-card
        '''

        cards = [ c['about'].split('/')[-1] for c in self.soup.find_all(class_='vocabulary-command-card')]
        for c in cards:
            quick  = 'quick'  in c
            buster = 'buster' in c
            arts   = 'arts'   in c
            if quick:
                self.card_numbers['quick' ] += 1
            elif buster:
                self.card_numbers['buster'] += 1
            elif arts:
                self.card_numbers['arts'  ] += 1

    def setServantNPGainAndStarGen(self):
        print(self.profile_url)
        data = [ td.get_text() for td in self.soup.select('.np-charge-table td')]
        #print(data)
        self.np_gain                 = data[0].replace("%", "")
        self.defensive_np_gain       = data[1].replace("%", "")
        self.star_absorption         = data[2].replace("%", "")
        self.star_generation_per_hit = data[3].replace("%", "")

    def setServantAttackDefense(self):
        stats = [ td.get_text() for td in self.soup.select('#atkhp-table td')]
        #base base max max grail grail
        self.base_attack  = stats[0]
        self.base_hp      = stats[1]
        self.max_attack   = stats[2]
        self.max_hp       = stats[3]
        self.grail_attack = stats[4]
        self.grail_hp     = stats[5]

    #set to grab rows instead of tds
    def setServantSkills(self):
        skill_names  = [ skill.get_text() for skill in self.soup.select('#skills .servant-skill .field--name-title')]
        skill_desc   = [ skill.get_text() for skill in self.soup.select('#skills .servant-skill-right p')]
        skill_tables = [ table for table in self.soup.select('div#skills .stats-skill-table table')]

        #archer of shinjuku is missing a <p> tag for his skill upgrade so have to do some janky shit
        if len(skill_tables) != len(skill_desc):
            skill_desc = []
            elements = self.soup.select('#skills .servant-skill-right')

            for element in elements:
                p = element.find("p")
                if p:
                    skill_desc.append(p.get_text())
                else:
                    text = ""
                    for c in element.children:
                        if isinstance(c, bs4.element.NavigableString):
                            text += c
                    skill_desc.append(text)

        #we need to set the skills that don't exist yet
        for i in range(len(skill_tables)):
            self.skills["skill" + str(i + 1)]           = {}

        for i in range(len(skill_tables)):
            self.skills["skill" + str(i + 1)]['name'] = skill_names[i]

        for i in range(len(skill_tables)):
            self.skills["skill" + str(i + 1)]['effect'] = skill_desc[i]

        skill_num = 1
        for table in skill_tables:
            trs = table.select("tr:not(:empty)") #this selector is required because Mephistopheles has an empty <tr> in his skill tables :[
            values = {};
            num_rows     = len(trs)
            effect_types = []
            #first, skill cooldowns
            cds = [ td.get_text() for td in trs[-1].find_all("td")] #last row always has cooldowns
            self.skills['skill' + (str(skill_num))]['cd'] = cds

            for i in range(1, num_rows - 1): #exclude the cooldowns and the levels (unless you want to include them..)
                row = trs[i] #grab current/next
                effect_type = row.find("th").get_text().replace("\n", "")
                effect_types.append(effect_type) #eg "Quick +"
                effect_values = [ td.get_text().replace("\n", "") for td in row.find_all("td")]
                values[effect_type] = effect_values

            self.skills['skill' + (str(skill_num))]['values'] = values
            self.skills['skill' + (str(skill_num))]['types']  = effect_types
            skill_num += 1

    def setServantPassives(self):
        # MATA HARI HAS NO PASSIVES LISTED SO THIS BREAKS HAVE TO FIX
        #should be pretty similar in design to setServantSkills
        # .view-class-skills-node
        #    .right-class-skills
        #       <a> Skill Title </a>
        #       <p> Skill Description </p>
        # There is probably some skills that don't have the description in a p, which we will have to fix eventually
        #
        """
            Want to be able to do something like
            Hmm need to be able to check the value of the passives...
            Ought to replace the spaces with underscores so we can do the notation below
            exists("passive_skills.Territory_Creation")
            contains("passive_skills.Territory_Creation", "10%")

            hmmm no this won't work... the problem is there are passive NAMES
            and they have ranks too
            like C+, EX, A+
            we can't descend into the data structure with approximately accurate keynames
            we can, however, crawl a predefined list of names
            like
            passive_skills {
                count : 3,
                skills : {
                    "Territory_Creation" : {
                        #skill_type : "Territory_Creation", #remove rank? or just search the skill_desc for "arts" and for "8%"??
                        skill_name : "Territory_Creation_C+",
                        skill_desc : "Increase arts cards effectiveness by 8%"
                    }
                }

            }
            exists("passive_skills.skills.Territory_Creation").contains("passive_skills.skills.Territory_Creation.skill_desc", "10%")
            map the generic skill type name to the actual version?
            if want to be able to search the description for two phrases should we implement an & option?
            contains("passive_skills.skills", "Territory_Creation")
            contains("passive_skills.names", "Territory_Creation")

        """
        passive_skills = [div for div in self.soup.select(".view-class-skills-node .right-class-skills")]

        for skill in passive_skills:
            has_skill = skill.find("a")
            if not has_skill:#or has_skill is None:
                continue
            skill_name         = skill.find("a").get_text().replace("\n", "")
            skill_generic_name = "_".join(skill_name.split(" ")[0:-1]) #hopefully grabs all but the last (rank)
            skill_name = skill_name.replace(" ", "_")

            if skill.find("p"):
                skill_desc = skill.find("p").get_text().replace("\n", "")
            else:
                skill_desc = ""
                for c in skill.children:
                    if isinstance(c, bs4.element.NavigableString):
                        skill_desc += c.get_text().replace("\n", "")
            temp = {}
            temp["skill_name"] = skill_name
            temp["skill_desc"] = skill_desc
            self.passive_skills['skills'][skill_generic_name] = temp
            self.passive_skills['count'] += 1


    def setServantTraits(self):
        attr_align = [ a.get_text() for a in self.soup.find(class_='attri-align-table').find_all('a')]
        self.attribute = attr_align[0]
        self.alignment = attr_align[1]

        traits = [ a.get_text().replace("\n", "") for a in self.soup.find(class_="traits-list-servant").find_all("a")]
        self.traits = traits

    def setServantTags(self):
        tags = [ a.get_text().replace("\n", "") for a in self.soup.find(class_="servant-tags-list").find_all("a")]
        self.tags = tags

    def setAscensionMats(self):
        table = self.soup.find(id="ascension-materials-table")
        trs   = table.find_all(class_="ascension-row")

        for tr in trs:
            tds = tr.find_all("td")
            ascension_stage = tds[0].get_text().replace(" ", "")
            cost = tds[1].get_text().replace(" ", "").replace(",", "")
            mat_container = tds[2]
            #div.paragraph--type--required-materials
                #.field--name-field-number-of-materials (x5)
                #field--name-field-item-icon
                    #a href .split("/")[-1] this will yield something like "archer-piece"
            mats = mat_container.find_all(class_="paragraph--type--required-materials")
            ascension_mats = {}

            for mat in mats:
                number = mat.find(class_="field--name-field-number-of-materials").get_text().replace("\n", "").replace(" ", "").replace("x", "")
                mat_name = mat.find(class_="field--name-field-item-icon").find("a")["href"].split("/")[-1]
                ascension_mats[mat_name] = number

            self.ascension_mats[ascension_stage] = ascension_mats

    def setSkillMats(self):
        #id = Skill-materials-table
        table = self.soup.find(id="Skill-materials-table")
        trs   = table.find_all(class_="skill-row")

        for tr in trs:
            tds = tr.find_all("td")
            skill_number  = tds[0].get_text().replace("\n", "")
            numbers = skill_number.split(" ")
            from_number = numbers[0]
            #don't need to_number because it's implied. 1 goes to 2 2 goes to 3 etc
            #to_number   = numbers[2] #1 -> 2

            cost = tds[1].get_text().replace(" ", "").replace(",", "")
            mat_container = tds[2]
            #div.paragraph--type--required-materials
                #.field--name-field-number-of-materials (x5)
                #field--name-field-item-icon
                    #a href .split("/")[-1] this will yield something like "archer-piece"
            mats = mat_container.find_all(class_="paragraph--type--required-materials")
            skill_mats = {}

            for mat in mats:
                number   = mat.find(class_="field--name-field-number-of-materials").get_text().replace("\n", "").replace(" ", "").replace("x", "")
                mat_name = mat.find(class_="field--name-field-item-icon").find("a")["href"].split("/")[-1]
                skill_mats[mat_name] = number

            self.skill_mats[from_number] = skill_mats

    def getTotalMats(self, skill_numbers=[10,10,10], ascension_aim = "Max"):
        """
            Not done yet

        total_mats = {
            "ascension-total" : {
                #"archer-piece" : 5 #ints, unlike the rest of my entire class definitions
            },
            "skill-total" : {

            },
            "total-total" : {

            }
        }
        times = {
            "10" : 2
            "9"  : 1
        }

        times = {}
        totals = {}
        #totals = {
        #  "mat_name" : 5, #etc
        #
        #}
        for skill_num in skill_numbers: #figure out how many times to multiply at each step
            if skill_num in times:
                times[str(skill_num)] += 1
            else:
                times[str(skill_num)] = 1
        """
        totals = {}
        for i in range(9):
            from_skill_num = i + 1
            mats = self.skill_mats[str(from_skill_num)]
            for mat_name in mats:
                total = 0
                mat_amount = int(mats[mat_name])
                for target_level in skill_numbers:
                    if from_skill_num < target_level:
                        total += mat_amount
                if not(mat_name in totals): #same mats may appear multipl times, so have to add, not set
                    totals[mat_name] = 0
                totals[mat_name] += total
        #print totals fine here
        #ascension_aim = 2, 3, 4 "Max"

        limit = 4 if ascension_aim == "Max" else int(ascension_aim)

        for i in range(2, limit + 1):
            mats = self.ascension_mats[str(i)]

            for mat_name in mats:
                mat_amount = int(mats[mat_name])
                if not(mat_name in totals): #same mats may appear multipl times, so have to add, not set
                    totals[mat_name] = 0
                totals[mat_name] += mat_amount

        if ascension_aim == "Max":
            mats = self.ascension_mats["Max"]
            for mat_name in mats:
                mat_amount = int(mats[mat_name])
                if not(mat_name in totals): #same mats may appear multipl times, so have to add, not set
                    totals[mat_name] = 0
                totals[mat_name] += mat_amount

        return totals

    def printTotalMats(self, skill_numbers=[10,10,10], ascension_aim = "Max"):
        """
        if skill_numbers == [10,10,10] and ascension_aim == "Max":
            total_mats = self.total_mats["total-total"]
        else:
            total_mats = self.getTotalMats(skill_numbers, ascension_aim)
        """
        total_mats = self.getTotalMats(skill_numbers, ascension_aim)
        text = ""
        for mat_name in total_mats:
            number_needed = total_mats[mat_name] #I think this one is actually an int
            text += mat_name + "(" + str(number_needed) + ") "
        print text

    def setTotalMats(self):
        """
            should be able to refactor this since the basic code for extracting mats
            is the same across the three methods (setAscen, setSkill, setTotal)

            DOESN"T WORK BECAUSE IT USES JAVASCRIPT.
            BUT, we can do the same thing. :)
        """
        total_mats = {
            "ascension-total" : {

            },
            "skill-total" : {

            },
            "total-total" : {

            }
        }

        for key in self.ascension_mats:
            item_dict = self.ascension_mats[key]
            for item_name in item_dict:
                item_amount = item_dict[item_name]
                if item_name in total_mats["ascension-total"]:
                    total_mats["ascension-total"][item_name] += int(item_amount)
                else:
                    total_mats["ascension-total"][item_name] = 0
                    total_mats["ascension-total"][item_name] += int(item_amount)

                if item_name in total_mats["total-total"]:
                    total_mats["total-total"][item_name] += int(item_amount)
                else:
                    total_mats["total-total"][item_name] = 0
                    total_mats["total-total"][item_name] += int(item_amount)

        for key in self.skill_mats:
            item_dict = self.skill_mats[key]
            for item_name in item_dict:
                item_amount = item_dict[item_name]
                if item_name in total_mats["skill-total"]:
                    total_mats["skill-total"][item_name] += 3*int(item_amount)
                else:
                    total_mats["skill-total"][item_name] = 0
                    total_mats["skill-total"][item_name] += 3*int(item_amount)

                if item_name in total_mats["total-total"]:
                    total_mats["total-total"][item_name] += 3*int(item_amount)
                else:
                    total_mats["total-total"][item_name] = 0
                    total_mats["total-total"][item_name] += 3*int(item_amount)


        self.total_mats = total_mats




"""
    How are we going to design a flexible extensible limitless method of filtering and comparing items
    hmm
    greater than fixed constant
    less than fixed constant


    if we include
        greatest
        least
    then we have to change how it works because it will only return one object.
    "The servant with the greatest attack AND np gain > 1.05% AND ..."
    To be fair ,that is a simple filter after the fact.
    Or to streamline things, we could simply check the attacks once the other conditions are met.

    So greatest or least can only select one attribute/stat
    to be checked after all the others are satisfied

    To use a non-class based approach we could have a list of attributes like so:
    Example:
    servant with the greatest attack AND Arts AOE NP AND NP Gain > 1.05% AND >3 hits on NP
    {

    }

    maybe do chaining
    Should fundamentally be able to handle | to allow for checking of multiple slots
    and should be able to handle special . notation for dictionary access
    query = (new Comparison()).greatest("max_attack").containsAny("noble_phantasms.np1.classification|noble_phantasms.np2.classification", "Anti-Army", "Anti-World" ).greater("np_gain", 1.05).greater("noble_phantasms.np1.hit_count|noble_phantasms.np2.hit_count", "5")

    query.check(servant[i])
    #stores all the servants that match the query
    #or only one if greatest or least is checked.
    #cannot use greatest and least together and cannot use greatest or least twice

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
                passedLocal |= (value >= target_value)
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
                passedLocal |= (value <= target_value)
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





if scrape:
    site = requests.get("https://gamepress.gg/grandorder/servants")
    #"servants-new-list"

    file = BeautifulSoup(site.content, 'html.parser')
    trs = file.find_all(class_="servants-new-row")
    #print(trs)
    servant_links = []
    for tr in trs:
        tier_row = tr.find(class_="servant-tier")
        link_row = tr.find(class_="servant-title")
        if tier_row and tier_row.get_text() != "": #i.e. if they are not a BEAST or untiered
            servant_links.append(base_url + link_row.find("a")['href'])


    servants = []
    for url in servant_links:
        servant_link_name = url.split("/")[-1]
        file_name = "servants/" + servant_link_name + ".pkl"

        if os.path.isfile(file_name):
            servant = load_object(file_name)
        else:
            servant = Servant(url)
            save_object(servant, file_name)

        servants.append(servant)

    #servants = [Servant(url) for url in servant_links]

    #save the file containing all of them, for easy filtering / queries
    save_object(servants, servants_filename)

    """
    query = Comparator().greater("noble_phantasms.np1.hit_count", "10").greater("np_gain", "1")

    for servant in servants:
        query.check(servant)
        #get all their info and store it

    passed_servants = query.getPassed()
    if len(passed_servants) > 0:
        for s in passed_servants:
            print(s['first_name'] + " " + s['last_name'])
    else:
        print("No servants meet your criteria")
    """


if runQuery:
    #load servants
    servants = load_object(servants_filename)

    query = Comparator().greater("noble_phantasms.np1.hit_count", "4").greater("np_gain", "0.75")
    query.check(test)
    servants = query.getPassed()
    if len(servants) > 0:
        for servant in query.getPassed():
            print(servant['first_name'] + " " + servant['last_name'])
    else:
        print("No servants meet your criteria")


#if singleServantQuery:
#default run
    #test = Servant(base_url + test_servant)
#print test.ascension_mats
#test.printSkillMats()
#test.printAscensionMats()
    #test.printTotalMats([8,10,10], 3)#works now hurray
#test.printSkillMats()
#test.printAscensionMats()
#print test.skill_mats
#print test.ascension_mats
#query = Comparator() #.greater("noble_phantasms.np1.hit_count", "7").less("np_gain", "1.00") #.exists("passive_skills.skills.Territory_Creation")
#query.contains("skills.skill1.effect|skills.skill2.effect|skills.skill3.effect", "own ATK") #works
#not sure how to deal with skill upgrades, although at max there would be 6 to check probably
#contains should have an or optoin for the
#actually, nvm, that is containsAny
#query.contains("passive_skills.skills.Riding.skill_desc", "8%") #this also works HURRAY
#query.containsAny("passive_skills.skills.Riding.skill_desc", "6%", "7%", "8%") #this also works HURRAY
#query.containsAny("passive_skills.skills.Riding.skill_desc|passive_skills.skills.Independent_Action.skill_desc", "8%") #this also works HURRAY
#query.either("passive_skills.skills.Riding.skill_desc=4%|passive_skills.skills.Independent_Action.skill_desc=5%|passive_skills.skills.Magic_Resistance.skill_desc=17.5%")

#should design a contains either or on
#right now it checks if riding or independent satisfies all of them.
#we should be able to check if either riding is above 8 or independent is above 10
# not just whether or not they both are
#query.check(test)
#print(query.getPassed())
#test.printServantInfo()

"""
#this works now.
Apparently I was using class variables instead of instance variables... oops.
Probably could have fixed by simply initializing the instance variable
saveTrial1 = False
if saveTrial1:
    test = Servant(base_url + test_servant)
    test.printServantInfo()
    save_object(test, test_servant.split("/")[-1] + ".pkl")
else:
    test = load_object(test_servant.split("/")[-1] + ".pkl")
    test.printServantInfo();
"""
def getServantData(url):
    """
    create list? with the data (maybe object that automates everything)
    open url using requests (maybe overkill, but idk)
    grab essential data
    """
    pass





