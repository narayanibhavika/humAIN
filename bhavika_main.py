from KEY import lib
import cv2
import numpy as np
import math
import pytesseract
from PIL import Image

temp_folder = 'C:\\Users\\hp\\Desktop\\bhavika\\'

picture = cv2.imread("pic.jpg")
cv2.imshow('pic', picture)


hsv = cv2.cvtColor(picture, cv2.COLOR_BGR2HSV)
hue, saturation, value = cv2.split(hsv)
#cv2.imshow('gray', value)

core = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4))
topHat = cv2.morphologyEx(value, cv2.MORPH_TOPHAT, core)
#cv2.imshow('topHat', topHat)
cv2.imwrite(temp_folder + 'topHat.jpg', topHat)

blackHat = cv2.morphologyEx(value, cv2.MORPH_BLACKHAT, core)
cv2.imwrite(temp_folder + 'blackHat.jpg', blackHat)
#cv2.imshow('blackHat', blackHat)

add = cv2.add(value, topHat)
subtract = cv2.subtract(add, blackHat)
#cv2.imshow('subtract', subtract)
cv2.imwrite(temp_folder + 'subtract.jpg', subtract)

blur = cv2.GaussianBlur(subtract, (5, 5), 0)
#cv2.imshow('blur', blur)
cv2.imwrite(temp_folder + 'blur.jpg', blur)


thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 39, 21)
#cv2.imshow('thresh', thresh)
cv2.imwrite(temp_folder + 'thresh.jpg', thresh)
cv2MajorVersion = cv2.__version__.split(".")[0]


if int(cv2MajorVersion) >= 4:
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
else:
    imageContours, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
height, width = thresh.shape
imageContours = np.zeros((height, width, 3), dtype=np.uint8)
characters = []
countOfcharacters = 0


for i in range(0, len(contours)):

    # draw contours based on actual found contours of thresh image
    cv2.drawContours(imageContours, contours, i, (255, 255, 255))

    # retrieve a possible char by the result ifChar class give us
    character = lib.ifChar(contours[i])

    # by computing some values (area, width, height, aspect ratio) characters list is being populated
    if lib.checkIfChar(character) is True:
        countOfcharacters = countOfcharacters + 1
        characters.append(character)
imageContours = np.zeros((height, width, 3), np.uint8)

ctrs = []

for char in characters:
    ctrs.append(char.contour)
# using values from ctrs to draw new contours
cv2.drawContours(imageContours, ctrs, -1, (0, 0, 255))
#cv2.imshow("contourscharacters", imageContours)
cv2.imwrite(temp_folder + ' contourscharacters.jpg', imageContours)

Plates_list = []
listOfListsOfMatchingChars = []

for possibleC in characters:

    # the purpose of this function is, given a possible char and a big list of possible chars,
    # find all chars in the big list that are a match for the single possible char, and return those matching chars as a list
    def matchingChars(possibleC, characters):
        ListMatchChar = []

        # if the char we attempting to find matches for is the exact same char as the char in the big list we are currently checking
        # then we should not include it in the list of matches b/c that would end up double including the current char
        # so do not add to list of matches and jump back to top of for loop
        for possibleMatchingChar in characters:
            if possibleMatchingChar == possibleC:
                continue

            # compute stuff to see if chars are a match
            distanceBetweenChars = lib.distanceBetweenChars(possibleC, possibleMatchingChar)

            angleBetweenChars = lib.angleBetweenChars(possibleC, possibleMatchingChar)

            Area = float(abs(possibleMatchingChar.boundingRectArea - possibleC.boundingRectArea)) / float(
                possibleC.boundingRectArea)

            Width = float(abs(possibleMatchingChar.boundingRectWidth - possibleC.boundingRectWidth)) / float(
                possibleC.boundingRectWidth)

            height = float(abs(possibleMatchingChar.boundingRectHeight - possibleC.boundingRectHeight)) / float(
                possibleC.boundingRectHeight)

            # check if chars match
            if distanceBetweenChars < (possibleC.diagonalSize * 5.6) and \
                    angleBetweenChars < 13.0 and \
                    Area < 0.6 and \
                    Width < 0.7 and \
                    height < 0.3:
                ListMatchChar.append(possibleMatchingChar)

        return ListMatchChar


    # here we are re-arranging the one big list of chars into a list of lists of matching chars
    # the chars that are not found to be in a group of matches do not need to be considered further
    ListMatchChar = matchingChars(possibleC, characters)

    ListMatchChar.append(possibleC)

    # if current possible list of matching chars is not long enough to constitute a possible Plate
    # jump back to the top of the for loop and try again with next char
    if len(ListMatchChar) < 3:
        continue

    # here the current list passed test as a "group" or "cluster" of matching chars
    listOfListsOfMatchingChars.append(ListMatchChar)

    # remove the current list of matching chars from the big list so we don't use those same chars twice,
    # make sure to make a new big list for this since we don't want to change the original big list
    listOfcharactersWithCurrentMatchesRemoved = list(set(characters) - set(ListMatchChar))

    recursiveListOfListsOfMatchingChars = []

    for recursiveListMatchChar in recursiveListOfListsOfMatchingChars:
        listOfListsOfMatchingChars.append(recursiveListMatchChar)

    break


