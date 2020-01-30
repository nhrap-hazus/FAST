from tkinter import *
from tkinter import filedialog
import pre_process,os, csv
from os import listdir
from os.path import isfile, join

dir = os.getcwd()
dir = os.path.dirname(dir)
hazardTypes = {'Riverine':'HazardR','CoastalV':'HazardCV','CoastalA':'HazardCA'}
fields = {'OCC':'Occupancy*','NumStories':'NumStories*','FoundationType':'Foundation Type*','SOID':'SpecificOcc_ID','BDDF_ID':'BuildingDDF','CDDF_ID':'ContentDDF','IDDF_ID':'InventoryDDF','HazardType':'Hazard-Type*'}# Fields for custom inpu
defaultFields = {'OCC':['Occupancy','Occ'], \
				 'NumStories':['NumStories', 'NumberStories','Num_Stories','Number_Stories'], \
				 'FoundationType':['FoundationType','Foundation Type','Foundation_Type'], \
				 'SOID':['SpecificOcc_ID','SOID'] , \
				 'BDDF_ID':['BuildingDDF','BDDF_ID','BldgDamageFnID'], \
				 'CDDF_ID':['ContentDDF','CDDF_ID','ContDamageFnId'], \
				 'IDDF_ID':['InventoryDDF','IDDF_ID','InvDamageFnId']}

def runHazus():
     entries = []
     # print(fields)
     entries.extend(root.fields.values())
     
     # print(entries)
     haz = pre_process.process(root.filename, entries)# Run the Hazus script with input from user using the GUI

     print('Pre-Process RUN',haz,entries)
     if haz[0]: popupmsg(str(haz[1][0])+' records sucessfully processed of ' + str(haz[1][1]) + ' records total.\n' \
         +str(haz[2][1])+' Building DDFs assigned.\n' \
         +str(haz[2][2])+' Content DDFs assigned.\n' \
         +str(haz[2][3])+' Inventory DDFs assigned.\n' \
         +str(haz[4][1])+' Building DDFs checked and '+str(haz[3][1])+' found valid.\n' \
         +str(haz[4][2])+' Content DDFs checked and '+str(haz[3][2])+' found valid.\n' \
         +str(haz[4][3])+' Inventory DDFs checked and '+str(haz[3][3])+' found valid.\n' \
         +'File saved to: ' + root.filename)

def browse_button():
     #UKS - made changes to open the File open dialog to the UDF folder where the input files are placed
     root.filename = filedialog.askopenfilename(initialdir = os.getcwd() + "../../UDF",title = "Select file",filetypes = (("csv files","*.csv"),("all files","*.*")))# Gets input csv file from user
     #root.filename = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("csv files","*.csv"),("all files","*.*")))# Gets input csv file from user
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
        lab = Label(row, width=22, text=field+": ", anchor='w')
             
        if field == 'Hazard-Type*':
             ent = Listbox(row,exportselection=0)
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
         if field != 'Hazard-Type*':# Not needed for raster input box
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
         
         else: root.fields[key] = hazardTypes[ents['Hazard-Type*'].get(ents['Hazard-Type*'].curselection())]
         
    if False in root.valid.values(): b1.config(fg='grey',command='')
    else: b1.config(fg='black', command=runHazus)
    root.after(100, checkform)#Recheck fields every 0.1 second

def popupmsg(msg):
    popup = Tk()
    popup.wm_title("FAST - Pre-Processing Complete...")
    label = Label(popup, text=msg)
    label.pack(side=LEFT)
    B1 = Button(popup, text="Okay", command = popup.destroy)
    B1.pack(side=BOTTOM, padx=5, pady=5)
    popup.mainloop()
                  
if __name__ == '__main__':
    root = Tk()
    root.csvFields = []# Input csv file fields
    root.fields = {key:''for key, value in fields.items()}
    root.valid = {}
    #UKS - Modified Title
    root.title("FAST - Pre-Processing....")
    
    ents = makeform(root, fields)
    lab = Label(root, text="* indicates required field.")
    lab.pack()
    lab = Label(root, text="Red fields are required and must be mapped.")
    lab.pack()
    lab = Label(root, text="Yellow fields have not been mapped, but are not required.")
    lab.pack()
    lab = Label(root, text="Green fields have been mapped successfully.")
    lab.pack()
    b1 = Button(root, text='Execute', command=runHazus)# Run button to start processing
    b1.pack(side=LEFT, padx=5, pady=5)
    b2 = Button(root, text="Browse to Inventory Input (.csv)", command=browse_button)# Browse for input csv file
    b2.pack(side=LEFT, padx=5, pady=5)
    b3 = Button(root, text='Quit', command=root.destroy)
    b3.pack(side=LEFT, padx=5, pady=5)
    root.after(100, checkform)# Recheck fields every 0.1 second
    root.mainloop()