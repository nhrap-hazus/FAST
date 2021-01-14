import os, csv

dir = os.getcwd()
print(dir)
if (dir.find('Python_env')!= -1):
     dir = os.path.dirname(dir)
def process(input,fmap):
    try:
        output = input.split('.')[0]+'_pre_processed.csv'
        print(output)
        OCC,NumStories,foundationtype,SOID,BDDF_ID,CDDF_ID,IDDF_ID,HazardType = fmap
        SOID = SOID if SOID != '' else 'SOID'
        BDDF_ID = BDDF_ID if BDDF_ID != '' else 'BDDF_ID'
        CDDF_ID = CDDF_ID if CDDF_ID != '' else 'CDDF_ID'
        IDDF_ID = IDDF_ID if IDDF_ID != '' else 'IDDF_ID'
        
        LUT_Dir = os.path.join(dir,'lookuptables')
        
        DDFAssign = ['SOoccupId_Occ_Xref','flBldgStructDmgFinal','flBldgContDmgFinal','flBldgInvDmgFinal','OccupancyTypes']
        DDFTables = {}
        for DDF in DDFAssign:
            with open(os.path.join(LUT_Dir,DDF+'.csv'), newline='') as csvfile:
                file = csv.DictReader(csvfile)
                DDFTable = [row for row in file]
                DDFTables[DDF] = DDFTable
                
        countie = [0,0,0,0]
        countie2 = [0,0,0,0]
        countie3 = [0,0,0,0]
        counter = 0
        counter2 = 0
        DDFDefault = ['flBldgStructDmgFn_DDF','flBldgContDmgFn_DDF','flBldgInvDmgFn_DDF']
        DDFDefaultTables = {}
        for DDF in DDFDefault:
            with open(os.path.join(LUT_Dir,DDF+'.csv'), newline='') as csvfile:
                file = csv.DictReader(csvfile)
                DDFDefaultTable = [list(row.values())[0] for row in file]
                DDFDefaultTables[DDF] = DDFDefaultTable

        with open(input, "r+") as f:
            reader = csv.reader(f)
            field_names = next(reader)

        with open(input, newline='') as csvfile:
            field_names = field_names + [field for field in [SOID,BDDF_ID,CDDF_ID,IDDF_ID] if field not in field_names]
            field_names.append('DDF_Validity')
            #print(field_names)
            writer = csv.DictWriter(open(output, 'w'), delimiter=',', lineterminator='\n', fieldnames = field_names)
            file = csv.DictReader(csvfile)
            for row in file:
                try:
                    value = 0
                    basement = 1 if int(row[foundationtype]) == 4 else 0
                    if row.get(SOID) == None and SOID != '':
                        
                        #Loop to generate the SOCID
                        for line in DDFTables['SOoccupId_Occ_Xref']:
                            compare = line['NumStoriesInt']                            
                            if len(compare) > 1 and int(line['Basement']) == basement and line['Occupancy'].strip() == row[OCC]:
                                if '-' in compare:
                                    if int(compare[0]) <= int(row[NumStories]) <= int(compare[-1]):
                                        value = line['SOccupId'].strip()
                                        row[SOID] = value
                                        countie[0] = countie[0] + 1
                                        row['DDF_Validity'] = None                                        
                                        break
                                elif '>' in compare:
                                    if int(row[NumStories]) > int(compare[1]):
                                        value = line['SOccupId'].strip()
                                        row[SOID] = value
                                        countie[0] = countie[0] + 1
                                        row['DDF_Validity'] = None                                      
                                        break
                                elif '<' in compare:
                                    if int(row[NumStories]) < int(compare[1]):
                                        value = line['SOccupId'].strip()
                                        row[SOID] = value
                                        countie[0] = countie[0] + 1
                                        row['DDF_Validity'] = None
                                        break                                       
                                elif 'any' in compare:
