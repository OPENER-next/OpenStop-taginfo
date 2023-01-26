import os, sys, json
from datetime import datetime
import urllib.request
import hashlib

TAGINFO = {}

# before we change anything, we need to make sure that something changed
# if nothing changed, we don't want to create a new commit

# load the file "taginfo.json"
with open("taginfo.json", "r", encoding="utf8") as f:
	taginfo = json.loads(f.read())

# read the md5 of the previous taginfo.json
previous_md5 = taginfo["project"]["catalog-md5"] 




# Set up the basic parameters
TAGINFO["data_format"] = 1
TAGINFO["data_url"] = "https://raw.githubusercontent.com/OPENER-next/OpenStop-taginfo/main/taginfo.json"
TAGINFO["project"] = {
	"name": "OpenStop",
	"description": "App for collecting OpenStreetMap-compliant accessibility data in public transport",
	"project_url": "https://openstop.app/",
	"doc_url": "https://github.com/OPENER-next/OpenStop",
	"icon_url": "https://raw.githubusercontent.com/OPENER-next/OpenStop/master/web/favicon.png",
	"contact_name": "OPENER next",
	"contact_email": "openernext@etit.tu-chemnitz.de"
}
TAGINFO["tags"] = []

TAGS = []

questions_for_tags = {}

def AddToQuestionsForTags(key, value, question, elementtypes):
	global questions_for_tags
	combikey = key + "=" + value
	if combikey not in questions_for_tags:
		questions_for_tags[combikey] = {}
		questions_for_tags[combikey]["questions"] = []
		questions_for_tags[combikey]["elements"] = elementtypes
	questions_for_tags[combikey]["questions"].append(question)


def getQuestionDescription(questions):
	# if there is only one question, return the description
	if len(questions) == 1:
		return "Added by \"" + questions[0] + "\" question."
	# if there are multiple questions, return the descriptions separated by a comma
	else:
		description = " Added by \""
		# get the next-to-last element of the list questions
		nexttolast = questions[-2]
		for question in questions:
			if question == nexttolast:
				description += question + "\" and \"" + questions[-1] + "\" questions."
				break
			else:
				description += "\"" + question + "\", "
		return description



def AddToTags(key, value, object_types, description):
	global TAGS
	t = {}
	t["key"] = key
	if value != None:
		t["value"] = value
	t["object_types"] = object_types
	t["description"] = description
	TAGS.append(t)

def OpenStopTypeToTaginfoType(s):
	d = {"OpenWay": "way", "ClosedWay": "area", "Node":"node", "Relation":"relation"}
	return d[s]



# the directory where the .json-Files are located
json_dir = ""

# load the files "map_feature_collection.json" and "question_catalog.json"
# Download the files from GitHub
urllib.request.urlretrieve("https://raw.githubusercontent.com/OPENER-next/OpenStop/master/assets/datasets/map_feature_collection.json", os.path.join(json_dir, "map_feature_collection.json"))
urllib.request.urlretrieve("https://raw.githubusercontent.com/OPENER-next/OpenStop/master/assets/datasets/question_catalog.json", os.path.join(json_dir, "question_catalog.json"))

# load the file "map_feature_collection.json"
with open(os.path.join(json_dir, "map_feature_collection.json")) as f:
	map_feature_collection = json.load(f)

# load the file "question_catalog.json"
with open(os.path.join(json_dir, "question_catalog.json"), "r", encoding="utf8") as f:
	question_catalog = json.load(f)



# Deactivated for now, there is no real reason we want to display the *single* tags used to display the map features
# If we would, why wouldn't we also want to display the tags used as conditions for the questions?
"""
# iterate over the map_feature_collection
for feature in map_feature_collection:
	for condition in feature["conditions"]:
		# if condition["osm_element"] is not set, then object_types = ["node", "way", "relation"]
		# if condition["osm_element"] is a single string, parse it and set object_types accordingly
		# if condition["osm_element"] is a list of strings, parse it and set object_types accordingly
		object_types = []
		if "osm_element" not in condition:
			object_types = ["node", "way", "relation"]
		elif isinstance(condition["osm_element"], str):
			if condition["osm_element"] == "Node":
				object_types = ["node"]
			elif condition["osm_element"] == "OpenWay":
				object_types = ["way"]
			elif condition["osm_element"] == "ClosedWay":
				object_types = ["way"]
			elif condition["osm_element"] == "Relation":
				object_types = ["relation"]
		# if object_types is still empty, then set it to ["node", "way", "relation", "area"]
		if len(object_types) == 0:
			object_types = ["node", "way", "relation", "area"]
		for key, value in condition["osm_tags"].items():
			AddToTags(key, value, object_types, "Used to identify and display \"" + str(feature["name"]) + "\" on the map.")
"""



# iterate over the question_catalog
for question in question_catalog:
	if "input" not in question["answer"]:
		continue
	# if there is a value "osm_element" in the condition, get the elements and set them as objecttypes
	objecttypes = ["node", "way", "relation", "area"]
	if "conditions" in question:
		if "osm_element" in question["conditions"][0]:
			objecttypes = []
			# get what type of data is stored at question["conditions"][0]["osm_element"]
			if isinstance(question["conditions"][0]["osm_element"], str):
				objecttypes.append(OpenStopTypeToTaginfoType(question["conditions"][0]["osm_element"]))
			elif isinstance(question["conditions"][0]["osm_element"], list):
				for t in question["conditions"][0]["osm_element"]:
					objecttypes.append(OpenStopTypeToTaginfoType(t))

	for answer in question["answer"]["input"]:
		if "osm_tags" not in answer:
			continue
		for key, value in answer["osm_tags"].items():
			AddToQuestionsForTags(key, value, str(question["question"]["text"]), objecttypes)

for combikey, data in questions_for_tags.items():
	key = combikey.split("=")[0]
	value = combikey.split("=")[1]
	AddToTags(key, value, data["elements"], getQuestionDescription(data["questions"]))


TAGINFO["tags"] = TAGS

# Delete the files we just downloaded
os.remove(os.path.join(json_dir, "map_feature_collection.json"))
os.remove(os.path.join(json_dir, "question_catalog.json"))

# BEFORE we write the taginfo.json file, we generate the md5 of the string representation of the TAGINFO dictionary
# and add it to the dictionary
new_md5 = hashlib.md5(json.dumps(TAGINFO, ensure_ascii=False).encode("utf8")).hexdigest()

if new_md5 == previous_md5:
	print("No changes detected, exiting")
	exit()
else:
	print("Changes detected, writing taginfo.json")
	TAGINFO["project"]["catalog-md5"] = new_md5
	TAGINFO["data_updated"] = datetime.strftime(datetime.now(), '%Y%m%dT%H%M%SZ')


# write the taginfo.json file
with open(os.path.join(json_dir, "taginfo.json"), "w", encoding="utf8") as f:
	f.write(json.dumps(TAGINFO, indent=4, ensure_ascii=False))










