from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
import pandas as pd
import regex as re
from textdistance import jaccard as jaccard
import math

pd.set_option('display.max_rows', None) #sets all rows to visible
pd.set_option('display.max_columns', None) #same with the columns

Calculated_Val = 0 # is the int value of the nutritional val
quantity = False #is ingred listed in quanity?
Unit_Found = 0 #the unit found
Amount = 0 #stores amount of each ingred

DB_Ingred_Row_Num = ''

my_url = 'https://www.allrecipes.com/personal-recipe/64771119/asd/' #url used for calculation
#my_url = input()

uClient = uReq(my_url) #stores url
page_html = uClient.read() #stores HTML
uClient.close() #closes web connection

page_soup = soup(page_html, "html.parser") #defines what is done with HTML

dfIngred = pd.DataFrame(columns=['ingredients']) #creates pandas df for ingreds
dfDataBase = pd.read_csv('Test_Ingred_Database.csv') #stores databse in pandas df
dfNutr_Vals = pd.DataFrame(columns=['Food Names', 'Calories', 'Protein', 'Fat', 'Carbohydrates', 'Sugar', 'Fiber', 'Sodium', 'Cholesterol'])
#dfUser_Input = pd.DataFrame(columns=['UserInput'])
dfUser_Input = pd.read_csv('UserInput.csv')

for ingredient in page_soup.find_all('span', class_ = 'recipe-ingred_txt added'): #while this exists, run through website
    ingredient_refined = ingredient.get_text().lower() #store value found
    ingredient_refined = re.sub(r'[^\w\d/\s]','',ingredient_refined) #refine ingredient found except for '/' which indicate a fraction

    dfIngred = dfIngred.append({'ingredients': ingredient_refined}, ignore_index=True) #adds string into 'dfingred' ~df

Row_Count_Ingred_List = dfIngred.shape[0]
Row_Count_Ingred_Database = dfDataBase.shape[0]

#functions

def Jaccard_Index(Cell1, Cell2):
    Cell1 = Cell1.lower().split() #removes punctuation and spilts string into list of words
    Cell2 = Cell2.lower().split() #removes punctuation and spilts string into list of words

    return jaccard(Cell1, Cell2) #calculates jaccard index of two strings

def Find_Amount(): #used to find unit of measure and amount
    global Cell1
    global Unit_Found
    global Amount
    global quantity
    found = False #Has unit been found?
    quantity = False #resets to zero for new ingred
    Units_Of_Measure = ['cup', 'tablespoon', 'teaspoon', 'ounce', 'pound', 'pinch'] #these are so far the only units of measure I have identified
    Cell1_Split = Cell1.lower().split() # formats cell1

    for Cell_Wrd_Num in range(len(Cell1_Split)):
        if found == True: #if ingredient has been found then break
            break
        else:
            pass
        for Unit_Num in range(len(Units_Of_Measure)):
            if found == True:
                break
            elif Cell1_Split[Cell_Wrd_Num].find(Units_Of_Measure[Unit_Num]) != -1: #If unit being tested is in string
                Unit_Found = Units_Of_Measure[Unit_Num]
                found = True #mark that unit has been found
                quantity = False
                Amount = Cell1_Split[Cell_Wrd_Num - 1] #stores the amount of each unit
                if Amount.find('/') != -1: #if amount is listed as fraction
                    Amount_Split = [char for char in Amount] #splits fraction into individual numbers
                    Amount = int(Amount_Split[0]) / int(Amount_Split[2]) #converts the fraction to a decimal value
            else:
                quantity = True #sets quanity to true, possibly just for now
                Amount = int(Cell1_Split[0]) #finds the amount

Nutritional_Vals = ['Calories', 'Protein', 'Fat', 'Carbohydrates', 'Sugar', 'Fiber', 'Sodium', 'Cholesterol'] #these are te nutritional values that are in the database

def Calc_Vals_A(Val_Name):
    global DB_Ingred_Row_Num
    global Unit_Found
    global Amount
    global dfDataBase
    global dfIngred
    global Calculated_Val
    DB_Val = float(dfDataBase[Val_Name].iloc[DB_Ingred_Row_Num]) #Nutri val from database
    DB_Conversion_Fact = float(dfDataBase['Conversion factor'].iloc[DB_Ingred_Row_Num]) #conversion factor from database
    #The conversion factor is what the val, listed in 100 grams, must be divided by to get a sing cup
    Amount = float(Amount)

    #This function converts the database val to the found unit of measure and then multiplies it by the amount of the ingredient
    if DB_Conversion_Fact != 0: #if there is a conversion fact in the database
        if Unit_Found == 'cup':
            Calculated_Val = DB_Val / DB_Conversion_Fact
            Calculated_Val = Calculated_Val * Amount
        elif Unit_Found == 'tablespoon':
            Calculated_Val = DB_Val / DB_Conversion_Fact
            Calculated_Val = (Calculated_Val / 16) * Amount
        elif Unit_Found == 'teaspoon':
            Calculated_Val = DB_Val / DB_Conversion_Fact
            Calculated_Val = (Calculated_Val / 48) * Amount
        elif Unit_Found == 'ounce':
            Calculated_Val = (DB_Val / 28.35) * Amount
        elif Unit_Found == 'pound':
            Calculated_Val = (DB_Val / 454) * Amount
        elif Unit_Found == 'pinch':
            Calculated_Val = (DB_Val / 2.77) * Amount
        return float(Calculated_Val)
    else:
        Calculated_Val = '0'

