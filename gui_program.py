print('Starting FAST...')
from tkinter import *
from tkinter import filedialog
import os, csv
#import matplotlib.pyplot as plt
#import pandas as pd
from os import listdir
from os.path import isfile, join
from hazpy.flood import UDF
import ctypes


dir = os.getcwd()
# print(dir)
if (dir.find('Python_env')!= -1):
     dir = os.path.dirname(dir)
# print(dir)
cwd = os.path.join(dir,'rasters')# Default raster directory
#cwd = 'C:\\_Repositories\\FAST\\rasters'
hazardTypes = {'Riverine':'HazardRiverine','CoastalV':'V','CoastalA':'CAE'}
rasters = [f for f in listdir(cwd) if isfile(join(cwd, f)) and f.endswith(('.tif','.tiff','.nc'))] #Search rasters folder for all .tif files and make a listprint('Rasters selection ',rasters)
#hazardTypes = {'Riverine':'HazardR','CoastalA':'HazardCA','CoastalB':'HazardCV'}
#fields = ['Occupancy*','NumStories*','SpecificOcc_ID','BuildingDDF','ContentDDF','InventoryDDF','Hazard-Type*']# Fields for custom input
fields = {'UserDefinedFltyId':'User Defined Flty Id*',
             'OCC':'Occupancy Class*',
             'Cost':'Building Cost*',
             'Area':'Building Area*',
             'NumStories':'Number of Stories*',
             'FoundationType':'Foundation Type*',
             'FirstFloorHt':'First Floor Height*',
             'ContentCost':'Content Cost',
             'BDDF_ID':'Building DDF',
             'CDDF_ID':'Content DDF',
             'IDDF_ID':'Inventory DDF',
             'InvCost':'Inventory Cost',
             'SOID':'Specific Occupancy ID',
             'Latitude':'Latitude*',
             'Longitude':'Longitude*',
             'flC':'Coastal Flooding attribute (flC)*',
             'raster':'Depth Grid (ft)**'}

#fields = {'OCC':'Occupancy*','NumStories':'NumStories*','SOID':'SpecificOcc_ID','BDDF_ID':'BuildingDDF','CDDF_ID':'ContentDDF','IDDF_ID':'InventoryDDF','raster':'Depth Grid (ft)*'}# Fields for custom inpu
#CBH - changed corresponding cost fields 8/28/19
defaultFields = {'OCC':['Occupancy','Occ'],
                      'NumStories':['NumStories','NumberStories','Num_Stories','Number_Stories'],
                      'SOID':['SpecificOcc_ID','SOID'],
                      'BDDF_ID':['BuildingDDF','BDDF_ID','BldgDamageFnID'],
                      'CDDF_ID':['ContentDDF','CDDF_ID','ContDamageFnId'],
                      'IDDF_ID':['InventoryDDF','IDDF_ID','InvDamageFnId'],
                      'InvCost':['InvCost','invcost'],
                      'UserDefinedFltyId':['UserDefinedFltyId','userdefinedfltyid','FltyId','fltyid','FacilityId','facilityid','Flty_Id','OJECTID','objectid','ObjectId','ID','Id','id'],
                      'Cost':['Cost','COST','cost','BuildingValue'],
                      'ContentCost':['ContentCost','CONTENTCOST','contentcost','Content_Cost','content_cost','Content_cost','ContentValue'],
                      'Area':['Area','area','AREA'],
                      'FoundationType':['FoundationType','Foundation_Type'],
                      'FirstFloorHt':['FirstFloorHt'],
                      'Latitude':['Latitude','latitude','LATITUDE',],
                      'Longitude':['Longitude','longitude','LONGITUDE']}
#defaultFields.update('UserDefinedFltyId' = "")
#print (defaultFields['UserDefinedFltyId'])                     


