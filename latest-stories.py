#!/usr/bin/env python

# Print out the stories that were compled during the last iteration.

import getopt, os, sys
import httplib
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

if __name__=="__main__":
    historyWeeks = 0
    baseURL = "https://www.pivotaltracker.com/services/v5/projects/"

    if (not os.environ.has_key('TRACKER_TOKEN')):
        print >>sys.stderr, "[ERROR] Environment variable not defined: TRACKER_TOKEN"
        sys.exit(-1) ;
    else:
        trackerHeaders = {"Content-Type": "application/json",
                          "X-TrackerToken": os.environ['TRACKER_TOKEN']}

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "vw:", ["weeks="])
    except getopt.GetoptError:
        (err, why, tb) = sys.exc_info()
        print >>sys.stderr, "[ERROR]: %s" % why
        sys.exit(1)

    for opt, arg in opts:
        if opt == "-v":
            verbose = True
        elif opt in ("-w", "--weeks"):
            historyWeeks = int(arg)

    for projectNum in args:
        trackerAPI = httplib.HTTPSConnection("www.pivotaltracker.com")
        trackerAPI.request("GET", "/services/v5/projects/%s" % projectNum, None, trackerHeaders)
        response = trackerAPI.getresponse()
        if (200 == response.status):
            project = json.loads(response.read())
        else:
            print >>sys.stderr, "[ERROR] http error response: %s, %s" % (response.status, response.reason)
            sys.exit(2) ;

        lastIter = project["current_iteration_number"] - historyWeeks

        trackerAPI.request("GET", "/services/v5/projects/%s/iterations/%s" % (projectNum, lastIter),
                           None, trackerHeaders)
        response = trackerAPI.getresponse()
        if (200 == response.status):
            iteration = json.loads(response.read())
        else:
            print >>sys.stderr, "[ERROR] http error response: %s, %s" % (response.status, response.reason)
            sys.exit(3)

        print "# %s\n" % project["name"]
        for i in iteration["stories"]:
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

        print "\n\n"

        trackerAPI.close()
