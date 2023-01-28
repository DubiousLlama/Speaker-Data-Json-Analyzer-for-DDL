import pandas as pd
import glob
import os
import time
import datetime
import sys
import re

# This datatype defines a single speak instance. By extracting all the speak instances in our data into a giant list of these,
# it makes it easier to write new functions to analyze the data.
class speakInstance:
    def __init__(self, group, speaker, uid, speakBlock):
        speakBlock = dict(speakBlock)
        self.uid = uid
        self.start = speakBlock['speakTime']
        self.end = speakBlock['finishTime']
        self.requestTime = speakBlock['requestTime']
        self.length = self.end-self.start
        self.speaker = speaker
        self.group = group


# Takes in a list of json files, performs the parsing and data organization, and writes the output to a xlsx file.
# Add custom functions for new types of data orginization in the indicated block below and save their output to the
# excel_sheets dictionary along with the name of the sheet you want the data to be written to.
def generate_output(speak_instances, roomnames, jsonname):

    #######################################
    # Place functions for generating output here.
    # Be sure to add the output to excel_sheets in the format key=sheetname, value=dataframe

    excel_sheets = {}

    excel_sheets['Speak Instances By Group'] = organize_by_group(speak_instances, roomnames)
    excel_sheets['Speaker Totals'] = total_speaker_times(speak_instances, roomnames)

    ########################################

    # Write the output to a xlsx file
    filename = check_for_existing_file(jsonname)
    writer = pd.ExcelWriter(filename)

    for sheetname, data in excel_sheets.items():
        data.to_excel(writer, sheet_name=sheetname)

    # close the Pandas Excel writer and output the Excel file.
    writer.save()

    return filename

def main():
    json_files, names = grab_json_files()

    parsed_jsons, roomnames = parse_jsons(json_files)

    for i in range(len(json_files)):
        speak_instances = get_speak_instances_from_json(parsed_jsons[i])
        filename = generate_output(speak_instances, roomnames[i], names[i])

    print("\nData saved to " +  filename + ". Exiting...")
    time.sleep(1.5)

########################################
# Data organization functions
########################################

# Takes in a  list of speak instances and roomnames and returns a dataframe with the following columns corresponding to each room:
# DisplayName_[roomname], ParticipantID_[roomname], SpeakTime_[roomname]. 
# Use the list comprehensions below as a model for how to organize the data in different ways. Note that for room in roomnames would need
# to be a different loop to organize the data by something other than room.
def organize_by_group(all_speak_instances, roomnames):
    out = pd.DataFrame()

    # sort the list of speak instances by start time. 
    all_speak_instances.sort(key=lambda x: x.start)

    # iterate over our many rooms, using list comprehensions to add the relevant data to our output dataframe
    for room in roomnames:
        # get the speak instances we care about create a dataframe to store this group's data in. We use this intermediate dataframe because
        # pandas is a bit annoying about adding new rows to a dataframe.
        speaksinroom = [x for x in all_speak_instances if x.group == room]
        newelems = pd.DataFrame(index=range(len(speaksinroom)))

        # debug code for ensuring proper ordering of speaks
        # speakstarts = [time.asctime(time.gmtime(x.start/1000.0)) for x in speaksinroom] 
        # newelems[room + "_startTime"] = speakstarts
        
        # create lists with the data we care about and add them to our intermediate dataframe
        newelems["DisplayName_" + room] = [x.speaker for x in speaksinroom]
        newelems["ParticipantID_" + room] = [x.uid for x in speaksinroom]
        newelems["SpeakTime_" + room] = [convert_to_minsecs(x.length) for x in speaksinroom] 
        
        # concatenate the intermediate dataframe to our output dataframe
        out = pd.concat([out, newelems], axis=1)
    
    return out