#function calculates vals if ingred listed in quantity
def Calc_Vals_Q(Val_Name):
    global DB_Ingred_Row_Num
    global dfDataBase
    global Calculated_Val
    global Amount
    DB_Val = float(dfDataBase[Val_Name].iloc[DB_Ingred_Row_Num]) #Database nutri val
    DB_Conversion_Fact = float(dfDataBase['Average weight '].iloc[DB_Ingred_Row_Num]) #The average weight of the ingred listed in quantity
    Amount = float(Amount)

    Calculated_Val = ((DB_Val / 100) * (DB_Conversion_Fact * Amount)) #Calculates nutri val
    return float(Calculated_Val)

#main loop

for Ingred_Num in range(Row_Count_Ingred_List):
    Cell1 = dfIngred['ingredients'].iloc[Ingred_Num] #cell1 is the ingred
    Max_Index = 0
    print('_______________')
    dfNutr_Vals.at[Ingred_Num, 'Food Names'] = Cell1
    for Jac_Test in range(Row_Count_Ingred_Database):
        Cell2 = dfDataBase['Food Name'].iloc[Jac_Test]

        if Jaccard_Index(Cell1, Cell2) > Max_Index:
            Max_Index = Jaccard_Index(Cell1, Cell2)
            DB_Ingred_Row_Num = Jac_Test
    Find_Amount()
    if DB_Ingred_Row_Num != 'N/A':
        print('list ingred',Ingred_Num + 1,':', Cell1, '-- db ingred found:', dfDataBase['Food Name'].iloc[DB_Ingred_Row_Num])
        if quantity == False:
            print(Amount, Unit_Found)
            for Nutritional_Vals_Num in range(len(Nutritional_Vals)):
                x = Calc_Vals_A(Nutritional_Vals[Nutritional_Vals_Num])
                if x != 0:
                    dfNutr_Vals.at[Ingred_Num, Nutritional_Vals[Nutritional_Vals_Num]] = x
                elif x == 0:
                    dfNutr_Vals.at[Ingred_Num, Nutritional_Vals[Nutritional_Vals_Num]] = 0
            #dfNutr_Vals = dfNutr_Vals.append({'Food Names': dfDataBase['Food Name'].iloc[DB_Ingred_Row_Num] }, ignore_index=True)
        elif quantity == True:
            print(Amount,'quantity')
            for Nutritional_Vals_Num in range(len(Nutritional_Vals)):
                x = Calc_Vals_Q(Nutritional_Vals[Nutritional_Vals_Num])
                if x != 0:
                    dfNutr_Vals.at[Ingred_Num, Nutritional_Vals[Nutritional_Vals_Num]] = x
                elif x == 0:
                    dfNutr_Vals.at[Ingred_Num, Nutritional_Vals[Nutritional_Vals_Num]] = 0

            #for Nutritional_Vals_Num in range(len(Nutritional_Vals)):
                #dfNutr_Vals.at[Ingred_Num, Nutritional_Vals[Nutritional_Vals_Num]] = 0

    else:
        dfNutr_Vals.at[Ingred_Num, Nutritional_Vals[Nutritional_Vals_Num]] = 0
        print(Cell1, 'not found')

dfNutr_Vals = dfNutr_Vals.append(dfNutr_Vals.sum(axis = 0, skipna = True), ignore_index = True)
dfNutr_Vals.at[Row_Count_Ingred_List, 'Food Names'] = 'Totals'
print('_______________')
print(dfNutr_Vals)

#'Calories', 'Protein', 'Fat', 'Carbohydrates', 'Sugar', 'Fiber', 'Sodium', 'Cholesterol'
Too_Much = []
Too_Much2 = []

x = 0

for x in range(len(Nutritional_Vals)):
    UI = dfUser_Input['UserInput'].iloc[x]
    UL = dfNutr_Vals[Nutritional_Vals[x]].iloc[Row_Count_Ingred_List]
    if UI < UL:
        comp_val = 100 - ((UI/UL) * 100)
        Too_Much.append(comp_val)
        Too_Much2.append(x)
    else:
        pass
x = 0

i = 0
Max_Disp = Too_Much[0]
Disp_Num = 0

for i in range(len(Too_Much)):
    Test_Disp = Too_Much[i]
    if Test_Disp > Max_Disp:
        Max_Disp = Test_Disp
        Disp_Num = int(Too_Much2[i])

Max_Nut_Val = dfNutr_Vals[Nutritional_Vals[Too_Much2[Disp_Num]]].iloc[Row_Count_Ingred_List]
Max_Ui = dfUser_Input['UserInput'].iloc[Too_Much2[Disp_Num]]

print('_______________')
Portion_Size = Max_Nut_Val / Max_Ui
print(Portion_Size, 'safe portions')
print('_______________')

'''
for d in range(len(Nutritional_Vals)):
    x = dfNutr_Vals['val': Nutritional_Vals[d]].iloc[Row_Count_Ingred_List - 1]
    dfNutr_Vals.at[Row_Count_Ingred_List - 1, Nutritional_Vals[d]] =  x / Portion_Size
'''















#