#                                    if int(row[NumStories]) < int(compare[1]):
                                    value = line['SOccupId'].strip()
                                    row[SOID] = value
                                    countie[0] = countie[0] + 1
                                    row['DDF_Validity'] = None
                                    break
                            elif len(compare) == 1 and line['Occupancy'].strip() == row[OCC] and int(compare) == int(row[NumStories]) and int(line['Basement']) == basement:
                                value = line['SOccupId'].strip()
                                row[SOID] = value
                                countie[0] = countie[0] + 1
                                row['DDF_Validity'] = None                            
                                break
                    #BUILDING DDF                        
                    if row.get(BDDF_ID) == None and BDDF_ID != '':
                        for line in DDFTables['flBldgStructDmgFinal']:
                            if line['SOccupId'].strip() == value and int(line[HazardType]) == 1:
                                row[BDDF_ID] = line['BldgDmgFnId']
                                countie[1] = countie[1] + 1
                                row['DDF_Validity'] = None
                                break
                            
                    elif row.get(BDDF_ID) != None and BDDF_ID != '':                        
                        countie3[1] += 1                    
                        default = row[BDDF_ID].strip()                       
                        row[BDDF_ID] = None
                        if default in DDFDefaultTables['flBldgStructDmgFn_DDF']:
                            row[BDDF_ID] = default
                            countie2[1] = countie2[1] + 1
                            row['DDF_Validity'] = None
                    
                    #CONTENT DDF                     
                    if row.get(CDDF_ID) == None and CDDF_ID != '':    
                        for line in DDFTables['flBldgContDmgFinal']:
                            if line['SOccupId'].strip() == value and int(line[HazardType]) == 1:
                                #UKS 04/08/2020 - fixed BDDF_ID to CDDF_ID as this is for content DDF
                                #Due to this the content DDF field was being wiped out and only building DDF field was being written
                                row[CDDF_ID] = line['ContDmgFnId']
                                countie[2] = countie[2] + 1
                                row['DDF_Validity'] = None
                                break
                            
                    elif row.get(CDDF_ID) != None and CDDF_ID != '':
                        countie3[2] += 1
                        default = row[CDDF_ID].strip()
                        row[CDDF_ID] = None
                        if default in DDFDefaultTables['flBldgContDmgFn_DDF']:
                            row[CDDF_ID] = default
                            countie2[1] = countie2[1] + 1
                            row['DDF_Validity'] = None
                    
                    #INVENTORY DDF         
                    if row.get(IDDF_ID) == None and IDDF_ID != '':   
                        for line in DDFTables['flBldgInvDmgFinal']:
                            if line['SOccupId'].strip() == value and int(line[HazardType]) == 1:
                                #UKS 04/08/2020 - fixed BDDF_ID to IDDF_ID as this is for inventory DDF
                                row[IDDF_ID] = line['InvDmgFnId']
                                countie[3] = countie[3] + 1
                                row['DDF_Validity'] = None
                                break
                            
                    elif row.get(IDDF_ID) != None and IDDF_ID != '':
                        countie3[3] += 1
                        default = row[IDDF_ID].strip()
                        row[IDDF_ID] = None
                        if default in DDFDefaultTables['flBldgInvDmgFn_DDF']:
                            row[IDDF_ID] = default
                            countie2[1] = countie2[1] + 1
                            row['DDF_Validity'] = None
                        
                        
                    counter += 1
                    counter2 += 1
                    if counter % 10000 == 0:
                        print( "   processing record " + str(counter),  ' countie = ', countie, ' countie2 = ', countie2)
                        
                    if counter == 1:
                        writer.writeheader()
                        writer.writerow(row)
                        continue
                    writer.writerow(row)
                except Exception as e:
                    writer.writerow(row)
                    counter2 += 1
                    print(e)
                    continue
            print("Total records processed: " + str(counter),  ' countie = ', countie, ' countie2 = ', countie2)
            return(True, [counter,counter2], countie, countie2, countie3)
    except Exception as e:
        print(e)
        return(False, counter, countie, countie2)