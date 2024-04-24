import os, sys, json
from datetime import datetime
import urllib.request
import hashlib
import requests

class OpenStopObject:
    # contains the data for the arb and qc files, and is able to download them
    # OpenStop.question_catalog_update_time()
    # OpenStop.advanced_question_catalog_update_time()

    def __init__(self):
        self.NORMAL_QC_url = "https://raw.githubusercontent.com/OPENER-next/OpenStop/master/assets/question_catalog/definition.json"
        self.ADVANCED_QC_url = "https://raw.githubusercontent.com/OPENER-next/OpenStop/master/assets/advanced_question_catalog/definition.json"
        self.NORMAL_ARB_url = "https://raw.githubusercontent.com/OPENER-next/OpenStop/master/assets/question_catalog/locales/en.arb"
        self.ADVANCED_ARB_url = "https://raw.githubusercontent.com/OPENER-next/OpenStop/master/assets/advanced_question_catalog/locales/en.arb"
        self.translations = {}
        self.question_catalog = []

    def question_catalog_update_time(self):
        # returns the date of the last commit of the question catalog
        r, p = HelperFunctions.get_repo_and_path_from_url(self.NORMAL_QC_url)
        return HelperFunctions.get_last_commit_date(r, p)

    def advanced_question_catalog_update_time(self):
        # returns the date of the last commit of the advanced question catalog
        r, p = HelperFunctions.get_repo_and_path_from_url(self.ADVANCED_QC_url)
        return HelperFunctions.get_last_commit_date(r, p)

    def load_translations(self):
        # loads the translations from the arb files
        for url in [self.NORMAL_ARB_url, self.ADVANCED_ARB_url]:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for key, value in data.items():
                    if not "@" in key:
                        self.translations[key] = value

    def get_string_from_arb_key(self, arb_key):
        # This function gets the (english) string from a given key like "@railroadAcousticWarningText"
        arb_key = arb_key.replace("@", "")
        if arb_key in self.translations:
            return self.translations[arb_key]
        else:
            return arb_key

    def load_question_catalogs(self):
        for url in [self.NORMAL_QC_url, self.ADVANCED_QC_url]:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                self.question_catalog.extend(data)
    
    def openstop_type_to_taginfo_type(self, s):
        return {
            "OpenWay": "way", 
            "ClosedWay": "area", 
            "Node":"node", 
            "Relation":"relation"
        }[s]    


class TagInfoObject:
    # enables us to generate a taginfo.json file, and add to the data in it
    # TIO.add_to_tags(key, value, object_types, description)
    # 
    def __init__(self):
        self.data = {}
        self.data["data_format"] = 1
        self.data["data_url"] = "https://raw.githubusercontent.com/OPENER-next/OpenStop-taginfo/main/taginfo.json"
        self.data["project"] = {
            "name": "OpenStop",
            "description": "App for collecting OpenStreetMap-compliant accessibility data in public transport",
            "project_url": "https://openstop.app/",
            "doc_url": "https://github.com/OPENER-next/OpenStop",
            "icon_url": "https://raw.githubusercontent.com/OPENER-next/OpenStop/master/web/favicon.png",
            "contact_name": "OPENER next",
            "contact_email": "openernext@etit.tu-chemnitz.de"
        }
        self.data["tags"] = []
        # a object to temporarily hold the list of questions for each combikey
        self.questions_for_tags = {}

    def get_last_taginfo_commit_date(self):
        # returns the date of the last commit of the taginfo.json file
        r, p = HelperFunctions.get_repo_and_path_from_url(self.data["data_url"])
        return HelperFunctions.get_last_commit_date(r, p)

    def add_to_questions_for_tags(self, key, value, question, elementtypes):
        if value == None:
            combikey = key
        else:
            combikey = key + "=" + value
        if combikey not in self.questions_for_tags:
            self.questions_for_tags[combikey] = {}
            self.questions_for_tags[combikey]["questions"] = []
            self.questions_for_tags[combikey]["elements"] = elementtypes
        self.questions_for_tags[combikey]["questions"].append(question)

    def add_to_tags(self, key, value, object_types, description):
        t = {}
        t["key"] = key
        if value != None:
            t["value"] = value
        t["object_types"] = object_types
        t["description"] = description
        self.data["tags"].append(t)

    def get_question_description(self, questions):
        # This function takes a list of questions and returns a description for taginfo for them
        # "Translate" the questions
        global openstop
        for i in range(len(questions)):
            questions[i] = openstop.get_string_from_arb_key(questions[i])
        # if there is only one question, return the description
        if len(questions) == 1:
            return "Added by \"" + questions[0] + "\" question."
        # if there are multiple questions, return the descriptions separated by a comma
        else:
            description = "Added by "
            # get the next-to-last element of the list questions
            nexttolast = questions[-2]
            for question in questions:
                if question == nexttolast:
                    description += "\"" + question + "\" and \"" + questions[-1] + "\" questions."
                    break
                else:
                    description += "\"" + question + "\", "
            return description

    def questions_for_tags_to_taginfo(self):
        for combikey, data in self.questions_for_tags.items():
            key = combikey.split("=")[0]
            try:
                value = combikey.split("=")[1]
                self.add_to_tags(key, value, data["elements"], self.get_question_description(data["questions"]))
            except IndexError:
                continue
                value = None
            

    def save_to_file(self, filename):
        with open(filename, "w", encoding="utf8") as f:
            f.write(json.dumps(self.data, indent=4, ensure_ascii=False))





