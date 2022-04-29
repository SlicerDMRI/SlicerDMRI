"""

pip_install("pandas")


"""

import csv
import json

dictionaryPath = "/opt/data/SlicerDMRI/Test-Dec01-N30/abcd30Subjects_data_forSteve-dictionary.csv"
subjectsPath = "/opt/data/SlicerDMRI/Test-Dec01-N30/abcd30Subjects_data_forSteve-data.csv"

dictionaryJSONPath = "/opt/data/SlicerDMRI/Test-Dec01-N30/abcd30Subjects_dictionary.json"
subjectsJSONPath = "/opt/data/SlicerDMRI/Test-Dec01-N30/abcd30Subjects_data.json"

def striphex(s):
    ret = ''
    for c in s:
        if ord(c) < 128:
            ret += c
    return(ret)

def beforehex(s):
    ret = ''
    for c in s:
        if ord(c) < 128 and c != "/":
            ret += c
        else:
            return(ret.strip())


key = ""
value = ""
dictionary = {}
with open(dictionaryPath) as csvfile:
    csvreader = csv.reader(csvfile)
    keys = csvreader.__next__()
    values = csvreader.__next__()
    for key, value in zip(keys,values):
        key = striphex(key)
        value = beforehex(value)
        dictionary[key] = value

subjects = []
with open(subjectsPath) as csvfile:
    csvreader = csv.reader(csvfile)
    fields = csvreader.__next__()
    for values in csvreader:
        subject = {}
        for field, value in zip(fields,values):
            subject[field] = value
        subjects.append(subject)


for key in subjects[0].keys():
    if key in dictionary:
        print(dictionary[key])
    print(key, subjects[0][key])


with open(dictionaryJSONPath, "w") as jsonfile:
    jsonfile.write(json.dumps(dictionary))

with open(subjectsJSONPath, "w") as jsonfile:
    jsonfile.write(json.dumps(subjects))
