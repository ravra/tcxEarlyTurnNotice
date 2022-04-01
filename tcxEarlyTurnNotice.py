# Script to modify a Garmin tcx file to provide some advance notification before a turn.
# Ridewithgps files provide a turn notification (via a CoursePoint/CP) right at the turn coordinates
# which makes it too late to be very useful. This script adds an additional notification/CP
# by looking back some number (goBack) Trackpoints for an earlier set of coordinates and using
# those coordinates for the new CP.

# Usage:
# python3 tcxEarlyTurnNotice.py myRoute.tcx

# Notes
# This has only be tested on tcx files from ridewithgps
# I've noticed that CoursePoints that are too close together (e.g. two quick turns) will not
# be displayed by my Garmin.
# Trackpoints are not all evenly spaced so the early notification will vary. Perhaps in a future
# version I'll use the DistanceMeters element instead of the goBack method.
# 
# ravra - Mar 29, 2022

from xml.dom import minidom
import sys, os

# Get tcx file
if len(sys.argv) == 2:
    filePath = sys.argv[1]
    filePathSplit = os.path.splitext(filePath)
    filePathNew = filePathSplit[0] + "New.tcx"
    print("Note: Output file is: ", filePathNew)
else:
    print("Error: No file provided as argument")
    sys.exit(1)

global doc, indent
doc = minidom.parse(filePath)

course = doc.getElementsByTagName("Course")[0] # Only one Course within the tcx files created by ridewith gps
indent = course.childNodes[0].data # Grab the indentation whitespace for formatting the new CoursePoint

# goBack is the number of Trackpoints to go back (within tlist) after locating the Trackpoint
# associated with a particular CoursePoint. After going back a certain number of Trackpoints 
# in tlist, the lat, lon, and time from that Trackpoint is collected for the new Coursepoint.

goBack = 2

# Get the text of an element
def getText(eleName, tag):
    return eleName.getElementsByTagName(tag)[0].childNodes[0].data

# The lat and lon text are child elements of the parent Position. Given a Position element, this
# functino returns the lat and lon text in a list
def getLatLonText(eleName):
    position = eleName.getElementsByTagName("Position")[0]
    lat = position.childNodes[1].childNodes[0].data
    lon = position.childNodes[3].childNodes[0].data
    #print("lat & lon: ", lat, " ", lon)
    return [lat, lon]

# Add a new child element to a parent element with given text and indentation
def addElement(eleName, newEleName, newEleText, eIndent):
    global doc
    nltext = doc.createTextNode(eIndent)  # Create a newline preparing for the next element
    child = eleName.appendChild(nltext)    # Add the newline to parent element
    newEle = doc.createElement(newEleName)    # Create the new element within the document
    text = doc.createTextNode(newEleText)  # Create a text node within the doc for the new element
    newEle.appendChild(text)                  # Add the text node to the new element
    eleName.appendChild(newEle)               # Append the new element to its parent element
    return newEle

# Create a new CoursePoint
def makeCoursePoint(name, point, notes, lat, lon, tim):
    global doc, indent
    cp = doc.createElement("CoursePoint")
    cptext = doc.createTextNode("")  # Prepare for childnode indent
    tchild = cp.appendChild(cptext)
    # Add elements
    # set element indent
    elementIndent = indent + "  "
    addElement(cp, "Name", name, elementIndent)
    addElement(cp, "Time", tim, elementIndent)
    positionNode = addElement(cp, "Position", "", elementIndent)
    latlonIndent = elementIndent + "  "
    addElement(positionNode, "LatitudeDegrees", lat, latlonIndent)
    addElement(positionNode, "LongitudeDegrees", lon, latlonIndent)

    cptext = doc.createTextNode(elementIndent)  # Prepare for childnode indent
    tchild = positionNode.appendChild(cptext)

    addElement(cp, "PointType", point, elementIndent)
    addElement(cp, "Notes", notes, elementIndent)
    cptext = doc.createTextNode(indent)  # Prepare for childnode indent
    tchild = cp.appendChild(cptext)
    # print("cp.toxml: \n", cp.toxml())
    return(cp)


##########################################################################
# Parse Trackpoints to store lat, lon, and time in the list 'tlist'

Trackpoints = doc.getElementsByTagName("Trackpoint")
#print("TrackPoints", TrackPoints)

i = 0
tlist = []

for tp in Trackpoints:
    lat = tp.getElementsByTagName("LatitudeDegrees")
    #print("lat is: ", lat[0].childNodes[0].data)
    lon = tp.getElementsByTagName("LongitudeDegrees")
    #print("lon is: ", lon[0].childNodes[0].data)
    tim = tp.getElementsByTagName("Time")
    #print("tim is: ", tim[0].childNodes[0].data)
    tlist.append([i, lat[0].childNodes[0].data, lon[0].childNodes[0].data, tim[0].childNodes[0].data])
    i = i + 1

#print("tlist is: ", tlist)

##########################################################################
# Parse CoursePoints and make copies eariler in the track

CoursePoints = doc.getElementsByTagName("CoursePoint")
#print("CoursePoints", CoursePoints)

for cp in CoursePoints:
    latlon = getLatLonText(cp) # Grab the lat & lon to search within tlist (i.e. Trackpoints)
    # print("latlon", latlon)
    # Grab other elements within the CP to copy into the new CP
    nameText = getText(cp, "Name")
    pointTypeText = getText(cp, "PointType")
    notesText = getText(cp, "Notes")
    timeText = getText(cp, "Time")

    for i in range(len(tlist)):
        if tlist[i][1] == latlon[0]:       # Check lat
            if tlist[i][2] == latlon[1]:   # Check lon
                if tlist[i][3] == timeText:   # Check time
                    #print("Match!")
                    if (i - goBack) >= 0:
                        goBackLat = tlist[i-goBack][1]
                        goBackLon = tlist[i-goBack][2]
                        goBackTim = tlist[i-goBack][3]
                        # print("GoBack lat, lon, tim: ", goBackLat, goBackLon, goBackTim)
                        ################################################################
                        # Create new CP using the current CP name, notes, point
                        # but with the goBack Trackpoint lat, lon, and time
                        newCp = makeCoursePoint(nameText, pointTypeText, notesText, goBackLat, goBackLon, goBackTim)
                        # Add new CP to Course element before the current CP
                        course.insertBefore(newCp, cp)
                        nltext = doc.createTextNode(indent)   # Add newline for end-tag
                        course.insertBefore(nltext, cp)

                    
# Write result xml to the output file
f = open(filePathNew, "w")
f.write(doc.toxml())
f.close()
#print(doc.toxml())

sys.exit(0)