class HelperFunctions:
    @staticmethod
    def get_repo_and_path_from_url(url):
        # returns the repo and path from a url
        # e.g. "https://raw.githubusercontent.com/OPENER-next/OpenStop/master/assets/question_catalog/definition.json"
        # returns "OPENER-next/OpenStop" and "assets/question_catalog/definition.json"
        # if the url is not a raw.githubusercontent.com url, returns None
        if "raw.githubusercontent.com" not in url:
            return None
        # remove the "https://raw.githubusercontent.com/" part
        url = url.replace("https://raw.githubusercontent.com/", "")
        # split the url at the second "/"
        repo = "/".join(url.split("/", 2)[:2])
        path = "/".join(url.split("/")[3:])
        return repo, path

    @staticmethod
    def get_last_commit_date(repo, path):
        url = f"https://api.github.com/repos/{repo}/commits?path={path}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            last_commit = data[0]
            last_commit_date = last_commit["commit"]["committer"]["date"]
            # The date is in the format "2021-08-31T12:00:00Z", so we need to convert it to a datetime object
            last_commit_date = datetime.strptime(last_commit_date, "%Y-%m-%dT%H:%M:%SZ")
            return datetime.now()
            return last_commit_date
            
        else:
            raise Exception("Failed to retrieve commit information for the file " + str(url) + " - " + str(response.status_code))

    @staticmethod
    def openstop_question_to_taginfo_questions_for_tags(questionDict, openstop_instance, taginfo_instance):
        # this is the main parsing function that will take a question from the question catalog and feed it into the taginfo-object 
        # questionDict is a single question from the question catalog
        # openstop_instance is an instance of the OpenStop class that the questions are from
        # taginfo_instance is an instance of the TagInfoObject class that the questions will be fed to
        if "input" not in questionDict["answer"]:
            return
        # if there is a value "osm_element" in the condition, get the elements and set them as objecttypes
        objecttypes = ["node", "way", "relation", "area"]
        if "conditions" in questionDict:
            if "osm_element" in questionDict["conditions"][0]:
                objecttypes = []
                # get what type of data is stored at question["conditions"][0]["osm_element"]
                if isinstance(questionDict["conditions"][0]["osm_element"], str):
                    objecttypes.append(openstop_instance.openstop_type_to_taginfo_type(questionDict["conditions"][0]["osm_element"]))
                elif isinstance(questionDict["conditions"][0]["osm_element"], list):
                    for t in questionDict["conditions"][0]["osm_element"]:
                        objecttypes.append(openstop_instance.openstop_type_to_taginfo_type(t))

        for answer in questionDict["answer"]["input"]:
            if "osm_tags" not in answer:
                continue
            for key, value in answer["osm_tags"].items():
                taginfo_instance.add_to_questions_for_tags(key, value, str(questionDict["question"]["text"]), objecttypes)

        # also recognize ["answer"]["constructor"] as a place where an osm tag can be found
        if "constructor" in questionDict["answer"]:
            for key, value in questionDict["answer"]["constructor"].items():
                taginfo_instance.add_to_questions_for_tags(key, None, str(questionDict["question"]["text"]), objecttypes)
   




def main():
    global taginfo, openstop
    # first, check if the last commit date for the taginfo.json file is more recent than the last commit date for the question catalogs
    if taginfo.get_last_taginfo_commit_date() > openstop.question_catalog_update_time() and taginfo.get_last_taginfo_commit_date() > openstop.advanced_question_catalog_update_time() and os.path.isfile("taginfo.json"):
        print("The taginfo.json file is more recent than the question catalogs.")
        return
    # if we are here, the question catalogs are more recent than the taginfo.json file and we need to regenerate the taginfo.json
    # load the question catalogs
    openstop.load_question_catalogs()
    # load the translations
    openstop.load_translations()
    # iterate over the question_catalog
    for question in openstop.question_catalog:
        HelperFunctions.openstop_question_to_taginfo_questions_for_tags(question, openstop, taginfo)
    # After we have generated the temporary questions_for_tags dictionary, we can add the data to the taginfo object    
    taginfo.questions_for_tags_to_taginfo()
    taginfo.save_to_file("taginfo.json")
    
if __name__ == "__main__":
    taginfo = TagInfoObject()
    openstop = OpenStopObject()
    main()