def runHazus():
     entries = []
     # print(fields)
     entries.extend(root.fields.values())
     #entries.append(ents['Hazard-Type*'].get(ents['Hazard-Type*'].curselection()))
     """
     for num, ent in enumerate(ents):# Construct a list for field names and their values for field mapping 
          if fields[num] == 'Hazard-Type*':
                entries.append([fields[num],ents[fields[num]].get(ents[fields[num]].curselection())])
          #else:
                #entries.append([fields[num],ents[fields[num]].get()])
     """
     # print(entries)
     # print(root.filename)
     #UKS 1/21/2020 - RTC CR 34227 
     runUDF = UDF()
     haz = runUDF.local(root.filename, entries)# Run the Hazus script with input from user using the GUI
     #haz = hazus.local(root.filename, entries)# Run the Hazus script with input from user using the GUI
     print('Run Hazus',haz,entries)
     
     if haz[0]:
          popupmsg(haz[1])
     else:
          popupmsg('Processing Failed. See log for details.')

def browse_button():
     #UKS - File open dialog changes
     initialdir = os.getcwd()
     if (initialdir.find('Python_env')!= -1):
          initialdir = os.path.dirname(initialdir)    
     root.filename = filedialog.askopenfilename(initialdir = os.path.join(initialdir ,'UDF'),title = "Select file",filetypes = (("csv files","*.csv"),("all files","*.*")))# Gets input csv file from user
     # Gets field names from input csv file and makes a list
     if root.filename != '':
         with open(root.filename, "r+") as f:
              reader = csv.reader(f)
              root.csvFields = next(reader)
         print(root.filename,root.csvFields)

def makeform(root, fields):# Assemble and format the fields to map from the list of fields
    entries = {}
    
    for field in fields.values():# Make entry box for each field
        row = Frame(root)
        lab = Label(row, width=30, text=field+": ", anchor='w')
             
        if field == fields['raster']: #'Depth Grid (ft)**': #UKS - modified to access the fields dictionary
             ent = Listbox(row, selectmode=EXTENDED, exportselection=0, height = 3)
             for num, raster in enumerate(rasters): ent.insert(num, raster)
             ent.selection_set(0)
             
        elif field == fields['flC']: #'Coastal Flooding attribute (flC)*':
             ent = Listbox(row,exportselection=0, height = 3)
             for num, hazardType in enumerate(hazardTypes.keys()): ent.insert(num, hazardType)
             ent.selection_set(0)

     
        else:
             ent = Entry(row)
             
        row.pack(side=TOP, fill=X, padx=5, pady=5)
        lab.pack(side=LEFT)
        ent.pack(side=RIGHT, expand=YES, fill=X)
        entries[field] = ent  
    return entries

def checkform():# Check validity of form entries
    root.fields = {key:''for key, value in fields.items()}
    for key, field in fields.items():
         #if field != 'Depth Grid (ft)**' and field != 'Coastal Flooding attribute (flC)*':# Not needed for raster input box
         if field != fields['raster'] and field != fields['flC']:# Not needed for raster input box
              color = "yellow" if '*' not in field else "red"
              ent = ents[field]
              value = ent.get()
              if '*' in field: root.valid[field] = False
              if len(root.csvFields) == 0:
                    color = None# If no input file is selected there is no coloring.
              elif value != '':
                    if value in root.csvFields:
                         root.fields[key] = value
                         color = "green"
                         if '*' in field: root.valid[field] = True
              else:
                    for defaultField in defaultFields[key]:
                         if defaultField in root.csvFields:
                              root.fields[key] = root.csvFields[root.csvFields.index(defaultField)]
                              color = "green"
                              if '*' in field: root.valid[field] = True
                              break
              ent.config(background=color)
              
         #elif field == 'Coastal Flooding attribute (flC)*': root.fields[key] = hazardTypes[ents[field].get(ents[field].curselection())]   
         elif field == fields['flC']: root.fields[key] = hazardTypes[ents[field].get(ents[field].curselection())]   
         
         else: root.fields[key] = [ents[field].get(index) for index in ents[field].curselection()]
         
    
    if False in root.valid.values(): b1.config(fg='grey',command='')
    else: b1.config(fg='black', command=runHazus)
    root.after(100, checkform)#Recheck fields every 0.1 second
    
def popupmsg(msg):
    popup = Tk()
    popup.wm_title("FAST - Processing Complete...")
    label = Label(popup, text=msg)
    label.pack(side="top", fill="x", pady=10)
    B1 = Button(popup, text="Okay", command = popup.destroy)
    B1.pack()
    popup.mainloop()
   
