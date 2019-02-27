#!/usr/bin/env python

# Print out the stories that were completed by tracking a specific label.

import getopt, os, sys
import httplib, urllib
import json
from pprint import pprint, pformat

def isChore(story):
    if ("chore" == story["story_type"]):
        return True ;
    else:
        return False ;

def isFeature(story):
    if ("feature" == story["story_type"]):
        return True ;
    else:
        return False ;

def storyState(story):
    return(story["current_state"]) ;

class trackerRequest:
    """Encapsulate our interactions with Pivotal Tracker's API."""

    def __init__(self, token, projectNum):
        self.__token = token ;
        self.__projectNum = projectNum ;
        self.__headers = {"Content-Type": "application/json",
                          "X-TrackerToken": self.__token}
        self.__httpPath = "/services/v5/projects/%s" % self.__projectNum

        self.__trackerAPI = httplib.HTTPSConnection("www.pivotaltracker.com")
        self.__trackerAPI.request("GET", self.__httpPath, None, self.__headers)
        response = self.__trackerAPI.getresponse()
        if (200 == response.status):
            self.project = json.loads(response.read())
        else:
            raise("[ERROR] http error response: %s, %s" % (response.status, response.reason)) ;

    def stories(self, weeksInPast=False, searchLabel=False):

        """Query Tracker to get a set of stories. specify either:
           - a number of weeks as a weeksInPast to get all stories completed that week
           - a label as searchLabel to get all stories associated with that label
        """
        if (weeksInPast):
            lastIter = self.project["current_iteration_number"] - weeksInPast
            self.__trackerAPI.request("GET", "%s/iterations/%s" % (self.__httpPath, lastIter),
                                      None, self.__headers)
        elif (searchLabel):
            searchPath = "search?query=%s" % urllib.quote("label:\"%s\" includedone:true" % searchLabel)
            self.__trackerAPI.request("GET", "%s/%s" % (self.__httpPath, searchPath),
                                      None, self.__headers)

        response = self.__trackerAPI.getresponse()
        if (200 == response.status):
            output = json.loads(response.read())
        else:
            raise("[ERROR] http error response: %s, %s" % (response.status, response.reason))

        if (weeksInPast):
            return(output["stories"]) ;
        # In Tracker's API, the results contain more than just stories.
        if (searchLabel):
            return(output["stories"]["stories"]) ;

    def close(self):
        self.__trackerAPI.close()

if __name__=="__main__":
    weeks = None
    label = None
    verbose = False

    if (not os.environ.has_key('TRACKER_API_TOKEN')):
        print >>sys.stderr, "[ERROR] Environment variable not defined: TRACKER_API_TOKEN"
        sys.exit(-1) ;

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "vw:l:", ["weeks=","label="])
    except getopt.GetoptError:
        (err, why, tb) = sys.exc_info()
        print >>sys.stderr, "[ERROR]: %s" % why
        sys.exit(1)

    for opt, arg in opts:
        if opt == "-v":
            verbose = True
        elif opt in ("-w", "--weeks"):
            weeks = int(arg)
        elif opt in ("-l", "--label"):
            label = arg

    for projectNum in args:
        myRequest = trackerRequest(os.environ['TRACKER_API_TOKEN'], projectNum)

        if (weeks):
            stories = myRequest.stories(weeksInPast=weeks)
        elif (label):
            stories = myRequest.stories(searchLabel=label)

        print "# %s\n" % myRequest.project["name"]
        if (0 == len(stories)):
            print >>sys.stderr, "  No results."
        else:
            for i in stories:
                if (isChore(i)):
                    pass ;
                elif ("unscheduled" == storyState(i)):
                          pass ; 
                elif (isFeature(i) and ("accepted" == storyState(i) or "delivered" == storyState(i))):
                    if (0 != len(i["labels"])):
                        try:
                            print "- %s (_%s_) [[#%s](%s)]" % (i["name"].encode("ascii", "ignore"),
                                                               ",".join([g["name"].encode("ascii", "ignore")
                                                                         for g in i["labels"]]),
                                                               i["id"], i["url"])
                        except:
                            (err, why, tb) = sys.exc_info() ;
                            print >>sys.stderr, "Error: %s, %s\n%s" % (err, why, i["url"])
                    else:
                        print "- %s [[#%s](%s)]" % (i["name"].encode("ascii", "ignore"), i["id"], i["url"])
                else:
                    if (0 != len(i["labels"])):
                        print "- [%s] %s (_%s_) [[#%s](%s)]" % (i["story_type"].upper(),
                                                                i["name"].encode("ascii", "ignore"),
                                                                ",".join([g["name"] for g in i["labels"]]),
                                                                i["id"], i["url"])
                    else:
                        print "- [%s] %s [[#%s](%s)]" % (i["story_type"].upper(),
                                                         i["name"].encode("ascii", "ignore"),
                                                         i["id"], i["url"])

        print "\n"

        myRequest.close()
