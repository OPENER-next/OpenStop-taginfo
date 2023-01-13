import os, sys, json
from datetime import datetime
import urllib.request

TAGINFO = {}

# Set up the basic parameters
TAGINFO["data_format"] = 1
TAGINFO["data_url"] = "https://raw.githubusercontent.com/OPENER-next/OpenStop-taginfo/main/taginfo.json"
TAGINFO["data_updated"] = datetime.strftime(datetime.now(), '%Y%m%dT%H%M%SZ')
TAGINFO["project"] = {
	"name": "OpenStop",
	"description": "App for collecting OpenStreetMap-compliant accessibility data in public transport",
	"project_url": "https://openstop.app/",
	"doc_url": "https://github.com/OPENER-next/OpenStop",
	"icon_url": "https://raw.githubusercontent.com/OPENER-next/OpenStop/master/web/favicon.png",
	"contact_name": "OPENER NEXT",
	"contact_email": "FIXME"
}
TAGINFO["tags"] = []

TAGS = []


def AddToTags(key, value, object_types, description):
	global TAGS
	t = {}
	t["key"] = key
	if value != None:
		t["value"] = value
	t["object_types"] = object_types
	t["description"] = description
	TAGS.append(t)




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
with open(os.path.join(json_dir, "question_catalog.json")) as f:
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
	for answer in question["answer"]["input"]:
		if "osm_tags" not in answer:
			continue
		for key, value in answer["osm_tags"].items():
			AddToTags(key, value, ["node", "way", "relation", "area"], "Added as possible answer to the question \"" + str(question["question"]["text"]) + "\".")


TAGINFO["tags"] = TAGS

# write the taginfo.json file
with open(os.path.join(json_dir, "taginfo.json"), "w") as f:
	json.dump(TAGINFO, f, indent=4)

# Delete the files we just downloaded
os.remove(os.path.join(json_dir, "map_feature_collection.json"))
os.remove(os.path.join(json_dir, "question_catalog.json"))








