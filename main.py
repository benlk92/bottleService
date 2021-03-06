from kivy.app import App
from kivy.properties import ObjectProperty, ListProperty, DictProperty, NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.listview import ListItemButton
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.button import Button
from functools import partial
from kivy.config import Config
from random import random, randint
import RPi.GPIO as GPIO

from time import time, sleep
import threading
import csv

Config.set("graphics", "width", "800")
Config.set("graphics", "height", "480")

# Push Test2


# Class to represent all ingredients in bottle service
class Ingredient(object):
    def __init__(self, name, brand = "", location = -1, ingType = "", manual = 0, inStock = 0, calibration = -1):
        self.name = name
        self.brand = brand
        self.location = location
        self.displayNorm = ""
        self.displaySmall = ""
        self.ingType = ingType
        self.inStock = inStock
        self.manual = manual
        self.spacer = ""
        self.newLine = ""
        self.calibration = calibration

        self.setDisplay()

    def setDisplay(self):
        if (self.brand == ""):
            self.spacer = ""
            self.newLine = ""
            self.displayNorm = self.name
            self.displaySmall = self.name
        else:
            self.spacer = " "
            self.newLine = "\n"
            self.displayNorm = self.brand + self.spacer + self.name
            self.displaySmall = self.brand + self.newLine + self.name

class Drink(object):
    def __init__(self, name, glassware = "", prepMethod = "", ingredients = {}):
        self.name = name
        self.glassware = glassware
        self.prepMethod = prepMethod
        self.ingredients = ingredients



class IngredientListButton(ListItemButton):
    font_size = 24
    
class SplashScreen(Screen):
    pass

class PairIngredients(Screen):
    pass

class MakeDrink(Screen):
    pass

class ManageDrinks(Screen):
    pass

class ManageIndDrinks(Screen):
    pass

class ManageIngredients(Screen):
    pass

class ManageBottleService(Screen):
    pass

class ManageRecipes(Screen):
    pass

class GeneralSettings(Screen):
    pass

class Shots(Screen):
    pass

class MyPopup(Popup):
    pass

class MessagePopup(Popup):
    pass

class ProgressPopup(Popup):
    pass

class OptionPopup(Popup):
    pass

class TripleOptionPopup(Popup):
    pass

class SpinnerPopup(Popup):
    pass

class CountPopup(Popup):
    pass

class NewIngPopup(Popup):
    pass

class CalibrationPrepPopup(Popup):
    pass

class Manager(ScreenManager):

    pairScreen = ObjectProperty(None)
    manageDrinkScreen = ObjectProperty(None)
    manageIngScreen = ObjectProperty(None)
    makeScreen = ObjectProperty(None)

    ingPopup = ObjectProperty(None)
    settingsPopup = ObjectProperty(None)

    curIngLocation = 0