# Takes in a  list of speak instances and roomnames and returns a dataframe with the following columns corresponding to each room:
# DisplayName_[roomname], ParticipantID_[roomname], TotalSpeakTime_[roomname].
# Use the dictionary and loop below as a model for how to sum data in different ways.
def total_speaker_times(all_speak_instances, roomnames):
    out = pd.DataFrame()

    # iterate over our many rooms
    for room in roomnames:
        speaksinroom = [x for x in all_speak_instances if x.group == room]

        #don't bother with rooms that have no speak instances
        if len(speaksinroom) == 0:
            continue

        # this will hold a tuple with the speaker's name and uid as the key, and a float for their total speak time as the value
        totalspeaklengths = {}
        numspeaktimes = {}
        
        # Get the total time each speaker spoke in the room
        for speak in speaksinroom:
            if (speak.uid, speak.speaker) in totalspeaklengths.keys():
                totalspeaklengths[(speak.uid, speak.speaker)] += speak.length
            else:
                totalspeaklengths[(speak.uid, speak.speaker)] = speak.length

        for speak in speaksinroom:
            if (speak.uid, speak.speaker) in numspeaktimes.keys():
                numspeaktimes[(speak.uid, speak.speaker)] += 1
            else:
                numspeaktimes[(speak.uid, speak.speaker)] = 1

        newelems = pd.DataFrame(index=range(len(totalspeaklengths)))

        # append the info to our intermediate dataframe
        displayorder = totalspeaklengths.keys() # .keys() can't be trusted to return the same order every time, so we need to store it. Thanks python.
        newelems["DisplayName_" + room] = list(map(lambda x: x[1], displayorder))
        newelems["ParticipantID_" + room] = list(map(lambda x: x[0], displayorder))
        newelems["TotalSpeakTime_" + room] = [convert_to_minsecs(totalspeaklengths[x]) for x in displayorder]
        newelems["NumSpeaks_" + room] = [numspeaktimes[x] for x in displayorder]

        # concatenate the intermediate dataframe to our output dataframe
        out = pd.concat([out, newelems], axis=1)

    return out


########################################
# Helper functions
########################################

# Grab all json files in the same folder as the script. Optional override_path argument can be used to get files from a different
# folder.
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

# Takes in a list of json files paths and return a list of pandas dataframes containing the userdata from each json
# organized in rows by room and a list of all roomnames parsed from the json files.
def parse_jsons(json_files):
    parsed_jsons = []
    roomnames = []

    #loop through each file and parse the json data
    for file in json_files:
        with open(file, 'r', encoding='utf-8', errors="replace") as json_file:
            print("Parsing " + file + "...")
            df = pd.read_json(json_file)

            #this is a bit messy, but it makes the first row of our output dataframes the room the data corresponds to.
            df_roomdata = pd.json_normalize(df['roomData'])
            df_userdata = pd.json_normalize(df['userData'])
            df_userdata.insert(0,'room','')
            df_userdata['room'] = df_roomdata['name']
            parsed_jsons.append(df_userdata)

            #add the room names to our list of roomnames
            roomnames.append(list(df_roomdata['name'])[0:])
            

    return parsed_jsons, roomnames

# Takes in a pandas dataframe resulting from a single deliberation and turns it into a list of speak instances.
# The optional exclude argument can be used to exclude a list of users from the list of speak instances (such as admins, in 
# cases where they spoke in the deliberation).
def get_speak_instances_from_json(df, exclude_speakers=[]):
    speak_instances = []
    i = 0
    for room in df['room']:
        for col in df.columns[1:]:
            user = df[col][i]
            if (user != None) and (not user in exclude_speakers):
                user = dict(user)
                speakBlocks = list(user['speakBlocks'])
                if speakBlocks:
                    for block in speakBlocks:
                        speak_instances.append(speakInstance(room, user['screenName'], user['id'], block))
        i+=1
    return speak_instances

# For prettifying speak-length data in miliseconds to human readable minutes:seconds format 
def convert_to_minsecs(length):
    d = datetime.timedelta(milliseconds=length)
    return str(d)[2:7]

# Given a filename, checks for an existing output file, and returns the appropriate filename to use in the format output (n).xlsx.
def check_for_existing_file(filename):
    if os.path.isfile(filename + ".xlsx"):
        i = 1
        while True:
            if not os.path.isfile(filename + " (" + str(i) + ").xlsx"):
                return filename + " (" + str(i) + ").xlsx"
            i+=1
    else:
        return filename + ".xlsx"

########################################
# Execution statement
########################################
if __name__ == "__main__":
    main()