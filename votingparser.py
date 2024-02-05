import pandas as pd
import time
import os, sys
import json
import glob
import re
import datetime

class participant_groupLevel:
    def __init__(self, group):
        self.group = group
        self.numYeas = 0
        self.numNays = 0
        self.numInitates = 0
        self.wroteQuestions = 0
        self.numVotesForQuestions = 0
        self.speakTime = 0
        self.speakCount = 0

class participant:
    def __init__(self, uid, name, role):
        self.uid = uid
        self.name = name
        self.role = role
        self.groups = {}

class group:
    def __init__(self, group):
        self.name = group
        self.startTime = 0
        self.endTime = 0
        self.speakingTime = 0

def grab_json_files(override_path=""):
    
    jsonnames = []

    if override_path != "":
        path = override_path
    else:
        path = os.getcwd()

    print("Searching " + path + " for json files\n")
    json_files = glob.glob(os.path.join(path, "*.json"))

    # grab the filenames we find. There is probably a more efficent way to do this but here we are
    for filepath in json_files:
        n = re.search(r".+\\([^\.]+)", filepath)
        jsonnames.append(n.group(1))

    #check that there are in fact some files to parse
    if len(json_files) == 0:
        print("No json files found in the current directory. Exiting.")
        time.sleep(2.5)
        sys.exit()

    return json_files, jsonnames

def grab_data_from_file(json_files):

    participants = {}
    group_list = {}

    for file in json_files:
        with open(file, 'r', encoding='utf-8', errors="replace") as json_file:
            parsed_json = json.load(json_file)

            for room in parsed_json:
                try:
                    roomName = room["roomData"]["name"]
                except KeyError:
                    continue
                
                if "userData" not in room.keys():
                    print("Skipped room " +  roomName + " because it has no users")
                    continue

                for user in room["userData"]:

                    if user["id"] not in participants.keys():
                        participants[user["id"]] = participant(user["id"], user["screenName"], user["role"])
                    
                    person = participants[user["id"]]
                    person.groups[roomName] = participant_groupLevel(roomName)

                    for item in user["advanceAgenda"]:
                        if item["answer"] == 1:
                            person.groups[roomName].numNays += 1
                        elif item["answer"] == 0:
                            person.groups[roomName].numYeas += 1

                    for block in user["speakBlocks"]:
                        time = block["finishTime"] - block["speakTime"]
                        if time:
                            person.groups[roomName].speakCount += 1
                            person.groups[roomName].speakTime += time
                            if roomName not in group_list.keys():
                                group_list[roomName] = group(roomName)
                                group_list[roomName].speakingTime += time
                            else:
                                group_list[roomName].speakingTime += time
                
                for item in room["transcriptData"]:
                    if item["type"] ==  "connect" and group_list[roomName].startTime == 0:
                        group_list[roomName].startTime = item["t"]
                    
                    if item["type"] == "submitQuestion":
                        person = item["userId"]
                        participants[person].groups[roomName].wroteQuestions += 1

                    if item["type"] == "submitQuestionRanks":
                        person = item["userId"]
                        participants[person].groups[roomName].numVotesForQuestions += 1

                    if item["type"] == "moderator":
                        if item["text"] == "Deliberation ends":
                            group_list[roomName].endTime = item["t"]

                        if item["text"] == "Introductions":
                            group_list[roomName].startTime = item["t"]
                            
                                  
                for item in room["pollData"].values():
                    if item["type"] == "advanceAgenda":
                        initator = item["data"]["from"]

                        participants[initator].groups[roomName].numInitates += 1

    return participants, group_list

def convert_to_minsecs(length):
    d = datetime.timedelta(milliseconds=length)
    return str(d)[:7]

def generate_output(participants, groups):
    df = pd.DataFrame(columns="Uid, _Name, Group, YeasMoveOn, NaysMoveOn, MoveOnInitiations, QuestionsWritten, VotesForQuestions, SpeakCount, SpeakTime, groupDelibTime, groupSpeakingTime".split(", "))

    for person in participants.values():
        if person.role in ["observer", "admin", "removed"]:
            continue
        for group in person.groups.values():
            df.loc[len(df.index)] = [person.uid, person.name, group.group, group.numYeas, group.numNays, group.numInitates, 
                                     group.wroteQuestions, group.numVotesForQuestions, group.speakCount, 
                                     str(convert_to_minsecs(group.speakTime)), 
                                     str(convert_to_minsecs(groups[group.group].endTime - groups[group.group].startTime)), 
                                     str(convert_to_minsecs(groups[group.group].speakingTime))]
            
    folder_name=os.path.basename(os.path.normpath(os.getcwd()))
    
    df.to_csv("metaverse_" + folder_name + "_long.csv", index=True, encoding='utf-8-sig')
    df = df.sort_values(by='Group')

    wdf = pd.pivot(df, index='Uid', columns='Group')

    wdf.columns = wdf.columns.swaplevel(0, 1)  # Swap the levels of multiindex columns
    wdf = wdf.sort_index(axis=1, level=0)

    wdf.to_csv("metaverse_" + folder_name + "_wide.csv", index=True, encoding='utf-8-sig')

def main():
    json_files, names = grab_json_files()

    participants, groups = grab_data_from_file(json_files)

    generate_output(participants, groups)

    print("Data saved. Exiting...")
    time.sleep(1.5)

if __name__ == "__main__":
    main()



# def main():
#     json_files, names = grab_json_files()

#     print(names)
#     print(json_files)

#     # parsed_jsons, roomnames, names = parse_jsons(json_files, names)

#     # for i in range(len(parsed_jsons)):
#     #     speak_instances = get_speak_instances_from_json(parsed_jsons[i], ['Record'])
#     #     filename = generate_output(speak_instances, roomnames[i], names[i])

#     # print("\nData saved to " +  filename + ". Exiting...")
#     # time.sleep(1.5)



# ########################################
# # Execution statement
# ########################################
# if __name__ == "__main__":
#     main()