class BottleService(BoxLayout):

    row0 = ObjectProperty(None)
    row1 = ObjectProperty(None)
    row2 = ObjectProperty(None)

    manager = ObjectProperty(None)
    drinkName = ObjectProperty(None)
    brand = ObjectProperty(None)
    ingName = ObjectProperty(None)
    typeField = ObjectProperty(None)
    glassField = ObjectProperty(None)
    prepField = ObjectProperty(None)


    ingListView = ObjectProperty(None)
    drinkListView = ObjectProperty(None)
    typeListView = ObjectProperty(None)
    glassListView = ObjectProperty(None)
    prepListView = ObjectProperty(None)
    avaDrinkListView = ObjectProperty(None)


    drinkTitle = ObjectProperty(None)
    shotTitle = ObjectProperty(None)
    ingSpinner = ObjectProperty(None)
    drinkName = ObjectProperty(None)
    prepSpinner = ObjectProperty(None)
    glassSpinner = ObjectProperty(None)
    ingPopup = ObjectProperty(None)

    ingTypeSpinner = ObjectProperty(None)

    inStockToggle = ObjectProperty(None)
    manualToggle = ObjectProperty(None)

    # manualIngSpinner = ObjectProperty(None)
    filterSpinner = ObjectProperty(None)

    ingBl = ObjectProperty(None)

    mainFilter = ObjectProperty(None)

    # manualButton = ObjectProperty(None)
    submitButton = ObjectProperty(None)

    manualStop = NumericProperty(0)

    drinkManager = []
    curDrinkManager = []

    ingredientList = {}
    drinkList = {}
    glassList = []
    prepList = []

    managing = 0

    currentButton = None

    ingCount = -1

    glassName = "Whatever"
    prepName = "I don't care"
    unpairedText = "-"
    unselectedText = "-"


    ounceInput = ObjectProperty(None)
    strengthInput = ObjectProperty(None)
    robotName = ObjectProperty(None)
    maxAmtInput = ObjectProperty(None)
    shotInput = ObjectProperty(None)
    displayToggle = ObjectProperty(None)

    ounceSetting = 0
    strengthSetting = 0

    justDisplay = 1

    rows = {0: {"Count": 5}, 1: {"Count": 4}, 2: {"Count": 5}}

    filterConstants = ["No Filter","In Stock", "Not in Stock", "Manual", "Automatic"]

    typeList = []
    ingList = []
    initialPairings = {}

    initialized = 0

    systemTime = 0

    bartenderChoosing = 0

    pourTime = 0
    startTime = 0
    endTime = 0

    isCancelled = False
    pairingMode = True



    def pairPopup(self, text):

        self.ingPopup.dismiss()

        if ((self.currentButton != None) & (self.justDisplay == 0)):

            if text != self.unpairedText:
                ing = self.ingredientList[text]
                if (self.currentButton.ing != None):
                    oldIng = self.currentButton.ing
                    oldIng.location = -1

                self.currentButton.ing = ing
                ing.location = self.currentButton.ind

                calPop = OptionPopup()
                calPop.title = "Prime the lines"
                calPop.labelText = ("Press and hold the Prime button\n until %s is dispensed" % text)
                calPop.okayButton.ing = ing
                calPop.okayButton.bind(on_press = partial(self.pourManuallyStart))
                calPop.okayButton.bind(on_release = partial(self.pourManuallyStop))
                calPop.okayButton.text = "Prime"
                calPop.cancelButton.text = "Continue"
                calPop.cancelButton.bind(on_press = partial(self.calibrateConfirm, calPop, ing))
                calPop.open()

            else:
                if (self.currentButton.ing != None):
                    oldIng = self.currentButton.ing
                    oldIng.location = -1
                self.currentButton.ing = Ingredient(self.unpairedText)

        self.filterDrinks()

    def calibrateConfirm(self, calPop, ing, okayButton):
    	calPop.dismiss()

        calPop = TripleOptionPopup()
        calPop.title = "Calibration Specification"

        calPop.option1.ing = ing
        calPop.labelText = ("Use default calibration or\n calibrate %s manually?" % ing.displayNorm)
        calPop.option1.text = "Calibrate Manually"
        calPop.option1.bind(on_press = partial(self.calibrationPrep, calPop, ing))
        calPop.option2.text = "Use Ingredient \nCalibration"
        calPop.option2.bind(on_press = partial(self.dismissCalPop, calPop))
        calPop.option2.halign =  "center"
        calPop.option3.text = "Use Default \nCalibration"
        calPop.option3.halign =  "center"

        calPop.option3.bind(on_press = partial(self.setDefaultCal, calPop))
        calPop.open()


    def setDefaultCal(self, calPop, pressedButton):
    	calPop.option1.ing.calibration = 1
    	self.dismissCalPop(calPop, None)

    def dismissCalPop(self, calPop, pressedButton):
    	calPop.dismiss()

    def calibrationPrep(self, calPop, ing, okayButton):

        calPop.dismiss()

        calPop = CalibrationPrepPopup()
        calPop.open()
        calPop.submitButton.bind(on_release = partial(self.calibrateManually, calPop, ing))


    def calibrateManually(self, calPop, ing, okayButton):

        ounceCount = calPop.ounceCount
        calPop.dismiss()
        self.pourTime = 0
        calPop = TripleOptionPopup()
        calPop.title = "Calibration"
        self.updateLabel(calPop, ounceCount, ing, None)

        calPop.option1.text = "Calibrate"
        calPop.option1.ing = ing
        calPop.option1.bind(on_press = partial(self.pourManuallyStart))
        calPop.option1.bind(on_release = partial(self.updateLabel, calPop, ounceCount, ing))
        calPop.option1.bind(on_release = partial(self.pourManuallyStop))
        calPop.option2.text = "Done"
        calPop.option2.bind(on_release = partial(self.calculateCalibration, ounceCount, ing, calPop))
        calPop.option3.text = "Reset"
        calPop.option3.bind(on_release = partial(self.resetCalibration, calPop, ounceCount, ing))
        calPop.open()


    def updateLabel(self, calPop, ounceCount, ing, okayButton):

        if (float(ounceCount) == 1.0):
            calPop.labelText = ("Press and hold the Calibrate button\n until exactly %s ounce is poured\n\n %.2f seconds to pour %s ounce of %s" % (ounceCount, self.pourTime, ounceCount, ing.displayNorm))
        else:
            calPop.labelText = ("Press and hold the Calibrate button\n until exactly %s ounces are poured\n\n %.2f seconds to pour %s ounces of %s" % (ounceCount, self.pourTime, ounceCount, ing.displayNorm))

    def resetCalibration(self, calPop, ounceCount, ing, okayButton):

        self.pourTime = 0

        self.updateLabel(calPop, ounceCount, ing, okayButton)

    def calculateCalibration(self, ounceCount, ing, calPop, cancelButton):
        calPop.dismiss()

        if (self.pourTime != 0):

	        ing.calibration = self.pourTime / float(ounceCount) / self.ingPins[ing.location]['Calibration']
	        secondsPerOunce = self.pourTime / float(ounceCount)

	        confirmPop = OptionPopup()
	        confirmPop.title = "Set Default?"
	        confirmPop.labelText = ("Set %.2f as the default \n calibration for Bottle %d?" % (secondsPerOunce, (1+ing.location)))
	        confirmPop.okayButton.bind(on_press = partial(self.inputDefaultCal, confirmPop, secondsPerOunce, ing))
	        confirmPop.okayButton.text = "Yes"
	        confirmPop.cancelButton.text = "No"
	        confirmPop.open()

        else:

        	ing.calibration = self.ingPins[ing.location]['Calibration']
        	stupidPop = MessagePopup()
        	stupidPop.title = "Default Calibration Set"
        	stupidPop.labelText = "Calibration time of 0 seconds was entered.\nDefault calibration used instead."
        	stupidPop.buttonText = "Okay, I guess."
        	stupidPop.open()


    def inputDefaultCal(self, confirmPop, secondsPerOunce, ing, pressedButton):
    	confirmPop.dismiss()
    	self.ingPins[ing.location]['Calibration'] = secondsPerOunce
    	ing.calibration = 1


    def setCurButton(self, pairButton):

        if (self.pairingMode):
            self.ingSpinner.values = [ing.displayNorm for ing in self.ingredientList.values() if ((ing.manual == 0) & (ing.location == -1))]
            
            if ((len(self.ingSpinner.values) > 0) | (pairButton.ing.name != self.unpairedText)):
                    self.ingSpinner.values.sort()
                    self.justDisplay = 1
                    self.ingSpinner.values.append(self.unpairedText) 
                    if (pairButton.ing != None):
                        self.ingSpinner.text = pairButton.ing.displayNorm
                    else:
                        self.ingSpinner.text = self.unpairedText

                    self.justDisplay = 0
                    self.ingPopup.open()
            
            self.currentButton = pairButton

        else:
            self.pourManuallyStart(pairButton)

            t = threading.Thread(target=self.liveLabelUpdate, args = [pairButton])
            t.start()

            pairButton.imageSource = "data/icons/bottlePressed.png"


    def liveLabelUpdate(self, pairButton):
        while ((self.endTime - self.startTime) < 0):
            sleep(.1)
            pairButton.pourDur = pairButton.pourDur + .1
            self.updatePairLabel(pairButton)

    def setImageSource(self, pairButton):
        pairButton.imageSource = "data/icons/bottle3.png"

    def updatePairLabel(self, pairButton):
        if ((not self.pairingMode) & (pairButton.ing.displayNorm != self.unpairedText)):
            # pairButton.pourDur = pairButton.pourDur + (time() - self.startTime)

            pairButton.amtText = ("%.2f oz." % (pairButton.pourDur / (self.ingPins[pairButton.ing.location]["Calibration"] * pairButton.ing.calibration)))


    def toggleManualMode(self):
        self.pairingMode = False

        for curRow in [self.row0, self.row1, self.row2]:
            for curButton in curRow.children:
                if (curButton.ing.displayNorm != self.unpairedText):
                    curButton.amtText = "0.00 oz."
                    curButton.pourDur = 0
                else:
                    curButton.amtText = ""

    def togglePairingMode(self, pairButton):
        self.pairingMode = True

        bottleCount = 14
        for curRow in [self.row2, self.row1, self.row0]:
            for curButton in curRow.children:
                curButton.amtText = "Bottle " + str(bottleCount)
                bottleCount = bottleCount - 1


    def settingsPopup(self):
        setPop = MyPopup()
        setPop.manager = self.manager
        setPop.pairButton.bind(on_press = partial(self.togglePairingMode))
        setPop.open()


    def setIngList(self, spinner):
        curType = self.drinkManager[int(spinner.ind)]["TypeSpinner"].text
        if curType == "All":
            spinner.values = self.ingList
        else:
            spinner.values = list(set([ing.name for ing in self.ingredientList.values() if ing.ingType == curType]))

        spinner.values.sort()


    def plusOz(self, button):
        if ((float(self.drinkManager[button.ind]["Label"].text) + self.ounceSetting) <= (float(self.maxAmtInput.text))):
            self.drinkManager[button.ind]["Label"].text = str(float(self.drinkManager[button.ind]["Label"].text) + self.ounceSetting)

    def minusOz(self, button):
        if ((float(self.drinkManager[button.ind]["Label"].text) - self.ounceSetting) >= 0):
            self.drinkManager[button.ind]["Label"].text = str(float(self.drinkManager[button.ind]["Label"].text) - self.ounceSetting)

    def manualPlus(self, label):
        label.text = str(float(label.text) + self.ounceSetting)

    def manualMinus(self, label):
        if ((float(label.text) - self.ounceSetting) >= 0):
            label.text = str(float(label.text) - self.ounceSetting)


    def filterDrinks(self):

        self.avaDrinkListView.adapter.data = self.genFilteredDrinkList()

        self.avaDrinkListView.adapter.data.sort()

        self.avaDrinkListView._trigger_reset_populate()

        liquorList = []
        for ing in self.ingredientList.values():
            if ((ing.manual == 0) & (ing.location != -1)):
                liquorList.append(ing.name)

        self.mainFilter.values = list(set(liquorList))
        self.mainFilter.values.sort()
        self.mainFilter.values.insert(0,"No Filter")

        if ((self.mainFilter.text != "No Filter") & (self.mainFilter.text[0:6] != "Filter")):        
        	self.mainFilter.text = "Filter By: " + self.mainFilter.text




    def genFilteredDrinkList(self):
        
        filteredDrinks = []
        for drink in self.drinkList.keys():
            filtered = 1


            for ing in self.drinkList[drink].ingredients.keys():

            	if (ing in self.ingredientList.keys()):
	                if (self.ingredientList[ing].manual == 1):
	                    if ((self.ingredientList[ing].inStock == 0) and (self.displayToggle.active)):
	                        filtered = 0

	                else:
	                    ingLocList = [ingCheck.location for ingCheck in self.ingredientList.values() if ingCheck.name.lower() == ing.lower()]
	                    if (not any([True for test in ingLocList if test >= 0])):
	                        filtered = 0


                else:
                    ingLocList = [ingCheck.location for ingCheck in self.ingredientList.values() if ingCheck.name.lower() == ing.lower()]
                    if (not any([True for test in ingLocList if test >= 0])):
                        filtered = 0


            if ((self.mainFilter.text not in self.drinkList[drink].ingredients.keys()) & (self.mainFilter.text != "No Filter")):
                filtered = 0

            if (filtered == 1):
                filteredDrinks.append(drink)
        return filteredDrinks
            
        

    def setToggles(self):
        if self.ingListView.adapter.selection:
            selection = self.ingListView.adapter.selection[0].text
            if (self.formatIngInputs() == selection):
                ing = self.ingredientList[selection]
                if self.inStockToggle.active:
                    ing.inStock = 1
                else:
                    ing.inStock = 0

                if self.manualToggle.active:
                    ing.manual = 1
                else:
                    ing.manual = 0

                if (self.ingTypeSpinner.text != "Type"):
                    ing.ingType = self.ingTypeSpinner.text

            self.filterDrinks()



    def popIngFields(self):
        if self.ingListView.adapter.selection:
            selection = self.ingListView.adapter.selection[0].text
            ing = self.ingredientList[selection]
            self.ingName.text = ing.name
            self.brand.text = ing.brand

            if (ing.manual == 1):
                self.manualToggle.active = True
            else: 
                self.manualToggle.active = False

            if (ing.inStock == 1):
                self.inStockToggle.active = True
            else:
                self.inStockToggle.active = False

            if ing.ingType == "":
                self.ingTypeSpinner.text = "Type"
            else:
                self.ingTypeSpinner.text = ing.ingType


    def formatIngInputs(self):
        if (self.brand.text == ""):
            return self.ingName.text

        else:
            return (self.brand.text + " " + self.ingName.text)


    def openNewIngPopup(self):
        self.editingIng = 0
        newIngPopup = self.genIngPopup()
        newIngPopup.submitButton.bind(on_press = partial(self.addNewIngredient, newIngPopup))
        newIngPopup.open()


    def openEditIngPopup(self):
        if not self.ingListView.adapter.selection:
            stupidPop = MessagePopup()
            stupidPop.title = "Selection Error"
            stupidPop.labelText = "No ingredient selected.\nPress any ingredient to select it."
            stupidPop.buttonText = "Okay"
            stupidPop.open()
        else:
            newIngPopup = self.genIngPopup()
            newIngPopup.submitButton.bind(on_press = self.editIngredient)
            newIngPopup.open()

            self.editingIng = 1
            self.popIngFields()


    def genIngPopup(self):
        newIngPopup = NewIngPopup()
        self.brand = newIngPopup.brand
        self.ingName = newIngPopup.ingName
        self.ingTypeSpinner = newIngPopup.ingTypeSpinner
        self.manualToggle = newIngPopup.manualToggle
        self.inStockToggle = newIngPopup.inStockToggle
        self.ingTypeSpinner.values = self.typeList
        self.ingTypeSpinner.values.sort()
        self.ingTypeSpinner.values.insert(0,"-")

        return newIngPopup



    
    def confirmIngredient(self):

        newIng = Ingredient(str(self.ingName.text.rstrip()), brand = str(self.brand.text.rstrip()))

        if self.ingTypeSpinner.text != "Type":
            newIng.ingType = self.ingTypeSpinner.text

        if self.inStockToggle.active:
            newIng.inStock = 1

        if self.manualToggle.active:
            newIng.manual = 1


        if ((newIng.name == "") and (newIng.brand == "")):

            stupidPop = MessagePopup()
            stupidPop.title = "Low Functioning Individual Error"
            stupidPop.labelText = "Ingredient names are kinda required"
            stupidPop.buttonText = "Okay, Mom"
            stupidPop.open()
            return -1

        if ((newIng.name == "") and (newIng.brand != "")):
            stupidPop = MessagePopup()
            stupidPop.title = "Low Functioning Individual Error"
            stupidPop.labelText = "Does it really seem like a good \nidea to add just a brand?"
            stupidPop.buttonText = "No.  No it doesn't."
            stupidPop.open()
            return -1

        # If there is no selection, just check if what"s trying to be added is already in the list
        if ((newIng.displayNorm in self.ingredientList.keys()) & (self.editingIng == 0)):
            warnPop = MessagePopup()
            warnPop.title = "Ingredient Error"
            warnPop.labelText = "Identical ingredient exists.  Duplicates not allowed. \nConsider adding or altering the brand."
            warnPop.open()
            return -1

        else:
            return newIng



    def addNewIngredient(self, ingPopup, submitButton):

        newIng = self.confirmIngredient()

        if (newIng != -1):
            listName = newIng.displayNorm

            self.ingredientList[listName] = newIng

            self.ingListView.adapter.data.insert(0, listName)

            self.ingListView.adapter.data.sort()

            self.ingListCleanup()



    def editIngredient(self, submitButton):

        newIng = self.confirmIngredient()
        selection = self.ingListView.adapter.selection[0].text
        oldIng = self.ingredientList[selection]

        if (newIng != -1):
            listName = newIng.displayNorm


            if (listName not in self.ingredientList.keys()):
                self.substituteIngredient(newIng, oldIng)
                self.deleteIngredient(None, None)
                newIng.calibration = oldIng.calibration
                newIng.location = oldIng.location
                self.ingredientList[listName] = newIng

            else:
                self.ingListView.adapter.data.remove(listName)
                oldIng.manual = newIng.manual
                oldIng.inStock = newIng.inStock
                oldIng.ingType = newIng.ingType

            self.filterDrinks()

            # Add the student to the ListView
            self.ingListView.adapter.data.insert(0, listName)

            self.ingListView.adapter.data.sort()


    def ingListCleanup(self):

        self.typeList = list(set([ing.ingType for ing in self.ingredientList.values()]))
        if ("" in self.typeList):
            self.typeList.remove("")
        self.ingList = list(set([ing.name for ing in self.ingredientList.values()]))

        self.filterDrinks()
        self.ingListView._trigger_reset_populate()
 
    def deleteIngredientConfirm(self):
 
        # If a list item is selected
        if self.ingListView.adapter.selection:

            # Get the text from the item selected
            selection = self.ingListView.adapter.selection[0].text

            for drink in self.drinkList.values():
                if selection in drink.ingredients.keys():
                    delIngPop = MessagePopup()
                    delIngPop.title = "Ingredient In Use Error"
                    delIngPop.labelText = ("%s is currently in use in a %s. \nManage that recipe before deleting." % (selection, drink.name))
                    delIngPop.buttonText = "Okay"
                    delIngPop.open()
                    return

            confirmPop = OptionPopup()
            confirmPop.title = "Deletion Confirmation"
            confirmPop.labelText = "Deleting %s will obliterate \nit from your entire library." % (selection)
            confirmPop.okayButton.bind(on_press = partial(self.deleteIngredient, confirmPop))
            confirmPop.okayButton.text = "Delete"
            confirmPop.open()

        else:
            delIngPop = MessagePopup()
            delIngPop.title = "No Selection Error"
            delIngPop.labelText = "No ingredient currently selected."
            delIngPop.buttonText = "Wow"
            delIngPop.open()
            return


    def deleteIngredient(self, confirmPop, okayButton):

        selection = self.ingListView.adapter.selection[0].text

        if (confirmPop != None):
            confirmPop.dismiss()

        self.ingListView.adapter.data.remove(selection)

        if selection in self.ingredientList.keys(): del self.ingredientList[selection]

        self.ingListView._trigger_reset_populate()


    def substituteIngredient(self, newIng, oldIng):

    	listName = newIng.displayNorm

        if self.ingListView.adapter.selection:

            selection = oldIng.name

            for drink in self.drinkList.values():
                oldIngs = drink.ingredients
                if selection in oldIngs.keys():
                    newIngs = {}
                    for ing in oldIngs.keys():
                        if (ing == selection):
                            newIngs[newIng.name] = oldIngs[ing]
                        else:
                            newIngs[ing] = oldIngs[ing]

                    drink.ingredients = newIngs


            for curRow in [self.row0, self.row1, self.row2]:
                for curButton in curRow.children:
                    if (curButton.ing.displayNorm != self.unpairedText):
                        if (curButton.text == oldIng.displaySmall):
                            curButton.ing = newIng



 
    def filterIngListView(self, filterBy):
        if (filterBy.lower() == 'manual'):
            self.ingListView.adapter.data = []
            for ing in self.ingredientList.values():
                if ing.manual:
                    self.ingListView.adapter.data.insert(0, ing.displayNorm)
            self.ingListView.adapter.data.sort()

        elif (filterBy.lower() == 'automatic'):
            self.ingListView.adapter.data = []
            for ing in self.ingredientList.values():
                if (ing.manual == 0):
                    self.ingListView.adapter.data.insert(0, ing.displayNorm)
            self.ingListView.adapter.data.sort()

        elif (filterBy.lower() == 'in stock'):
            self.ingListView.adapter.data = []
            for ing in self.ingredientList.values():
                if (ing.inStock and ing.manual):
                    self.ingListView.adapter.data.insert(0, ing.displayNorm)
            self.ingListView.adapter.data.sort()

        elif (filterBy.lower() == 'not in stock'):
            self.ingListView.adapter.data = []
            for ing in self.ingredientList.values():
                if ((ing.inStock == 0) and (ing.manual)):
                    self.ingListView.adapter.data.insert(0, ing.displayNorm)
            self.ingListView.adapter.data.sort()

        elif (filterBy.lower() == "no filter"):
            self.ingListView.adapter.data = []
            for ing in self.ingredientList.values():
                self.ingListView.adapter.data.insert(0, ing.displayNorm)
            self.ingListView.adapter.data.sort()

        else:
            if (filterBy in self.typeList):
                self.ingListView.adapter.data = []

                for ing in self.ingredientList.values():
                    if (ing.ingType == filterBy):
                        self.ingListView.adapter.data.insert(0, ing.displayNorm)
                self.ingListView.adapter.data.sort()

    def applySettings(self):


        try:
            self.ounceInput.text = str(round(float(self.ounceInput.text.rstrip()),2))
        except ValueError:
            self.ounceInput.text = str(.25)

        try:
            self.maxAmtInput.text = str(round(float(self.maxAmtInput.text.rstrip()),2))
        except ValueError:
            self.maxAmtInput.text = str(4.0)

        try:
            self.shotInput.text = str(round(float(self.shotInput.text.rstrip()),2))
        except ValueError:
            self.shotInput.text = str(1.5)

        try:
            self.strengthInput.text =  str(round(float(self.strengthInput.text.rstrip()),2))
        except ValueError:
            self.strengthInput.text = str(25)




        self.ounceSetting = float(self.ounceInput.text)
        self.strengthSetting = float(self.strengthInput.text)

        self.filterDrinks()

    def managementAdd(self, curField, curListView, listType):

        curList = self.findList(listType)

        if (curField.text == ""):
            stupidPop = MessagePopup()
            stupidPop.title = "Low Functioning Individual Error"
            stupidPop.labelText = "You can't add nothing.  Idiot."
            stupidPop.buttonText = "Okay"
            stupidPop.open()
            return


        if ((curField.text.rstrip() not in curList) & (curField.text.rstrip() != "")):
            curList.append(curField.text.rstrip())
            curList.sort()

            # Add the student to the ListView
            curListView.adapter.data.insert(0, curField.text.rstrip())
     
            # Reset the ListView
            curListView._trigger_reset_populate()
            curField.text = ""

            self.updateLists()
        else:
            stupidPop = MessagePopup()
            stupidPop.title = "Duplicate Error"
            stupidPop.labelText = ("%s is already in your Library" % curField.text.rstrip())
            stupidPop.buttonText = "Dismiss"
            stupidPop.open()



    def manDelConfirm(self, curListView, listType):

        if curListView.adapter.selection:

            confirmPop = OptionPopup()
            confirmPop.title = "Deletion Confirmation"
            confirmPop.labelText = "Deleting %s will obliterate \nit from your entire library." % (curListView.adapter.selection[0].text)
            confirmPop.okayButton.bind(on_press = partial(self.managementDelete, curListView, listType, confirmPop))
            confirmPop.okayButton.text = "Delete"
            confirmPop.open()

        else:
            stupidPop = MessagePopup()
            stupidPop.title = "Low Functioning Individual Error"
            stupidPop.labelText = "You can't delete nothing.\nBecause then nothing couldn't be."
            stupidPop.buttonText = "Okay"
            stupidPop.open()
            return


    def  managementDelete(self, curListView, listType, confirmPop, button):

        confirmPop.dismiss()

        curList = self.findList(listType)

        # If a list item is selected
        if curListView.adapter.selection:

            # Get the text from the item selected
            selection = curListView.adapter.selection[0].text
 
            # Remove the matching item
            curListView.adapter.data.remove(selection)

            curList.remove(selection)

            # Reset the ListView
            curListView._trigger_reset_populate()

            if (listType == "prep"):
                for drink in self.drinkList.values():
                    if drink.prepMethod == selection:
                        drink.prepMethod = ""
            elif (listType == "glass"):
                for drink in self.drinkList.values():
                    if drink.glassware == selection:
                        drink.glassware = ""
            elif (listType == "type"):
                for ing in self.ingredientList.values():
                    if ing.ingType == selection:
                        ing.ingType = ""

            self.updateLists()

    def findList(self, listType):

        curList = None

        if (listType == "prep"):
            curList = self.prepList
        elif (listType == "glass"):
            curList = self.glassList 
        elif (listType == "type"):
            curList = self.typeList

        return curList


    def populate(self):


		self.ounceInput.text = str(self.ounceSetting)      
		self.strengthInput.text = str(self.strengthSetting)

		for ing in self.ingredientList.values():
		    self.ingListView.adapter.data.extend([ing.displayNorm])

		    if ing.location != -1:
		        self.initialPairings[ing.location] = ing

		self.ingListView.adapter.data.sort()

		self.ingList = list(set([ing.name for ing in self.ingredientList.values()]))

		for drink in self.drinkList.keys():
		    self.drinkListView.adapter.data.extend([drink])

		self.drinkListView.adapter.data.sort()

		self.filterDrinks()


		# self.glassSpinner.values = self.glassList
		# self.prepSpinner.values = self.prepList

		for item in self.glassList:
		    self.glassListView.adapter.data.extend([item])

		for item in self.prepList:
		    self.prepListView.adapter.data.extend([item])

		for item in self.typeList:
		    self.typeListView.adapter.data.extend([item])

		self.glassListView.adapter.data.sort()
		self.prepListView.adapter.data.sort()
		self.typeListView.adapter.data.sort()

		liquorList = []
		for ing in self.ingredientList.values():
		    if ((ing.manual == 0) & (ing.location != -1)):
		        liquorList.append(ing.name)

		self.mainFilter.values = list(set(liquorList))
		self.mainFilter.values.sort()
		self.mainFilter.values.insert(0,"No Filter")





		self.typeList.sort()

		self.popPairIngs()


    def updateLists(self):
        self.typeListView.adapter.data.sort()

        self.typeList.sort()

        self.filterSpinner.values = self.filterConstants + self.typeList

        # self.glassSpinner.values = self.glassList
        # self.glassSpinner.values.sort()
        # self.glassListView.adapter.data.sort()
        # self.glassSpinner.values.insert(0, self.glassName)

        # self.prepSpinner.values = self.prepList
        # self.prepSpinner.values.sort()
        # self.prepListView.adapter.data.sort()
        # self.prepSpinner.values.insert(0, self.prepName)

    def popPairIngs(self):

        self.updateLists()

        ind = -1

        for i in self.rows.keys():
            for num in range(self.rows[i]["Count"]):
                ind = ind + 1
                bottleButton = Builder.load_string("""
Button:
    id: button%d
    size_hint: None,None
    size: (140,140) 
    background_color: (0,0,0,0)
    background_normal: ""
    ind: %d
    halign: "center"
    text: "%s" if self.ing == None else self.ing.displaySmall
    ing: None
    amtText: "Bottle %d"
    pourDur: 0
    imageSource: "data/icons/bottle3.png"
    bottleImage: bottleImage 

    Label:
        text: root.amtText
        y: ((2 * self.parent.y + self.parent.height) / 2) - (self.height / 2) + 30
        x: ((2 * self.parent.x + self.parent.width) / 2) - (self.width / 2)
        size_hint_y: None
        size_hint_x: None
        height: self.parent.height
        width: self.parent.width

    Image:
        id: bottleImage
        source: root.imageSource
        y: ((2 * self.parent.y + self.parent.height) / 2) - (self.height / 2)
        x: ((2 * self.parent.x + self.parent.width) / 2) - (self.width / 2)
        size_hint_y: None
        size_hint_x: None
        height: self.parent.height
        width: self.parent.width

""" % (ind, ind, self.unpairedText, (ind + 1)))


                bottleButton.ing = Ingredient(self.unpairedText)
                bottleButton.bind(on_press = self.setCurButton)
                bottleButton.bind(on_release = self.setImageSource)
                bottleButton.bind(on_release = partial(self.pourManuallyStop))

                if ind not in self.initialPairings.keys():
                    bottleButton.text = self.unpairedText
                else:
                    bottleButton.ing = self.initialPairings[ind]
                    # self.manualIngSpinner.values.append(bottleButton.ing.displayNorm)

                if i == 0:
                    self.row0.add_widget(bottleButton)
                elif i == 1:
                    self.row1.add_widget(bottleButton)
                elif i == 2:
                    self.row2.add_widget(bottleButton)

            self.initialized = 1
            # self.manualIngSpinner.values.sort()


    def deleteDrinkConfirm(self):

        if self.drinkListView.adapter.selection:

            confirmPop = OptionPopup()
            confirmPop.title = "Deletion Confirmation"
            confirmPop.labelText = "Deleting %s will obliterate \nit from your entire library." % (self.drinkListView.adapter.selection[0].text)
            confirmPop.okayButton.bind(on_press = partial(self.deleteDrink, confirmPop))
            confirmPop.okayButton.text = "Delete"
            confirmPop.open()

        else:
            stupidPop = MessagePopup()
            stupidPop.title = "Selection Error"
            stupidPop.labelText = "No drink selected to delete."
            stupidPop.buttonText = "Okay"
            stupidPop.open()



    def deleteDrink(self, confirmPop, curButton):

        if (confirmPop != None):
            confirmPop.dismiss()

        # If a list item is selected
        if self.drinkListView.adapter.selection:

            # Get the text from the item selected
            selection = self.drinkListView.adapter.selection[0].text
 
            # Remove the matching item
            self.drinkListView.adapter.data.remove(selection)

            if selection in self.drinkList.keys(): del self.drinkList[selection]
 
            # Reset the ListView
            self.drinkListView._trigger_reset_populate()

    def choosePrep(self):

        ingredients = {}
        for drinkIng in self.drinkManager:
            if (drinkIng["Spinner"].text != ""):
                ingredients[drinkIng["Spinner"].text] = {"Amount":float(drinkIng["Label"].text)}

        if (self.drinkName.text.rstrip() == ""):
            stupidPop = MessagePopup()
            stupidPop.title = "Name Error"
            stupidPop.labelText = "This drink has no name :("
            stupidPop.buttonText = "Okay, it deserves a name."
            stupidPop.open()
            return

        elif (len(ingredients) == 0):
            stupidPop = MessagePopup()
            stupidPop.title = "Creation Error"
            stupidPop.labelText = "No ingredients added to this drink."
            stupidPop.buttonText = "Okay"
            stupidPop.open()
            return


        prepPop = SpinnerPopup()
        prepPop.title = "Preparation Method"
        prepPop.labelText = "1. How is a " + self.drinkName.text + " prepared?"
        prepPop.okayButton.bind(on_press = partial(self.chooseGlass, prepPop))
        prepPop.okayButton.text = "Submit"
        prepPop.spinnerValues = self.prepList
        prepPop.optionSpinner.text = self.prepSpinnerText
        prepPop.open()


    def chooseGlass(self, prepPop, button):
        prepPop.dismiss()

        self.manager.current = "One"

        glassPop = SpinnerPopup()
        glassPop.title = "Glassware Selection"
        glassPop.labelText = "2. What is a " + self.drinkName.text + " served in?"
        glassPop.okayButton.bind(on_press = partial(self.submitDrink, prepPop, glassPop))
        glassPop.okayButton.text = "Submit"
        glassPop.spinnerValues = self.glassList
        glassPop.optionSpinner.text = self.glassSpinnerText
        glassPop.open()




    def submitDrink(self, prepPop, glassPop, button):

        glassPop.dismiss()

        ingredients = {}
        for drinkIng in self.drinkManager:
            if (drinkIng["Spinner"].text != ""):
                ingredients[drinkIng["Spinner"].text] = {"Amount":float(drinkIng["Label"].text)}




        if (self.managing == 1):
            self.deleteDrink(None, None)

        if prepPop.optionSpinner.text == self.prepName:
            prepType = ""
        else:
            prepType = prepPop.optionSpinner.text

        if glassPop.optionSpinner.text == self.glassName:
            glassType = ""
        else:
            glassType = glassPop.optionSpinner.text

        self.drinkList[self.drinkName.text.rstrip()] = Drink(self.drinkName.text.rstrip(), glassware = glassType, prepMethod = prepType, ingredients = ingredients)
        self.drinkListView.adapter.data.insert(0, self.drinkName.text.rstrip())

        self.drinkListView.adapter.data.sort()
        self.drinkListView._trigger_reset_populate()

        for child in [child for child in self.ingBl.children]:  
            if hasattr(child, "type"):
                if child.type == "IngLayout":
                    self.ingBl.remove_widget(child)

        self.filterDrinks()

        self.manager.current = "Eight"


    def populateManageDrink(self, layout):

        self.managing = 1


        for child in [child for child in layout.children]:  
            if hasattr(child, "type"):
                if child.type == "IngLayout":
                    layout.remove_widget(child)

        if self.drinkListView.adapter.selection:
            self.manager.current = "Four"

            selection = self.drinkListView.adapter.selection[0].text
            drink = self.drinkList[selection]

            self.ingCount = -1
            self.drinkManager = []

            for drinkIng in drink.ingredients.keys():
                curDrinkIng = self.addRow(layout)
                curDrinkIng["Spinner"].text = drinkIng
                if (drinkIng in self.ingredientList.keys()):
                    curDrinkIng["TypeSpinner"].text = self.ingredientList[drinkIng].ingType
                else: 
                    curDrinkIng["TypeSpinner"].text = ""
                curDrinkIng["Label"].text = str(drink.ingredients[drinkIng]["Amount"])

            self.drinkName.text = drink.name

            if drink.prepMethod != "":
                self.prepSpinnerText = drink.prepMethod
            else:
                self.prepSpinnerText = self.prepName
            if drink.glassware != "":
                self.glassSpinnerText = drink.glassware
            else: 
                self.glassSpinnerText = self.glassName

        else:
            stupidPop = MessagePopup()
            stupidPop.title = "Selection Error"
            stupidPop.labelText = "No drink selected to manage."
            stupidPop.buttonText = "Okay"
            stupidPop.open()



    def clearManageDrink(self, layout):

        self.managing = 0

        for child in [child for child in layout.children]:  
            if hasattr(child, "type"):
                if child.type == "IngLayout":
                    layout.remove_widget(child)

        self.drinkName.text = ""
        self.manager.current = "Four"
        self.ingCount = -1
        self.drinkManager = []
        self.prepSpinnerText = self.prepName
        self.glassSpinnerText = self.glassName
        self.addRow(layout)


    def makeDrink(self, layout):

        if ((len(self.avaDrinkListView.adapter.selection)>0) | (self.bartenderChoosing == 1)):

            if (self.bartenderChoosing == 1):
                selection = self.bartenderSelection
            else:
                selection = self.avaDrinkListView.adapter.selection[0].text

            if (selection in self.genFilteredDrinkList()):

                self.curDrinkManager = []

                for child in [child for child in layout.children]:  
                    if hasattr(child, "type"):
                        if child.type == "IngLayout":
                            layout.remove_widget(child)

                drink = self.drinkList[selection]


                self.drinkTitle.labelName = drink.name
                self.drinkTitle.drink = drink
                # self.shotTitle.text = "Pour Shot of " + drink.name
                self.manager.current = "Five"
                drinkCount = -1
                for i, baseIngName in enumerate(drink.ingredients.keys()):
                    for testIng in self.ingredientList.values():
                        if testIng.name == baseIngName:
                            ingKey = testIng.displayNorm

                    if (baseIngName in self.ingredientList.keys()):
                        ingKey = baseIngName

                    if (self.ingredientList[ingKey].manual == 0):
                        drinkCount = drinkCount + 1
                        newRow = Builder.load_string("""
BoxLayout:
    type: "IngLayout"
    spacing: 20
    size_hint_y: None
    padding: [20,0,20,0]
    brands: [""]

    height: "30dp"

    Label:
        type: "Ingredient"
        text: "%s"

    Spinner:
        type: "Spinner"
        text: "-"
        values: self.parent.brands

    Slider:
        type: "Slider"
        steps: .1
        value: 0
        min: %d
        max: %d

    CheckBox:
        id: manualToggle
        type: "Toggle"
        canvas.before:
            Color:
                rgb: 1,1,1
            Rectangle:
                pos:self.center_x-8, self.center_y-8
                size:[16,16]

""" % (baseIngName, self.strengthSetting * -1, self.strengthSetting))


                        newRow.brands = [ing.brand for ing in self.ingredientList.values() if ((ing.name == baseIngName) & (ing.location != -1))]
                        if ("" in newRow.brands):
                            newRow.brands.remove("")

                        if (baseIngName in self.ingredientList.keys()):
                            if (self.ingredientList[ingKey].location != -1):
                                print "found Gin"
                                newRow.brands.append("-")

                        layout.add_widget(newRow)
                        layout.height = (str(drinkCount * 30 + 35) + "dp")

                        recipe = {"Layout": newRow}
                        for child in newRow.children:
                            if hasattr(child, "type"):
                                if (child.type == "Spinner"):
                                    recipe["Spinner"] = child
                                    child.text = child.values[-1]
                                elif (child.type == "Slider"):
                                    recipe["Slider"] = child
                                elif (child.type == "Toggle"):
                                    recipe["Toggle"] = child
                                elif (child.type == "Ingredient"):
                                    recipe["Ingredient"] = child.text
                        self.curDrinkManager.append(recipe)

        else:
            stupidPop = MessagePopup()
            stupidPop.title = "Selection Error"
            stupidPop.labelText = "No drink selected to make."
            stupidPop.buttonText = "Okay"
            stupidPop.open()

        self.bartenderChoosing = 0


    def howManyDrinks(self, drink, drinkType):

        if (all([row["Toggle"].active for row in self.curDrinkManager])):
            stupidPop = MessagePopup()
            stupidPop.title = "No Ingredients Included Error"
            stupidPop.labelText = "Nice.  A drink with no ingredients.  Real nice."
            stupidPop.buttonText = "Okay"
            stupidPop.open()
            return

        else:

            countPop = CountPopup()
            countPop.drinkType = drinkType
            countPop.open()
            countPop.countButton.bind(on_press = partial(self.calcIngs, drink, drinkType))

    def calcIngs(self, drink, drinkType, button):

        oldIngs = drink.ingredients
        newIngs = {}

        if (button.pourIndividually.active):
            drinkPourCount = 1.0
            repeatTarget = float(button.count[0])
        else:
            drinkPourCount = float(button.count[0])
            repeatTarget = 1.0

              
        for ing in oldIngs.keys():
            for ing2 in self.curDrinkManager:
                toExclude = False
                curStrength = 0
                if (ing2["Ingredient"] == ing):
                    curStrength = ing2["Slider"].value
                    toExclude = ing2["Toggle"].active

            if (not toExclude):
                newIngs[ing] = {"Amount": round((oldIngs[ing]["Amount"] * drinkPourCount * (1 + curStrength / 100.)), 3)}

        newDrink = Drink("NewDrink", ingredients = newIngs, prepMethod = drink.prepMethod, glassware = drink.glassware)
        if (drinkType == "Drink"):
            self.progressPopGen(newDrink, repeatTarget)
        elif (drinkType == "Shot"):
            self.calcShots(newDrink, drinkPourCount, repeatTarget)


    def calcShots(self, drink, drinkCount, repeatTarget):
        oldIngs = drink.ingredients
        newIngs = {}
        totalOunces = 0.0

        for ing in oldIngs.keys():
            totalOunces = totalOunces + float(oldIngs[ing]["Amount"])

        for ing in oldIngs.keys():
            newIngs[ing] = {"Amount": round((float(oldIngs[ing]["Amount"]) / totalOunces * float(self.shotInput.text) * drinkCount), 3)}
        self.progressPopGen(Drink("NewDrink", ingredients = newIngs, prepMethod = drink.prepMethod, glassware = drink.glassware), repeatTarget)



    def progressPopGen(self, drink, repeatTarget):
        progressPop = ProgressPopup(auto_dismiss = False)
        progressPop.open()
        progressPop.manager = self.manager
        progressPop.repeatTarget = repeatTarget
        progressPop.drink = drink
        progressPop.cancelButton.bind(on_press = partial(self.cancelPour, progressPop))

        if (repeatTarget > 1):
            progressPop.continueButton.text = ("Click to Pour Drink %d of %d" % ((progressPop.repeatCount + 1), progressPop.repeatTarget))
        else:
            progressPop.continueButton.text = "Click to Pour Drinks"

        ingMessage = ""
        ingCount = 0
        ingsToPour = {}
        pourDur = 0


        for row in self.curDrinkManager:
            ingName = row["Ingredient"]
            if (row["Spinner"].text != "-"):
                ingName = row["Spinner"].text + " " + ingName

            curIng = self.ingredientList[ingName]
            ing = curIng.name

            if (curIng.manual == 1):
                ingCount = ingCount + 1
                ingMessage = ingMessage + str(round(drink.ingredients[ing]["Amount"], 2)) + " ounces of " + ing + ",\n"

            else:
                curLocation = self.ingPins[curIng.location]
                curPin = curLocation['GPIO']

                ingsToPour[ing] = {"Time": drink.ingredients[ing]["Amount"] * curIng.calibration * curLocation["Calibration"], "Pin": curPin}

                if (ingsToPour[ing]["Time"] > pourDur):
                    pourDur = ingsToPour[ing]["Time"]

        print pourDur

        # for ing in drink.ingredients.keys():

        #     if (ing in self.ingredientList.keys()):
        #         if (self.ingredientList[ing].manual == 1):
        #             ingCount = ingCount + 1
        #             ingMessage = ingMessage + str(round(drink.ingredients[ing]["Amount"], 2)) + " ounces of " + ing + ",\n"

        #         elif (self.ingredientList[ing].manual == 0):
        #             if (len(self.curDrinkManager) > 0):
        #                 for row in self.curDrinkManager:
        #                     if ing == row["Ingredient"]:
        #                         if (row["Spinner"].text == "-"):
        #                             curIng = self.ingredientList[ing]
        #                             curLocation = self.ingPins[curIng.location]
        #                             curPin = curLocation['GPIO']
        #                         else:
        #                             for ingBrand in self.ingredientList.values():
        #                                 if ((ingBrand.brand == row["Spinner"].text) & (ingBrand.name == ing)):
        #                                     curIng = ingBrand
        #                                     curLocation = self.ingPins[ingBrand.location]
        #                                     curPin = curLocation['GPIO']
        #             else:
        #                 curPin = self.ingPins[self.ingredientList[ing].location]['GPIO']

        #             ingsToPour[ing] = {"Time": drink.ingredients[ing]["Amount"] * curIng.calibration * curLocation["Calibration"], "Pin": curPin}

        #             if (ingsToPour[ing]["Time"] > pourDur):
        #                 pourDur = ingsToPour[ing]["Time"]


        ingMessage = ingMessage[:-2]
        ingMessage = ingMessage + "\n"
        
        if (drink.name == "ExactDrink"):
            for ing in drink.ingredients.keys():
                drinkKey = ing
            progressPop.instructionsText = "Pouring " + str(drink.ingredients[drinkKey]["Amount"]) + " ounces of " + drinkKey + "\n\n"
        
        else:
            if (ingCount == 0):
                ingMessage = "Once poured, "
            else:
                ingMessage = ("Once poured, add: \n" + ingMessage)

            if (drink.glassware == ""):
                glassText = ""
            else:
                glassText = " in a " + drink.glassware.lower()

            if (drink.prepMethod == ""):
                if (ingCount == 0):
                    prepText = "serve "
                else:
                    prepText = "Serve "                    
            else:
                if (ingCount == 0):
                    prepText = "serve " + drink.prepMethod.lower()
                else:
                    prepText = "Serve " + drink.prepMethod.lower()

            progressPop.instructionsText = ingMessage + prepText+ glassText + "\n\n"

        progressPop.continueButton.bind(on_press = partial(self.pourDrink, progressPop, pourDur, ingsToPour))





    def pourDrink(self, progressPop, pourDur, ingsToPour, progressButton):

        drink = progressPop.drink
        progressPop.continueButton.disabled = True
        progressPop.pbValue = 0
        progressPop.continueButton.text = "Pour in Progress"

        if (progressPop.repeatCount < progressPop.repeatTarget):

            progressPop.repeatCount = progressPop.repeatCount + 1


            self.pbEvent = Clock.schedule_interval(partial(self.incrementPB, progressPop), (pourDur + self.ullagePressTime) / 100.)

            t = threading.Thread(target=self.openValves, args = [ingsToPour])
            t.start()

        else:
            progressPop.dismiss()
            self.manager.current = "One"

    def cancelPour(self, makePop, cancelButton):
        self.isCancelled = True
        makePop.continueButton.text = "Drink Cancelled\nClick to Continue"


        for pin in self.ingPins.values():
            GPIO.output(pin["GPIO"],0)

        if ((makePop.repeatCount == 0) | (makePop.pbValue == 0) | (makePop.pbValue >= 100)):
	        makePop.dismiss()
	        self.manager.current = "One"

        makePop.repeatCount = 10


    def pourExactConfirm(self, ingName, ingAmount):
        if (ingName != self.unselectedText):
            ings = {ingName: {"Amount": float(ingAmount)}}

            confirmPop = OptionPopup()
            confirmPop.title = "Pour Confirmation"
            confirmPop.labelText = "Pour %s ounces of  %s?" % (ingAmount, ingName)
            confirmPop.okayButton.bind(on_press = partial(self.pourExact, confirmPop, ings))
            confirmPop.okayButton.text = "Yes!"
            confirmPop.open()

        else:
            stupidPop = MessagePopup()
            stupidPop.title = "Selection Error"
            stupidPop.labelText = "No ingredient selected."
            stupidPop.buttonText = "Okay"
            stupidPop.open()

    def pourExact(self, confirmPop, ings, button):
        confirmPop.dismiss()
        self.pourDrink(Drink("ExactDrink", ingredients = ings))


    def showRecipe(self):

        if (self.drinkTitle.labelName[0].lower() in 'aeiou'):
            recipeText = "An " + self.drinkTitle.labelName + " is:\n\n"

        else:
            recipeText = "A " + self.drinkTitle.labelName + " is:\n\n"
        curDrink = self.drinkTitle.drink

        for ing in curDrink.ingredients.keys():
            line = ("%.2f ounces of %s\n" % (curDrink.ingredients[ing]["Amount"], ing))
            recipeText = recipeText + line

        stupidPop = MessagePopup()
        stupidPop.size = (400, (180 + 20 * len(curDrink.ingredients)))
        stupidPop.messageLabel.halign = 'left'
        stupidPop.title = self.drinkTitle.labelName + " Recipe"
        stupidPop.labelText = recipeText
        stupidPop.buttonText = "Okay"
        stupidPop.open()



    def incrementPB(self, progressBar, *largs):
        if ((progressBar.pbValue < 100) & (not self.isCancelled)):
            progressBar.pbValue = progressBar.pbValue + 1

        else:

        	progressBar.continueButton.disabled = False

        	if (self.isCancelled):
			    progressBar.repeatCount = progressBar.repeatTarget
			    progressBar.pbValue = 0
			    progressBar.continueButton.text = "Drink Cancelled\nClick to Continue"

	        else:

	            if (progressBar.repeatCount < progressBar.repeatTarget):
	                progressBar.continueButton.text = ("Click to Pour Drink %d of %d" % ((progressBar.repeatCount + 1), progressBar.repeatTarget))
	            else:
	                progressBar.continueButton.text = "Click to Continue"

	            self.pbEvent.cancel()


    def openValves(self, ingsToPour):

        times = []
        pins = []
        ings = []
        for ing in ingsToPour.keys():
            times.append(ingsToPour[ing]["Time"])
            pins.append(ingsToPour[ing]["Pin"])

        inds = sorted(range(len(times)), key=lambda k: times[k])

        times = [times[ind] for ind in inds]
        pins = [pins[ind] for ind in inds]
        GPIO.output(self.pressurePin, 1)
        sleep(self.ullagePressTime)

        for i in range(1,len(times)):
            for j in range(i,len(times)):
                times[j] = times[j] - times[i-1]

        for pin in ingsToPour.values():
            GPIO.output(pin["Pin"],1)

        for i in range(len(times)):
            sleep(times[i])
            GPIO.output(pins[i],0)
            if (self.isCancelled):
                return

        for pin in ingsToPour.values():
            GPIO.output(pin["Pin"],0)

        GPIO.output(self.pressurePin, 0)


    def addRow(self, layout):
        if (self.ingCount < 9):

            self.ingCount = self.ingCount + 1
            newRow = Builder.load_string("""
BoxLayout:
    type: "IngLayout"
    spacing: 10
    size_hint_y: None
    padding: [20,0,20,0]
    ingList: []
    typeList: []
    ind: %d

    height: "30dp"

    BoxLayout: 
        Spinner:
            type: "TypeSpinner"
            text: "All"
            values: self.parent.parent.typeList
            ind: self.parent.parent.ind

    BoxLayout:
        Spinner:
            type: "Spinner"
            values: self.parent.parent.ingList
            ind: self.parent.parent.ind


    BoxLayout:

        Button:

            background_color: (0,0,0,1)
            background_normal: ""
            type: "Minus"
            ind: self.parent.parent.ind


            Image:
                source: "data/icons/minus.png"
                y: ((2 * self.parent.y + self.parent.height) / 2) - (self.height / 2)
                x: ((2 * self.parent.x + self.parent.width) / 2) - (self.width / 2)
                size_hint_y: None
                size_hint_x: None
                height: 20
                width: 20

        Label:
            type: "Label"
            halign: "center"
            text: "1.0"

        Button:
            background_color: (0,0,0,0)
            background_normal: ""
            type: "Plus"
            ind: self.parent.parent.ind


            Image:
                source: "data/icons/plus2.png"
                y: ((2 * self.parent.y + self.parent.height) / 2) - (self.height / 2)
                x: ((2 * self.parent.x + self.parent.width) / 2) - (self.width / 2)
                size_hint_y: None
                size_hint_x: None
                height: 20
                width: 20

""" % self.ingCount)

            newRow.ingList = self.ingList
            newRow.typeList = self.typeList
            newRow.typeList.sort()
            newRow.typeList.insert(0, "All")
            layout.height = (str(self.ingCount * 30 + 35) + "dp")



            recipe = {"Layout": newRow}
            for child2 in newRow.children:
                if len(child2.children) > 0:
                    for child in child2.children:
                        if hasattr(child, "type"):
                            if (child.type == "Spinner"):
                                recipe["Spinner"] = child
                            elif (child.type == "Label"):
                                recipe["Label"] = child
                            elif (child.type == "TypeSpinner"):
                                recipe["TypeSpinner"] = child
                            elif (child.type == "Plus"):
                                recipe["Plus"] = child
                            elif (child.type == "Minus"):
                                recipe["Minus"] = child


            recipe["Spinner"].bind(on_press = self.setIngList)
            recipe["Plus"].bind(on_press = self.plusOz)
            recipe["Minus"].bind(on_press = self.minusOz)

            layout.add_widget(newRow)

            self.drinkManager.append(recipe)

            return recipe

    def removeRow(self, layout):
        if (self.ingCount >= 1):
            layout.remove_widget(layout.children[0])
            self.ingCount = self.ingCount -1
            layout.height = (str(self.ingCount * 30 + 35) + "dp")

            self.drinkManager.pop()

    def bartendersChoice(self, layout):

        ind = randint(0,len(self.genFilteredDrinkList())-1)
        for i, drink in enumerate(self.genFilteredDrinkList()):
            if (i == ind):
                self.bartenderSelection = drink
        self.bartenderChoosing = 1
        self.makeDrink(layout)

    def pourManuallyStart(self, pourButton):
        self.startTime = time()

        if (pourButton.ing.displayNorm != self.unselectedText):
            ingPin = self.ingPins[pourButton.ing.location]['GPIO']
            GPIO.output(self.pressurePin, 1)
            GPIO.output(ingPin, 1)

        else:
            stupidPop = MessagePopup()
            stupidPop.title = "Selection Error"
            stupidPop.labelText = "No ingredient selected."
            stupidPop.buttonText = "Okay"
            stupidPop.open()

    def pourManuallyStop(self, pourButton):
        self.endTime = time()
        if (pourButton.ing.displayNorm != self.unselectedText):
            ingPin = self.ingPins[pourButton.ing.location]['GPIO']
            GPIO.output(self.pressurePin, 0)
            GPIO.output(ingPin, 0)

            self.pourTime = self.pourTime + (self.endTime - self.startTime)

    def purgePopup(self):

        calPop = OptionPopup()
        calPop.title = "Purge Lines?"
        calPop.labelText = "Purge all paired locations?"
        calPop.okayButton.bind(on_press = partial(self.purgeLines, calPop))

        calPop.okayButton.text = "Confirm"
        calPop.cancelButton.text = "Cancel"
        calPop.open()

    def purgeLines(self, calPop, purgeButton):
        calPop.dismiss()

        stupidPop = MessagePopup()
        stupidPop.title = "Purge in Progress"
        stupidPop.labelText = "Purging in Progress.  Please wait."
        stupidPop.messageButton.disabled = True
        stupidPop.buttonText = "Continue"
        stupidPop.open()

        purgeOunces = .125

        ingsToPour = {}

        for curRow in [self.row0, self.row1, self.row2]:
            for curButton in curRow.children:
                if (curButton.ing.displayNorm != self.unpairedText):
                    curIng = curButton.ing
                    curLocation = self.ingPins[curIng.location]
                    curPin = curLocation["GPIO"]

                    ingsToPour[curIng.displayNorm] = {"Time": purgeOunces * curLocation["Calibration"] * curIng.calibration, "Pin": curPin}

        t = threading.Thread(target=self.thePurge, args = [ingsToPour, stupidPop])
        t.start()


    def thePurge(self, ingsToPour, purgePopup):
    	
        pins = []
        for ing in ingsToPour.keys():
            pins.append(ingsToPour[ing]["Pin"])

        GPIO.output(self.pressurePin, 1)
        sleep(self.ullagePressTime)

        for i, pin in enumerate(ingsToPour.values()):
            GPIO.output(pin["Pin"],1)
            sleep(.75)
            GPIO.output(pin["Pin"],0)
            purgePopup.labelText = ("Purge %d of %d complete." % ((i + 1), len(ingsToPour)))


        for pin in ingsToPour.values():
            GPIO.output(pin["Pin"],0)

        GPIO.output(self.pressurePin, 0)

        purgePopup.messageButton.disabled = False