imageContours = np.zeros((height, width, 3), np.uint8)

for ListMatchChar in listOfListsOfMatchingChars:
    contoursColor = (255, 0, 0)

    contours = []

    for matchingChar in ListMatchChar:
        contours.append(matchingChar.contour)

    cv2.drawContours(imageContours, contours, -1, contoursColor)

#cv2.imshow("completeCountors", imageContours)
cv2.imwrite(temp_folder + 'completeCountors.jpg', imageContours)


for ListMatchChar in listOfListsOfMatchingChars:
    possiblePlate = lib.PossiblePlate()

    # sort chars from left to right based on x position
    ListMatchChar.sort(key=lambda matchingChar: matchingChar.centerX)

    # calculate the center point of the Plate
    PlateCenterX = (ListMatchChar[0].centerX + ListMatchChar[len(ListMatchChar) - 1].centerX) / 2.0
    PlateCenterY = (ListMatchChar[0].centerY + ListMatchChar[len(ListMatchChar) - 1].centerY) / 2.0

    PlateCenter = PlateCenterX, PlateCenterY

    # calculate Plate width and height
    PlateWidth = int((ListMatchChar[len(ListMatchChar) - 1].boundingRectX + ListMatchChar[
        len(ListMatchChar) - 1].boundingRectWidth - ListMatchChar[0].boundingRectX) * 1.2)

    totalOfCharHeights = 0

    for matchingChar in ListMatchChar:
        totalOfCharHeights = totalOfCharHeights + matchingChar.boundingRectHeight

    averageCharHeight = totalOfCharHeights / len(ListMatchChar)

    PlateHeight = int(averageCharHeight * 1.6)

    # calculate correction angle of Plate region
    opposite = ListMatchChar[len(ListMatchChar) - 1].centerY - ListMatchChar[0].centerY

    hypotenuse = lib.distanceBetweenChars(ListMatchChar[0],
                                                ListMatchChar[len(ListMatchChar) - 1])
    correctionAngleInRad = math.asin(opposite / hypotenuse)
    correctionAngleInDeg = correctionAngleInRad * (180.0 / math.pi)

    # pack Plate region center point, width and height, and correction angle into rotated rect member variable of Plate
    possiblePlate.rrLocationOfPlateInScene = (tuple(PlateCenter), (PlateWidth, PlateHeight), correctionAngleInDeg)

    # get the rotation matrix for our calculated correction angle
    rotationMatrix = cv2.getRotationMatrix2D(tuple(PlateCenter), correctionAngleInDeg, 1.0)

    height, width, numChannels = picture.shape

    # rotate the entire image
    pictureRotated = cv2.warpAffine(picture, rotationMatrix, (width, height))

    # crop the image/Plate indentify
    pictureCropped = cv2.getRectSubPix(pictureRotated, (PlateWidth, PlateHeight), tuple(PlateCenter))

    # copy the cropped Plate image into the applicable member variable of the possible Plate
    possiblePlate.Plate = pictureCropped

    # populate Plates_list with the indentify Plate
    if possiblePlate.Plate is not None:
        Plates_list.append(possiblePlate)

    # draw a ROI on the original image
    for i in range(0, len(Plates_list)):
        # finds the four vertices of a rotated rect - it is useful to draw the rectangle.
        p2fRectPoints = cv2.boxPoints(Plates_list[i].rrLocationOfPlateInScene)
        rectColour = (0,0 , 255)

        cv2.line(imageContours, tuple(p2fRectPoints[0]), tuple(p2fRectPoints[1]), rectColour, 2)
        cv2.line(imageContours, tuple(p2fRectPoints[1]), tuple(p2fRectPoints[2]), rectColour, 2)
        cv2.line(imageContours, tuple(p2fRectPoints[2]), tuple(p2fRectPoints[3]), rectColour, 2)
        cv2.line(imageContours, tuple(p2fRectPoints[3]), tuple(p2fRectPoints[0]), rectColour, 2)

        cv2.line(picture, tuple(p2fRectPoints[0]), tuple(p2fRectPoints[1]), rectColour, 2)
        cv2.line(picture, tuple(p2fRectPoints[1]), tuple(p2fRectPoints[2]), rectColour, 2)
        cv2.line(picture, tuple(p2fRectPoints[2]), tuple(p2fRectPoints[3]), rectColour, 2)
        cv2.line(picture, tuple(p2fRectPoints[3]), tuple(p2fRectPoints[0]), rectColour, 2)

        cv2.imshow("indentify", imageContours)
        cv2.imwrite(temp_folder + 'indentify.jpg', imageContours)

        #cv2.imshow("pic", picture)
        cv2.imwrite(temp_folder + 'indentifyOriginal.jpg', picture)

        cv2.imshow("Plate1", Plates_list[i].Plate)
        cv2.imwrite(temp_folder + 'plate.jpg', Plates_list[i].Plate)

picture = Image.open('plate.jpg')
x = pytesseract.image_to_string(picture)
char=[]
for i in range (len(x)):
    if(48<=ord(x[i])<=57 or 65<= ord(x[i])<=90):
        N=x[i]
        char.append(N)
print("".join(char)) 



cv2.waitKey(0) 

cv2.destroyAllWindows()  