def sortandsavecsv(inputCSVName, outputCSVName, sortFieldName, sortDesc=True):
    with open(inputCSVName + '.csv', 'r', newline='') as f_input:
        csv_input = t1.DictReader(f_input)
        data = sorted(csv_input, key=lambda row:(abs(float(row[sortFieldName]))< 0,float(row[sortFieldName])), reverse=sortDesc)

    with open('test' + '_sorted.csv', 'w', newline='') as f_output:    
        csv_output = t1.DictWriter(f_output, fieldnames=csv_input.fieldnames)
        csv_output.writeheader() 
        csv_output.writerows(data)      

#def visualize():
#    df =  pd.read_csv('C:/_Hazus/June-Dec_2019/OpenHazus_POC_demo/OpenHazus_POC/UDF/Minot_HAZ_PNNL_PreProcessed_ORIG_COM6_pre_processed_PNNL_100_sorted.csv')
#    bldg_loss_data = df["BldgLossUSD"]
#    occup_data = df["Occ"]
#        #df1 =  pd.read_csv('C:\_Hazus\June-Dec_2019\OpenHazus_POC_demo\OpenHazus_POC\lookuptables\OccupancyTypes.csv')
#        #occup_data = df1["Occupancy"]

#    sums = df.groupby(df['Occ'].str[:3])["BldgLossUSD"].sum()
#        #colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#8c564b"]
#        #explode = (0.1, 0.1, 0.1, 0.1, 0.1,0.1) 
#        #explode=explode, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140
#    plt.pie(sums, startangle=140, autopct='%1.1f%%') #,explode=explode)
#    plt.title("Building Losses by Occupany type....")
#    plt.legend(sums[0],labels=sums.index, bbox_to_anchor=(1,0), loc="lower right", bbox_transform=plt.gcf().transFigure)
#    plt.show()
    
# if __name__ == '__main__':
root = Tk()
root.wm_iconbitmap('Images/Hazus.ico')
root.csvFields = []# Input csv file fields
root.fields = {key:''for key, value in fields.items()}
root.valid = {}
#UKS
root.title("FAST - Flood Assessment Structure Tool")
ents = makeform(root, fields)

# calculate x and y coordinates for the Tk root window

ws = root.winfo_screenwidth() # width of the screen
hs = root.winfo_screenheight() # height of the screen
w = ws * 0.25
h = hs * 0.87
x = (ws/2) - (w/2)
y = (hs/2) - (h/2) - 50

# set the dimensions of the screen and where it is placed
#x = 0
#y = 0
#root.geometry('+%d+%d'%(x,y))  
# root.geometry('%dx%d+%d+%d' % (w, h, x, y))

lab = Label(root, text="* indicates required field.", anchor = 'w').pack(fill='both')
lab = Label(root, text="**Press the ctrl key to process multiple depth grids.", anchor = 'w').pack(fill='both')
#lab.pack() 
lab = Label(root, text="Fields named similar to defaults are searched for.", anchor = 'w').pack(fill='both')
#lab.pack()    
lab = Label(root, text="Red fields are required and must be mapped.", anchor = 'w').pack(fill='both')
#lab.pack()
lab = Label(root, text="Green fields have been mapped successfully.", anchor = 'w').pack(fill='both')
#lab.pack()
lab = Label(root, text="Yellow fields have not been mapped, but are not required.", anchor = 'w').pack(fill='both')
#lab.pack()
b1 = Button(root, text='Execute', command=runHazus, fg = 'Grey')# Run button to start processing
b1.pack(side=LEFT, padx=5, pady=5)
b2 = Button(root, text="Browse to Inventory Input (.csv)", command=browse_button)# Browse for input csv file
b2.pack(side=LEFT, padx=5, pady=5)
b3 = Button(root, text='Quit', command=root.destroy)
b3.pack(side=LEFT, padx=5, pady=5)
#b4 = Button(root, text='Visualize', command=visualize, fg = 'Grey')
#b4.pack(side=LEFT, padx=5, pady=5)


root.after(100, checkform)# Recheck fields every 0.1 second
# minimize the console window
ctypes.windll.user32.ShowWindow( ctypes.windll.kernel32.GetConsoleWindow(), 6)
root.mainloop()