class BottleServiceApp(App):

    BS = None
    ingredientFile = None
    drinkFile = None
    time = NumericProperty(0)
    settings = {}
    progressValue = NumericProperty(0)

    def build(self):

        Clock.schedule_interval(self._update_clock, 1 / 60.)

        ingPins = {}
        with open("calibrationPairing.csv") as f:
            reader = csv.reader(f)
            items = []
            for item in reader:
                ingPins[int(item[0])] = {'GPIO': int(item[1]), 'Calibration': float(item[2])} 
        

        ingredientFile = "ingredients.csv"
        self.ingredientFile = ingredientFile
        ingredientList = {}
        with open(ingredientFile) as f:
            reader = csv.reader(f)
            for ing in reader:
                newIng = Ingredient(ing[0].rstrip(), brand = ing[1], location = int(ing[2]), ingType = ing[3], manual = int(ing[4]), inStock = int(ing[5]), calibration = float(ing[6]))
                ingredientList[newIng.displayNorm] = newIng 

        drinkFile = "drinks.csv"
        self.drinkFile = drinkFile
        drinkList = {}
        with open(drinkFile) as f:
            reader = csv.reader(f)
            for drink in reader:
            	if (len(drink) > 0):
	                drinkIngs = {}
	                for trip in range(3,len(drink)-1, 2):
	                    drinkIngs[drink[trip]] = {"Amount":float(drink[trip + 1])}
	                drinkList[drink[0]] = Drink(drink[0], glassware = drink[1], prepMethod = drink[2], ingredients = drinkIngs)

        settings = [{"File": "glassware.csv", "List":[]}, {"File": "types.csv", "List":[]}, {"File": "prepMethods.csv", "List":[]}]
        for sett in settings:    
            with open(sett["File"]) as f:
                reader = csv.reader(f)
                for item in reader:
                    sett["List"].append(item[0]) 

        BS = BottleService()

        BS.ingPins = ingPins


        GPIO.setmode(GPIO.BCM)

        pressurePin = 26

        ullagePressTime = 1.

        GPIO.setup(pressurePin, GPIO.OUT, initial=0)

        for pin in ingPins.values():
		    GPIO.setup(pin['GPIO'], GPIO.OUT, initial=0)


        with open("generalSettings.csv") as f:
            reader = csv.reader(f)
            items = []
            for i, item in enumerate(reader):
                items.append(item[0])    


        BS.pressurePin = pressurePin
        BS.ullagePressTime = ullagePressTime            
        BS.robotName.text = items[0]
        BS.ounceSetting = float(items[1])
        BS.strengthSetting = float(items[2])
        BS.maxAmtInput.text = str(float(items[3]))
        BS.shotInput.text = str(float(items[4]))
        BS.displayToggle.active = bool(float(items[5]))


        BS.ingredientList = ingredientList

        BS.drinkList = drinkList

        for ing in ingredientList.values():
            if (ing.ingType != ""):
                settings[1]["List"].append(ing.ingType)

        settings[1]["List"] = list(set(settings[1]["List"]))

        BS.glassList = settings[0]["List"]
        BS.typeList = settings[1]["List"]
        BS.prepList = settings[2]["List"]

        BS.glassList.sort()
        BS.typeList.sort()
        BS.prepList.sort()

        BS.populate()

        self.BS = BS

        return BS

    def save(self):
        with open(self.ingredientFile, "w") as f:
            writer = csv.writer(f, delimiter = ",")
            for ing in self.BS.ingredientList.values():
                writer.writerow([ing.name, ing.brand, str(ing.location), ing.ingType, ing.manual, ing.inStock, ing.calibration])

        with open(self.drinkFile, "w") as f:
            writer = csv.writer(f, delimiter=",")
            for drink in self.BS.drinkList.values():
                indIngs = [drink.name]
                indIngs.append(drink.glassware)
                indIngs.append(drink.prepMethod)
                for ing in drink.ingredients.keys():
                    indIngs.append(ing)
                    indIngs.append(str(drink.ingredients[ing]["Amount"]))                    
                writer.writerow(indIngs)

        settings = [{"File": "glassware.csv", "List":[]}, {"File": "types.csv", "List":[]}, {"File": "prepMethods.csv", "List":[]}]

        settings[0]["List"] = self.BS.glassList
        settings[1]["List"] = self.BS.typeList
        settings[2]["List"] = self.BS.prepList

        for sett in settings:
            with open(sett["File"], "w") as f:
                writer = csv.writer(f, delimiter=",")
                for item in sett["List"]:
                    if item != "All":                   
                        writer.writerow([item])

        with open("generalSettings.csv", "w") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow([self.BS.robotName.text])        
            writer.writerow([self.BS.ounceInput.text])        
            writer.writerow([self.BS.strengthInput.text])        
            writer.writerow([self.BS.maxAmtInput.text])        
            writer.writerow([self.BS.shotInput.text])        
            writer.writerow([int(self.BS.displayToggle.active)])  



        with open("calibrationPairing.csv", "w") as f:
			writer = csv.writer(f, delimiter=",")        	
			for ind in self.BS.ingPins.keys():
				writeRow = [str(ind), str(self.BS.ingPins[ind]['GPIO']), str(self.BS.ingPins[ind]['Calibration'])]
				writer.writerow(writeRow)
      


    def _update_clock(self, dt):
        self.time = time()




if __name__ == "__main__":

    try:
        BS = BottleServiceApp()
        BS.run()    
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
