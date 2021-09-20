"""
    Hazus - Flood UDF
    ~~~~~

    FEMA developed module for analzying risk and loss from floods.

    :copyright: © 2019 by FEMA's Natural Hazards and Risk Assesment Program.
    :license: cc, see LICENSE for more details.
    :author(FAST Merge): Ujvala K Sharma (UKS) 
    :date:   1/14/2020
    :Task:   RTC CR 34227

    :Update: 4/13/2020
    :Task:   RTC CR 35520 - FAST Custom DDFs

    :Update: 6/11/2020
    :Bugfix: - https://github.com/nhrap-hazus/FAST/issues/6
    
"""

import logging
import os, csv, sys, time, math, datetime, math, subprocess, numpy as np, utm
from osgeo import gdal, osr, gdal_array, gdalconst
from osgeo.gdalconst import *

class UDF():
    def __init__(self):
        pass
    
    # This test allows the script to be used from the operating
    # system command prompt (stand-alone), in a Python IDE, 
    # as a geoprocessing script tool, or as a module imported in
    # another script
    @staticmethod
    def local(spreadsheet, fmap):
        raster = fmap[-1]#[-1]
        fmap = fmap[:-1]
        cwd = os.getcwd()
        if (cwd.find('Python_env')!= -1):
            cwd = os.path.dirname(cwd)
        outDir = os.path.dirname(spreadsheet)
        argv = (spreadsheet, os.path.join(cwd, r"lookuptables"), outDir, [os.path.join(cwd, 'rasters', grid) for grid in raster], "False", fmap)        
        objUDF = UDF()
        return objUDF.flood_damage(*argv)
    
    @staticmethod
    def flood_damage(UDFOrig, LUT_Dir, ResultsDir, DepthGrids, QC_Warning, fmap):
        # UDFOrig = USer-supplied UDF input file. Full pathname required
        # LUT_Dir = folder name where the Lookup table libraries reside
        # ResultsDir = Where the output file geodatabase will be created. Folder (dir) must exist, else fail
        # DepthGrids = one or more flood depth grids
        # QC_Warning = Boolean, report on informative inconsistency observations if selected, otherwise suppress them  
        gdal.SetCacheMax(2**30*5)
        logger = logging.getLogger('FAST')
        logger.setLevel(logging.INFO)
        cdir = os.getcwd()
        if (cdir.find('Python_env')!= -1):
            cdir = os.path.dirname(cdir)

        logDirName = "Log"
        logDir = os.path.join(cdir, logDirName)

        handler = logging.FileHandler(logDir + '\\' + 'app.log')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        log = []#CBH
        logger.info('\n')
        logger.info('Calculation FL Building & Content Losses...')
        counter = 0
        try:
            # Measure script performance
            start_time = time.time()
            QC_Warning = QC_Warning.lower() == 'true'

            #Get field names
            with open(UDFOrig, "r+") as f:
                reader = csv.reader(f)
                field_names = next(reader)
                #f.close()
                
                #########################################################################################################
                # UDF Input Attributes. The following are standard Hazus names/capitalizations.
                #########################################################################################################
                UserDefinedFltyId, OccupancyClass, Cost, Area, NumStories, FoundationType, FirstFloorHt, ContentCost, BldgDamageFnID, ContDamageFnId, InvDamageFnId, InvCost, SOI, latitude, longitude, flC = fmap#[map for map in fmap if map != '' else]#[value if value != '' and any(value in s for s in field_names) == True else field for field, value in fmap]
                
                # If your UDF Naming Convention differs from the Hazus namings, 
                # you can specify your names here, and override the assignments above
                # Example: (of course, uncomment this)
                # UserDefinedFltyId = "UDF_ID"

                # Note that this script has no use for the following Hazus-MH Flood UDF variables:
                #    Name, Address, City, Statea, Zipcode, Contact, PhoneNumber, YearBuilt, BackupPower, 
                #    ShelterCapacity, Latitude, Longitude, Comment, BldgType, DesignLevel, FloodProtection

                #########################################################################################################
                #  UDF Output Attributes
                #########################################################################################################
                # Good programming practice: have these names as variables rather than hardcoded within commands
                # Most users need not change these, unless you do not like the names
                BldgDmgPct                = "BldgDmgPct"
                BldgLossUSD                = "BldgLossUSD"
                ContentCostUSD            = "ContentCostUSD"
                ContDmgPct                = "ContDmgPct"
                ContentLossUSD            = "ContentLossUSD"
                InventoryCostUSD        = "InventoryCostUSD"
                InvDmgPct                = "InvDmgPct"
                InventoryLossUSD         = "InventoryLossUSD"

                # Note there are no Hazus equivalents for the following output attributes.
                # DOGAMI believes these to be value-added, and suggests Hazus provide this information.
                # See spreadsheet accompanying the script for naming convention
                flExp         = "flExp"
                Depth_in_Struc    = "Depth_in_Struc"
                Depth_Grid    = "Depth_Grid"    # The renamed raster sample data. "RASTERVALU" is not a useful name
                SOID        = "SOID" if SOI == '' else SOI        # Specific Occupancy ID
                BDDF_ID        = "BDDF_ID" if BldgDamageFnID == '' else BldgDamageFnID
                CDDF_ID        = "CDDF_ID" if ContDamageFnId == '' else ContDamageFnId
                IDDF_ID        = "IDDF_ID" if InvDamageFnId == '' else InvDamageFnId
                DebrisID    = "DebrisID"
                Debris_Fin    = "Debris_Fin"      # Debris for Finish work
                Debris_Struc= "Debris_Struc"      # Debris from structural elements
                Debris_Found= "Debris_Found"       # Debris from foundation
                Debris_Tot    = "Debris_Tot"      # Total Debris - sum of the previous
                GridName    = "GridName"
                Restor_Days_Min    = "Restor_Days_Min" # Repair/Restoration times
                Restor_Days_Max    = "Restor_Days_Max"
                #########################################################################################################
                #  Setups for other namings.
                #########################################################################################################
                # Building, Content, Inventory DDF Lookup tables. Use these if user does not supply their own DDF_ID
                # Note that Inventory has no unique LUTs for Coastal Zones.
                # Prefix Naming Convention in this program:
                #   B   Building
                #   C   Content
                #   I   Inventory
                BR          = "Building_DDF_Riverine_LUT_Hazus4p0.csv"
                BCA         = "Building_DDF_CoastalA_LUT_Hazus4p0.csv"
                BCV         = "Building_DDF_CoastalV_LUT_Hazus4p0.csv"
                BFull    = "flBldgStructDmgFn.csv"    # Full DDF library for Building Structural damage

                CR          = "Content_DDF_Riverine_LUT_Hazus4p0.csv"
                CCA         = "Content_DDF_CoastalA_LUT_Hazus4p0.csv"
                CCV         = "Content_DDF_CoastalV_LUT_Hazus4p0.csv"
                CFull    = "flBldgContDmgFn.csv"    # Full DDF library for Building Content damage

                IR          = "Inventory_DDF_LUT_Hazus4p0.csv"
                IFull    = "flBldgInvDmgFn.csv"    # Full DDF library for Building Inventory damage
                IEconParams    = "flBldgEconParamSalesAndInv.csv"  # Needed to calculate business inventory value and loss
                DebrisX    = "flDebris_LUT.csv"    # A synthesis of [dbo].[flDebris] and information Hazus Flood Technical Manual (2011), Table 11.1
                RestFnc    = "flRsFnGBS_LUT.csv"    # A modification of [db].[flRsFnGBS] to make it compatible for lookup table purposes

                # Other Lookup tables exported from SQL database that may be of interest for Direct Economic Loss calculations.
                # The basic need DOGAMI had was to establish the building restoration times -
                # and that is fundamental information for all other direct economic loss calculations
                # DOGAMI did not calculate, for example, rental income loss.
                # You can expand the functionality, if you wish, 
                # following the methods outlined in the Hazus Flood Technical Manual (2011)
                #xx = "flBldgEconParamWageCapitalIncome.csv"
                #xx = "flBldgEconParamRental.csv"
                #xx = "flBldgEconParamRecaptureFactors.csv"
                #xx = "flBldgEconParamOwnerOccupied.csv"
                # Process some of the user input.
                UDFRoot     = os.path.basename(UDFOrig)

                #Resultsfgdb = os.path.join(ResultsDir, y)
                Resultsfgdb = ResultsDir

                # Set up the look-up tables
                BRP  = os.path.join(LUT_Dir, BR)
                BCAP = os.path.join(LUT_Dir, BCA)
                BCVP = os.path.join(LUT_Dir, BCV)
                BFP  = os.path.join(LUT_Dir, BFull)
                CRP  = os.path.join(LUT_Dir, CR)
                CCAP = os.path.join(LUT_Dir, CCA)
                CCVP = os.path.join(LUT_Dir, CCV)
                CFP  = os.path.join(LUT_Dir, CFull)
                IRP  = os.path.join(LUT_Dir, IR)
                IFP  = os.path.join(LUT_Dir, IFull)
                IEP  = os.path.join(LUT_Dir, IEconParams)
                Debris = os.path.join(LUT_Dir, DebrisX)
                Rest = os.path.join(LUT_Dir, RestFnc)

                # Process the look-up tables into a list of Dictionary elements
                # Note the standard (default) Lookup Tables were separately developed.
                # Yes, they are a subset of the full lookup table
                bddf_lut_riverine     = [row for row in csv.DictReader(open(BRP))]
                bddf_lut_coastalA     = [row for row in csv.DictReader(open(BCAP))]
                bddf_lut_coastalV     = [row for row in csv.DictReader(open(BCVP))]
                bddf_lut_full         = [row for row in csv.DictReader(open(BFP))]

                cddf_lut_riverine     = [row for row in csv.DictReader(open(CRP))]
                cddf_lut_coastalA     = [row for row in csv.DictReader(open(CCAP))]
                cddf_lut_coastalV     = [row for row in csv.DictReader(open(CCVP))]
                cddf_lut_full         = [row for row in csv.DictReader(open(CFP))]

                iddf_lut_riverine     = [row for row in csv.DictReader(open(IRP))]
                iddf_lut_full         = [row for row in csv.DictReader(open(IFP))]
                iecon_lut            = [row for row in csv.DictReader(open(IEP))]

                debris_lut            = [row for row in csv.DictReader(open(Debris))]
                rest_lut            = [row for row in csv.DictReader(open(Rest))]

                # Build up lists to use for checking legitimate user-supplied DDF_ID values
                bddf_lut_full_list = []
                cddf_lut_full_list = []
                iddf_lut_full_list = []
                for x in bddf_lut_full:
                    bddf_lut_full_list.append(x['BldgDmgFnID'])    # Yes, the capitalization is due to a quirk in the [dbo].[flBldgStructDmgFn].
                for x in cddf_lut_full:
                    cddf_lut_full_list.append(x['ContDmgFnId'])  # Yes, the case is inconsistent with Building column name. That's the way the Hazus database is.
                for x in iddf_lut_full:
                    iddf_lut_full_list.append(x['InvDmgFnId'])

                Content_x_0p5 = ['RES1', 'RES2', 'RES3A', 'RES3B', 'RES3C', 'RES3D', 'RES3E', 'RES3F', 'RES4', 'RES5', 'RES6', 'COM10']
                Content_x_1p0 = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM8', 'COM9', 'IND6', 'AGR1', 'REL1', 'GOV1', 'EDU1']
                Content_x_1p5 = ['COM6', 'COM7', 'IND1', 'IND2', 'IND3', 'IND4', 'IND5', 'GOV2', 'EDU2']

                # Default inventory DDF only defined for a subset. IF not in this set, set default Inventory Cost Basis = 0
                Inventory_List = ['COM1', 'COM2', 'IND1', 'IND2', 'IND3', 'IND4', 'IND5', 'IND6', 'AGR1']

                # Check for the presence of optional fields (Coastal Flooding, user-supplied DDFs for Building, Content, Inventory)
                #
                CoastalZoneSupplied = ubddf = ucddf = uiddf =  cdest = idest = CoastalZoneCode = uccost = uicost = 0

                xt = True if flC != '' else False
                if xt:
                    print( "Coastal Flooding attribute (flC) supplied. Will use where specified")
                    CoastalZoneSupplied = 1
                xt = True if BldgDamageFnID != '' else False
                if xt:
                    print( "User-supplied Building Depth Damage Function (BldgDamageFnID) attribute supplied. Will use where specified")
                    ubddf = 1
                xt = True if ContDamageFnId != ''  else False
                if xt:
                    print("User-supplied Content  Depth Damage Function attribute (ContDamageFnId supplied. Will use where specified")
                    ucddf = 1
                xt = True if InvDamageFnId != '' else False
                if xt:
                    print("User-supplied Inventory Depth Damage Function attribute (InvDamageFnId supplied. Will use where specified")
                    uiddf = 1
                xt = True if ContentCost != '' else False
                if xt:
                    print( "User-supplied Content Cost supplied.  Will use user supplied value where specified, else use the default")
                    uccost = 1
                xt = True if InvCost != '' else False
                if xt:
                    print("User-supplied Inventory Cost supplied.  Will use user supplied value where specified, else use the default")
                    uicost = 1
                    
                #logger.info('Custom DDF assignment based on tables...')
                requiredFields = [UserDefinedFltyId, OccupancyClass, Cost, Area, NumStories, FoundationType, FirstFloorHt, latitude, longitude]

                # Process each depth grid specified by user
                DGrids = DepthGrids#.split(';')   # Using the interactive window, it's not a list. Make it so.
                for dgp in DGrids:
                    # Set up the Results file. Extract grid to points, add needed fields, adjust for First Floor Height.
                    # Depth_in_Struc:  The adjusted flood depth
                    # flExp:   A simple 1/0 statement: is the UDF in the specified floodplain or is it not?
                    # SOID = SpecificOccupId.  A conversion of the OccupancyClass, FoundationType, and NumStories fields into a 4 to 5 character string for lookup.
                    # BDDF_ID = the particular Depth Damage Function ID used for that record
                    # BldgDmgPct = Loss Ratio for Building
                    # BldgLossUSD = Estimated Building Loss in US$  (some fraction of the user-specified Cost)
                    #
                    # Need to strip out any periods in the depth grid file name, say, "depth100.tif", as periods are COMPLETELY UNACCEPTABLE in fgdb feature class naming
                    # And if an input shapefile is specified, drop the *.shp extension. So a Texas Two Step to get a clean name
                    
                    y = os.path.split(dgp)[1]
                    x = UDFRoot.split('.')[0] + "_" + y.split('.')[0]
                    ResultsFile = os.path.join(Resultsfgdb, x)
                    gridroot = y    #  Put into an attribute in the Results file. Redundant, but handy when appending multiple results files together.

                    # Some research should go into INTERPOLATE versus NONE in the next function.
                    # A cursory peek suggested Hazus-MH Flood does 'NONE' (it had a better match).
                    # So to better match to the Hazus-MH Flood results, we (for now) choose 'NONE'.            
                    # Process each UDF record, calculating its damage based on depth and building type.
                        
                    new_fields = [Depth_Grid, Depth_in_Struc, flExp, SOID, BDDF_ID, BldgDmgPct, BldgLossUSD, ContentCostUSD, CDDF_ID, ContDmgPct, ContentLossUSD, InventoryCostUSD, IDDF_ID, InvDmgPct, InventoryLossUSD, DebrisID, Debris_Fin, Debris_Struc, Debris_Found, Debris_Tot, Restor_Days_Min, Restor_Days_Max, GridName]
                    field_names = field_names + new_fields
                    # counter = 0
                    counter2 = 0
                    
                    recCountNonZeroDepth = 0
                    
                    invalidSOID = 0
                    
                    #file_out = open(os.path.join(Resultsfgdb, x+".csv"), 'w')
                    
                    #CBH - to display the output directory on the final message
                    outputDir = os.path.join(Resultsfgdb, x+".csv")
                    file_out = open(outputDir, 'w')
                    raster = gdal.Open(dgp)
                    #fn = 'aster.img'
                    ds = gdal.Open(dgp, GA_ReadOnly)
                    if ds is None:
                        print('Could not open ' + dgp)
                        sys.exit(1)
                    #os.sys('gdalwarp '+dgp+' '+' C:/Users/Owner/Desktop/work.tif -t_srs "+proj=longlat +ellps=WGS84"')
                    band = raster.GetRasterBand(1)      
                    noData = band.GetNoDataValue()
                    cols = raster.RasterXSize
                    rows = raster.RasterYSize
                    transform = raster.GetGeoTransform()
                    xOrigin = transform[0]
                    yOrigin = transform[3]
                    pixelWidth = transform[1]
                    pixelHeight = -transform[5]
                    data = band.ReadAsArray(0, 0, cols, rows)
                    IsUTM = True if osr.SpatialReference(wkt=raster.GetProjection()).GetAttrValue('UNIT') == 'metre' else False
                    print('Is it UTM? ', IsUTM)
                            
                    with open(UDFOrig, newline='') as csvfile:
                        # reset counter
                        counter = 0
                        writer = csv.DictWriter(file_out, delimiter=', ', lineterminator='\n', fieldnames = field_names)
                        file = csv.DictReader(csvfile)
                        for row in file:
                            counter += 1#CBH - counter for unmatched SoccIds
                            #try:
                            #Check if any required fields are NULL
                            #If NULL do not process the record and do not make an entry in the results file
                            if None in [row[rField] for rField in requiredFields] or '' in [row[rField] for rField in requiredFields]: 
                                setValue(Depth_in_Struc, -99999)
                                writer.writerow(row) #CBH 08/29/19                            
                                continue #CBH - Change added 8/28/19
                            def getValue(name):# Get value of row from name.
                                if name != Depth_Grid:
                                    val = row[name].strip() if row[name].strip() != '' else 0#CBH
                                    try: val = float(val)#CBH
                                    except: pass#CBH
                                    return val
                                else:                        
                                    X = float(getValue(longitude))
                                    Y = float(getValue(latitude))
                                    X, Y = list(utm.from_latlon(Y, X)[:2]) if IsUTM else [X, Y]
                                    col = int((X - xOrigin) / pixelWidth)
                                    roww = int((yOrigin - Y ) / pixelHeight)
                                    
                                    #If incorrect depth grid used the depth is set to 0
                                    #PRUSVI
                                    #Fix for index out of range issue that was occuring due to larger depth grids
                                    val = data[roww][col] if abs(col) < abs(cols) and abs(roww) < abs(rows) and data[roww][col] != noData else 0 
                                    #val = retrieve_pixel_value((Y, X))
                                    #logger = logging.getLogger(str(data[roww][col]) + ' ' + str(abs(col)) + ' ' +str(abs(cols)) +  ' ' + str(abs(roww)) + ' ' + str(abs(rows)))                       
                                    row[name] = val
                                    return(float(val))

                            def setValue(name, value):# Set value of attribute from name to given parameter.
                                row[name] = value
                            
                            
                            if counter % 10000 == 0:# and QC_Warning:
                                print( "   processing record " + str(counter))

                            ###################################################
                            # Depth Adjustments
                            ###################################################
                            # Adjust Depth-in-Structure, given the First Floor Height. This will produce the occasional negative value. That is OK
                            # NOTE: Some users suggest that Coastal Flooding should be adjusted by an additional 1.0 foot, because in coastal flooding, 
                            # FFH should be considered to be at the freeboard.
                            # However, we confirmed with the Hazus coding team that the Hazus-MH Flood model does NO such adjustment
                            # So for now, we do not do ANY FFH adjustment
                            #
                            # Note this simple calculation varies with the Hazus-MH flood model implementation that rounds FFH to the nearest 0.5 foot level
                            # (which will produce minor differences in the loss ratio calculation).
                            # We maintain the script implements the methods more cleanly. There was no compelling technical reason for
                            # the Hazus-MH flood model to round to the nearest 0.5 foot.
                            rastervalue = getValue(Depth_Grid)
                            FFHeight = float(getValue(FirstFloorHt))
                            depth = rastervalue - FFHeight if rastervalue is not None else None   # Must mind the empty (null) case where the UDF has no Raster values
                            userDefinedFltyId = getValue(UserDefinedFltyId)   # Capture it for reporting purposes when encountering records with odd values.

                            # Get some basic information for the record
                            # One could insert some quality checks here and revert to a default if an illegal OccupancyClass, FoundationType, or NumStories
                            # At minimum, clean up the Occupancy Class. This sometimes has trailing spaces, due to Hazus processing quirks.
                            
                            x                = getValue(OccupancyClass)
                            OC                = x#.strip()#CBH
                            x                 = getValue(FoundationType)
                            foundationType  = float(x)#UKS - resolved the issue of RES1 with foundationType = 4 assigned the incorrect SOID due to incorrect datatype
                            numStories         = float(getValue(NumStories))
                            area             = float(getValue(Area))    # Used in Inventory Loss Calculation
                            if CoastalZoneSupplied:
                                CoastalZoneCode = flC #getValue(flC) # Only acquire if a Coastal Zone is defined for that UDF
                                CoastalZoneCode = "" if CoastalZoneCode is None else CoastalZoneCode#.strip()

                            # Build up the SpecifOccupId based on OccupancyClass, NumStories, FoundationType:
                            # Prefix, Middle Character, Suffix
                            #
                            # Prefix: Take advantage of the Slice feature in Python. Note the negative sign for right() equivalent
                            # Note that REL1 is the exception in the OccupancyClass list.
                            # QC:  We may want to bark an exception here: check for illegal OccupancyClass? or other combos (e.g. RES2 with more than one story)
                            sopre = OC[:1]+OC[-(len(OC)-3):] if OC != 'REL1' else 'RE1'

                            # Suffix: Easy - Basement or no Basement
                            #UKS - use the value 4 as a number not string
                            sosuf = 'B' if foundationType == 4 else 'N'

                            # Middle Character: Number of Stories
                            if OC[:4] == 'RES3':
                                # RES3 has three categories: 1 3 5
                                somid = '5' if numStories > 4 else '3' if numStories > 2 else '1'

                            elif OC[:4] == 'RES1':
                                # If NumStories is not an integer, assume Split Level residence
                                # Also, cap it at 3.
                                numStories = 3 if numStories > 3.0 else numStories
                                somid = str(round(numStories)) if numStories - round(numStories) == 0 else 'S'

                            elif OC[:4] == 'RES2':
                                # Manuf. Housing is by definition limited to one story
                                somid = '1'

                            else:
                                # All other cases: Easy!  1-3, 4-7, 8+
                                somid = 'H' if numStories > 6 else 'M' if numStories > 3 else 'L'
                                
                            SpecificOccupId = sopre + somid + sosuf
                            
                            #if OC[:4] == 'RES1' and foundationType == 4:
                            #    logger.info('foundation type = ' + str(foundationType) + ' and SOID = ' + SpecificOccupId)
                            #logger.info(SpecificOccupId)
                            
                            setValue(SOID, SpecificOccupId)

                            # Content and Inventory Cost. Determine each, even if structure not exposed to flooding
                            # Content Loss in US$: depends if user supplied a content cost field, and if it is > 0.
                            # If not, then use a default multiplier, depending on OccupancyClass, per Hazus-MH Flood Technical Manual table
                            CMult =  0.5 if OC in Content_x_0p5 else 1.0 if OC in Content_x_1p0 else 1.5 if OC in Content_x_1p5 else 0
                            if uccost:
                                xt = int(float(getValue(ContentCost)))
                                xt = -1 if xt is None else xt     # Null value check. If ContentCost is NULL, use the default value
                            else:
                                xt = -1
                            ccost = int(getValue(Cost)) * CMult if xt == -1 else xt

                            # Inventory Cost
                            OWDI = OC in Inventory_List
                            xt = getValue(InvCost) if uicost else -1
                            xt = xt if xt is not None else -1   #  Clean up case where InvCost is supplied but is null
                            if OWDI and xt == -1:
                                # Use default cost formula
                                for lutrow in iecon_lut:
                                    if lutrow['Occupancy'] == OC:
                                        GrossSales = lutrow['AnnualSalesPerSqFt']
                                        BusinessInv = lutrow['BusinessInvPctofSales']
                                        # Table imports as string type (?!) so we must convert tabular data to a float type
                                        # Yes, raw data is typically in Integer format, be flexible for future data which may be available in dollars.cents
                                        # Must divide by 100, as BusinessInv in the input table is a Percent figure
                                        # Area is in Square Feet
                                        icost = float(GrossSales)*float(BusinessInv)*area/100
                                        break
                            # If a user-supplied Inventory Cost is supplied, use it.
                            elif xt > -1 :
                                icost = getValue(InvCost)
                            else:
                                icost =0

                            setValue(ContentCostUSD, ccost)
                            setValue(InventoryCostUSD, icost)

                            #UKS - Negative Depth_in_Struc is OK but Negative depth from raster is not -Modified the logic to check against
                            #rastervalue
                            
                            # depth measured for that point, set some default values for the output to clearly indicate that there is No Exposure
                            # and quickly move on to the next record
                            
                            #UKS - modified the usage to depth (which is Depth_in_Struc) to rastervalue
                            if rastervalue is None or rastervalue <= 0:    # Depending on Depth Grid format, the Extract_2_Point returns Null or -9999
                                setValue(flExp, 0)    # Structure is NOT exposed.
                                #setValue(Depth_in_Struc, None)    # Default value, again emphasizing the point is not exposed. Make SummaryStats more straightforward
                                
                                #UKS - Recorded even though negative
                                if rastervalue is None:
                                    setValue(Depth_in_Struc, 0)
                                else:
                                    setValue(Depth_in_Struc, depth)
                                
                                setValue(BDDF_ID, 0)
                                setValue(BldgDmgPct, 0)
                                setValue(BldgLossUSD, 0)
                                setValue(CDDF_ID, 0)
                                setValue(ContDmgPct, 0)
                                setValue(ContentLossUSD, 0)
                                setValue(IDDF_ID, 0)
                                setValue(InvDmgPct, 0)
                                setValue(InventoryLossUSD, 0)
                                setValue(DebrisID, '')
                                setValue(Debris_Fin, None) # Partition the Debris into its three components - Table 11.1 Hazus-MH Flood Technical Manual
                                setValue(Debris_Struc, None)
                                setValue(Debris_Found, None)
                                setValue(Debris_Tot, None)
                                setValue(Restor_Days_Min, 0)
                                setValue(Restor_Days_Max, 0)
                                
                                #UKS
                                recCountNonZeroDepth -= 1
                            else:
                                # The UDF is exposed. Calculate Building, Content, Inventory Losses
                                setValue(flExp, 1)                                                    
                                setValue(Depth_in_Struc, depth)  # Record the depth in structure.
                                # (To be considered: optional freeboard adjustment for Coastal Flooding)
                                # Hazus 4.0 model does *no* adjustment. Some have suggested that one should add a freeboard margin; e.g., adjust FFH by -1 foot.
                                # But there is no clear consensus on such a conservative adjustment.

                                # If depth is over 24 feet or less than -4 feet, then adjust depth. LUTs do not extend beyond that range!
                                # Note that Hazus-MH flood model caps the grid raster at 24 feet, then does the subtraction. This creates some differences in results.
                                # We believe that you do the FFH subtraction before capping the depth at 24 feet.
                                depth = 24 if depth > 24 else depth
                                depth = -4 if depth < -4 else depth

                                # Get some basic information for the record
                                # One could insert some quality checks here andrevert to a default if an illegal OccupancyClass, FoundationType, or NumStories
                                # At minimum, clean up the Occupancy Class. This sometimes has trailing spaces, due to Hazus processing quirks.
                                x                = getValue(OccupancyClass)
                                OC                = x
                                x                 = str(getValue(FoundationType))
                                foundationType  = float(x)#UKS - resolved the issue of RES1 with foundationType = 4 assigned the incorrect SOID due to incorrect datatype
                                numStories         = float(getValue(NumStories))
                                area             = float(getValue(Area))    # Used in Inventory Loss Calculation

                                # Construct the strings for the LUT reference: if depth <0, use 'm'. If >0, use 'p'
                                # See the Column headings in the csv lookup tables.
                                # Need to strip out the minus sign using abs() and the decimal point using int(), and convert it to a string using str()
                                suffix_l = str(int(abs(math.floor(depth))))
                                suffix_u = str(int(abs(math.ceil(depth))))
                                prefix_l = 'm' if math.floor(depth) < 0 else 'p'
                                prefix_u = 'm' if math.ceil(depth) < 0 else 'p'  # Need to fuss over the boundary case  -1 < depth < 0
                                l_index = prefix_l + suffix_l
                                u_index = prefix_u + suffix_u

                                ###########################################################
                                # BUILDING LOSS CALCULATION
                                ###########################################################
                                # Did user specify a Building DDF? If so, use that to reference the Full LUT, else use the Default LUT.
                                # Due to Hazus-MH Flood definitions, this is Text type.
                                BID = getValue(BldgDamageFnID) if ubddf else None
                                
                                #print(', OC=' + OC + ', QC_Warning=' + str(QC_Warning)+ ', BID=' + str(int(BID)))
                                #print(bddf_lut_full_list)
                                # If BID is specified by the user, and defined, then assume they know what is best, and use the full lookup table.
                                # Tests are ok if you go left-to-right. Go from most-basic-test-to-more-advanced in the same line.  Can't flip the order here!
                                if BID is not None and BID != '' and str(int(BID)) in bddf_lut_full_list:
                                    # Search the  full lookup table to find the DDF_ID that matches the BID
                                    # 'gotcha' checks for no hits - set a check bit - that should not happen, given the membership test with bddf_lut_full_list.
                                    # For more efficiency, break out of the loop if it is found
                                    gotcha = 0
                                    #print("inside")
                                    for lutrow in bddf_lut_full:
                                        if lutrow['BldgDmgFnID'] == str(int(BID)):    # This is a string match. For completeness and trailing spaces, may want to make it an integer?
                                            gotcha += 1                                
                                            ddf1 = lutrow
                                            # Notify user if the OccupancyClass associated with the user-specified DDFID is inconsistent with the user-supplied OccupancyClass
                                            # This is not harmful; DOGAMI script has chosen to just process it (Hazus silently reverts back to the default!)
                                            # Simple notification
                                            OccClsCheck = ddf1['Occupancy']
                                            #print('Occupancy =' + OccClsCheck + ', OC=' + OC + ', QC_Warning=' + str(QC_Warning))
                                            if OccClsCheck != OC and QC_Warning:
                                                print("FYI: User-supplied Building DDFID " + BID + " Occupancy Class is inconsistent with UDF Occupancy Class " + OC + " versus "+OccClsCheck+ "  " + userDefinedFltyId)
                                            break
                                            
                                    #UKS RTC Task 35520 - Custom DDFs implementation 04/08/2020
                                    if gotcha != 0:
                                        d_lower = float(ddf1[l_index])
                                        d_upper = float(ddf1[u_index])
                                        #eflBDDF = 1
                                    else:
                                        d_lower = 0
                                        d_upper = 0
                                        damage = 0
                                        
                                    ddf_id = int(BID)  # Yes, it is redundant to post, again, what the user specified. But it is consistent with Default LUT
                                else:
                                    # We may have gotten here because of a bad BDDF code. If so, revert to the default and notify user
                                    # Note we are in the Default DDF section, and will calculate loss in that manner.
                                    if QC_Warning and BID is not None and BID != '' and int(BID)>0:
                                        print("User specified a non-official Building DDFID: " + BID + "    UID: " + userDefinedFltyId )
                                        print("   Reverting to default Building DDF for Occupancy Class " + OC)

                                    # Go through the lookup table, one row at a time to find the Structure of interest
                                    # 'gotcha' checks for no hits - set a check bit
                                    # Also, for more efficiency, break out of the loop if it is found
                                    gotcha = 0

                                    # Change DDF table only if Coastal Zone is defined (CoastalZoneSuppled) AND a legitimate Coastal Zone Code (AE, V, VE)
                                    # Otherwise use default ddf.
                                    # As of Hazus 4.0, Coastal lookup tables are only applicable for RES-type structures.
                                    
                                    #UKS 04/09/2020, RTC Task 35520 - Custom DDFs implementation
                                    #Need to assign default only if blank Building DDF provided by the user                       
                                    blut = bddf_lut_riverine
                                    if CoastalZoneSupplied and OC[:3] =='RES':
                                        if CoastalZoneCode == 'CAE' :
                                            blut = bddf_lut_coastalA
                                        if CoastalZoneCode == 'VE' or CoastalZoneCode == 'V':
                                            blut = bddf_lut_coastalV

                                    # Now do the lookup in the Default DDF
                                    for lutrow in blut:
                                        if lutrow['SpecificOccupId'] == SpecificOccupId:
                                            gotcha += 1
                                            ddf1 = lutrow
                                            #UKS 04/09/2020, RTC Task 35520 - Custom DDFs implementation
                                            # Not overwriting User's BDDF
                                            if BID is None or BID == '':
                                                ddf_id = lutrow['DDF_ID']   # For the Record. Will go in the Results file.
                                            else:
                                                ddf_id = int(BID)
                                            break # Quit once you found it.

                                    if gotcha == 0:
                                        # This should not occur
                                        print( "something wrong, no match for Specific Occupancy ID :" + SpecificOccupId + "   UDF: " + UserDefinedFltyId)
                                        invalidSOID += 1
                                        setValue(SOID, SpecificOccupId)#CBH
                                        setValue(BDDF_ID, 'Unmatched')#CBH
                                        writer.writerow(row)#CBH
                                        logger.info('Unmatched SOID: ' + SpecificOccupId + ' with userDefinedFltyId: ' + str(userDefinedFltyId))#CBH
                                        continue
                                        #sys.exit(2)
                                
                                # Dictionary lookup: get damage percentage for the particular row at the particular depths
                                # The Dictionary element comes from either the Full or the Default table; common code after this point.
                                #UKS 04/08/2020, RTC Task 35520 - Custom DDFs implementation
                                if gotcha != 0:
                                    d_lower = float(ddf1[l_index])
                                    d_upper = float(ddf1[u_index])
                                    # Get fractional amount of depth, for interpolation
                                    frac = depth - math.floor(depth)
                                    damage = (d_lower + frac*(d_upper - d_lower))/100
                                else:
                                    damage = 0
                                        
                                if gotcha == 0:
                                    # This should not occur, given the memebership test with bddf_lut_full_list. Just in case:
                                    print("Problem: nothing matches the SpecificOccupId of " + SpecificOccupId + "     Check entry UDFID " + str(userDefinedFltyId) + " with " + OC )
                                    SpecificOccupId = "XXXX"
                                    
                                    #UKS 04/08/2020, RTC Task 35520 - Custom DDFs implementation
                                    BDDF_ID = LR = bldg_loss = -9999
                                    damage = 0

                                # Calculate building loss, set other attributes                                    
                                setValue(BDDF_ID, ddf_id)
                                setValue(SOID, SpecificOccupId)
                                setValue(BldgDmgPct, damage*100)  # Hazus convention: percentage
                                bldg_loss = damage * int(getValue(Cost))
                                setValue(BldgLossUSD, bldg_loss)

                                ###########################################################
                                # CONTENT LOSS CALCULATION
                                ###########################################################
                                # Did user specify a Content DDF? If so, use that to reference the Full LUT, else use the Default LUT.
                                # Due to Hazus-MH Flood conventions, the CDDF_ID is of type Text
                                BID = getValue(ContDamageFnId)if ucddf else None

                                # If BID is specified by the user, then assume they know what is best, and use the full lookup table.
                                # Tests are ok if you go left-to-right. Go from most-basic-test-to-more-advanced in the same line.  Can't flip the order here!                   
                                if BID is not None and BID != '' and str(int(BID)) in cddf_lut_full_list:
                                    # Search the  full lookup table to find the DDF_ID that matches the BID
                                    # 'gotcha' checks for no hits - set a check bit - that should not happen, given the membership test with bddf_lut_full_list.
                                    # For more efficiency, break out of the loop if it is found
                                    gotcha = 0
                                    for lutrow in cddf_lut_full:
                                        if lutrow['ContDmgFnId'] == str(int(BID)):    # This is a string match. For completeness and trailing spaces, may want to make it an integer?
                                            gotcha += 1
                                            ddf1 = lutrow
                                            # Notify user if the OccupancyClass associated with the user-specified DDFID is inconsistent with the user-supplied OccupancyClass
                                            # This is not harmful; DOGAMI script has chosen to just process it (Hazus silently reverts back to the default!)
                                            # Simple notification
                                            OccClsCheck = ddf1['Occupancy']
                                            if OccClsCheck != OC and QC_Warning:
                                                print("FYI: User-supplied Content  DDFID " + BID + " Occupancy Class is inconsistent with UDF Occupancy Class " + OC + " versus "+OccClsCheck+ "  " + userDefinedFltyId)
                                            break
                                    #UKS 04/08/2020, RTC Task 35520 - Custom DDFs implementation
                                    if gotcha !=0:
                                        d_lower = float(ddf1[l_index])
                                        d_upper = float(ddf1[u_index])
                                    else:
                                        d_lower = 0
                                        d_upper = 0
                                        damage = 0
                                    ddf_id = int(BID)  # Yes, it is redundant to post, again, what the user specified. But it is consistent with Default LUT

                                else:
                                    # We may have gotten here because of a bad CDDF code. If so, revert to the default and notify user
                                    # Note we are in the Default DDF section, and will calculate loss in that manner.
                                    if QC_Warning and BID is not None and BID != '' and int(BID)>0:
                                        print( "FYI: User specified a non-official Content DDFID: " + BID + "    UID: " + userDefinedFltyId + "   Reverting to default Content DDF for Occupancy Class " + OC)

                                    # Go through the lookup table, one row at a time to find the Structure of interest
                                    # 'gotcha' checks for no hits - set a check bit
                                    # Also, for more efficiency, break out of the loop if it is found
                                    gotcha = 0

                                    # Change DDF table if Coastal; otherwise use default ddf.
                                    # As of Hazus 4.0, Coastal lookuptables only applicable for RES-type structures.
                                    # Need to filter out "REL" from "RES" - look at second letter
                                    
                                    #UKS 04/09/2020, RTC Task 35520 - Custom DDFs implementation
                                    # Need to assign default only if blank Content DDF provided by the user
                                    clut = cddf_lut_riverine
                                    if CoastalZoneSupplied and OC[:3] =='RES':
                                        if CoastalZoneCode == 'CAE' :
                                            clut = cddf_lut_coastalA
                                        if CoastalZoneCode == 'VE' or CoastalZoneCode == 'V':
                                            clut = cddf_lut_coastalV

                                    for lutrow in clut:
                                        if lutrow['SpecificOccupId'] == SpecificOccupId:
                                            gotcha += 1
                                            ddf1 = lutrow
                                            #UKS 04/09/2020, RTC Task 35520 - Custom DDFs implementation
                                            #Not overwriting User's CDDF
                                            if BID is None or BID == '':
                                                ddf_id = lutrow['DDF_ID']   # For the Record. Will go in the Results file.
                                            else:
                                                ddf_id = int(BID)
                                            break # Quit once you found it.
                                    if gotcha == 0:
                                        # This should not occur
                                        print("something wrong for Content lookup, no match for Specific Occupancy ID :" + SpecificOccupId + "   Counter:" + str(counter))


                                # Dictionary lookup: get damage percentage for the particular row at the particular depths
                                # The Dictionary element comes from either the Full or the Default table; common code after this point.
                                #UKS 04/08/2020, RTC Task 35520 - Custom DDFs implementation
                                if gotcha != 0:
                                    d_lower = float(ddf1[l_index])
                                    d_upper = float(ddf1[u_index])
                                    # Get fractional amount of depth, for interpolation
                                    frac = depth - math.floor(depth)
                                    damage = (d_lower + frac*(d_upper - d_lower))/100
                                else:
                                    damage = 0

                                if gotcha == 0:
                                    # Should not occur, given the check for membership in the list. But here just in case
                                    print("Problem with Content Loss: nothing matches the SpecificOccupId of " + SpecificOccupId + "Check entry " + str(counter) + " with " + OC + " " + str(numStories))
                                    SpecificOccupId = "XXXX"
                                    
                                    #UKS 04/08/2020, RTC Task 35520 - Custom DDFs implementation
                                    #No need to change the CDDF_ID
                                    CDDF_ID = LR = bldg_loss = -9999
                                    damage = 0
                            
                                setValue(CDDF_ID, ddf_id)
                                setValue(ContDmgPct, damage*100)   # Hazus convention: percenage
                                content_loss = damage*ccost
                                setValue(ContentLossUSD, content_loss)

                                ###########################################################
                                # INVENTORY LOSS CALCULATION
                                ###########################################################
                                # Did user specify an Inventory DDF? If so, use that to reference the Full LUT, else use the Default LUT.
                                # Due to Hazus-MH Flood conventions, the IDDF_ID is of type Text
                                BID = getValue(InvDamageFnId) if uiddf else None
                                # If BID is specified by the user, then assume they know what is best, and use the full lookup table.
                                # Tests are ok if you go left-to-right. Go from most-basic-test-to-more-advanced in the same line.  Can't flip the order here!
                                                
                                if BID is not None and BID != '' and str(int(BID)) in iddf_lut_full_list:
                                    # Search the  full lookup table to find the DDF_ID that matches the BID
                                    # 'gotcha' checks for no hits - set a check bit - that should not happen, given the membership test with bddf_lut_full_list.
                                    # For more efficiency, break out of the loop if it is found
                                    gotcha = 0
                                    for lutrow in iddf_lut_full:
                                        if lutrow['InvDmgFnId'] == str(int(BID)):    # This is a string match. For completeness and trailing spaces, may want to make it an integer?
                                            gotcha += 1
                                            ddf1 = lutrow
                                            # Notify user if the OccupancyClass associated with the user-specified DDFID is inconsistent with the user-supplied OccupancyClass
                                            # This is not harmful; DOGAMI script has chosen to just process it (Hazus silently reverts back to the default!)
                                            # Simple notification
                                            OccClsCheck = ddf1['Occupancy']
                                            if OccClsCheck != OC and QC_Warning:
                                                print("FYI: User-supplied Inventory DDFID " + BID + " Occupancy Class is inconsistent with UDF Occupancy Class " + OC + " versus "+OccClsCheck+ "  " + userDefinedFltyId)
                                            break
                                    #UKS 04/0982020, RTC Task 35520 - Custom DDFs implementation
                                    if gotcha !=0:
                                        d_lower = float(ddf1[l_index])
                                        d_upper = float(ddf1[u_index])
                                        frac = depth - math.floor(depth)
                                        damage = (d_lower + frac*(d_upper - d_lower))/100                            
                                    else:
                                        damage = 0
                                    ddf_id = int(BID)  # Yes, it is redundant to post, again, what the user specified. But it is consistent with Default LUT
                                else:
                                    # We may have gotten here because of a bad IDDF code. If so, revert to the default and notify user
                                    # Note we are in the Default DDF section, and will calculate loss in that manner.
                                    if QC_Warning and BID is not None and BID != '' and int(BID)>0:
                                        print( "User specified a non-official Inventory DDFID: " + BID + "    UID: " + userDefinedFltyId + "   Reverting to default Inventory DDF for Occupancy Class " + OC)

                                    # Go through the lookup table, one row at a time to find the Structure of interest
                                    # 'gotcha' checks for no hits - set a check bit
                                    # Also, for more efficiency, break out of the loop if it is found
                                    gotcha = 0

                                    # Inventory: There is no Coastal Flooding default table to use
                                    ilut = iddf_lut_riverine

                                    # Default Inventory DDF defined only for a subset of OccupancyClass types                                               
                                    if OC in Inventory_List:
                                        for lutrow in ilut:
                                            if lutrow['SpecificOccupId'] == SpecificOccupId:
                                                gotcha += 1
                                                ddf1 = lutrow
                                                #UKS 04/09/2020- Not overwriting User's IDDF
                                                if BID is None or BID == '':
                                                    ddf_id = lutrow['DDF_ID']   # For the Record. Will go in the Results file.
                                                else:
                                                    ddf_id = int(BID)
                                                break # Quit once you found it.
                                                
                                        #UKS 04/10/2020 - commented to clean up
                                        #if gotcha == 0:
                                            # This should not occur
                                        #    print("something wrong for Inventory lookup, no match for Specific Occupancy ID :" + SpecificOccupId + "   Counter:" + str(counter))
                                            #sys.exit(2)

                                        # Dictionary lookup: get damage percentage for the particular row at the particular depths
                                        # The Dictionary element comes from either the Full or the Default table; common code after this point.
                                        if gotcha != 0:
                                            d_lower = float(ddf1[l_index])
                                            d_upper = float(ddf1[u_index])
                                            # Get fractional amount of depth, for interpolation
                                            frac = depth - math.floor(depth)
                                            damage = (d_lower + frac*(d_upper - d_lower))/100

                                        if gotcha == 0:
                                            # Should not occur, given the check for membership in the list. But here just in case
                                            print("Problem with Inventory Loss: nothing matches the SpecificOccupId of " + SpecificOccupId + "Check entry " + str(counter) + " with " + OC + " " + str(numStories))
                                            SpecificOccupId = "XXXX"
                                            
                                            #UKS 04/08/2020 - No need to change the BDDF_ID & damage = 0 and SOCID not found in the deafult csv
                                            IDDF_ID = LR = bldg_loss = -9999
                                            damage = 0
                                    else:
                                        # No default DDF ID exists for the given OccupancyClass. Fill them in with zeros
                                        damage = 0
                                        ddf_id = 0
                                                        
                                setValue(IDDF_ID, ddf_id)                
                                setValue(InvDmgPct, damage*100)  # Hazus convention - percentage

                                # Inventory Loss in US$: depends if user supplied an inventory cost field, and if it is > 0.
                                # If not supplied, or 0, then use the default value based on OccupancyClass and Square Footage
                                # per Hazus-MH Flood Technical Manual table
                                # But note that the 'default value' is defined only for a subset of OccupancyClasses
                                # Logic spelled out in accompanying spreadsheet - to simplify it, create three variables
                                # OWDI = OccupancyClass with Default Inventory
                                # USID = User-supplied Inventory DDF is supplied and legitimate
                                # USIC = User-supplied Inventory Cost is supplied and non-zero and non-null

                                inventory_loss = damage * icost
                                setValue(InventoryLossUSD, inventory_loss)

                                ###########################################################
                                # DEBRIS CALCULATIONS
                                ###########################################################
                                # Calculate only for exposed buildings
                                if depth is not None and depth > 0:#CBH - added > 0, 8/28/19
                                    # Build up a DebrisID key for accessing Debris LUT table
                                    # Basement/No Basement only defined for RES1.
                                    # Slab/Footing: Simple mapping of FoundationType (includes Basement by definition)
                                    # dsuf = depth suffix
                                    bsm = 'NB'   # No Basement is the default. Only override for RES1
                                    #UKS - use the value 4 and 7 as a number not string
                                    fnd = 'SG' if (foundationType == 4 or foundationType == 7) else 'FT'  # SG: Slab on Grade.  FT = ???? DEFINE THIS - FROM BBOHN.
                                    # Flood depth key varies, depending if it's a RES1/Basement.
                                    if (OC == 'RES1' or OC == 'COM6') and foundationType == 4:
                                        #UKS - Special case handled for RES1 with FT SG
                                        #COM6 is always NB
                                        if OC == 'RES1':                                        
                                            bsm = 'B'
                                        dsuf = '-8' if depth <-4 else '-4' if depth < 0 \
                                            else '0' if depth <4 else '4' if depth < 6 \
                                            else '6' if depth <8 else '8'
                                    else:  # Credit to BBohn who identified 0/1/4/8/12 as common breakpoints shared by all non-RES1-Basement
                                        dsuf = '0' if depth <1 else '1' if depth < 4 \
                                        else '4' if depth <8 else '8' if depth < 12 else '12'                                    
                                                                    
                                    #RES2 - if depth in structure is negative (<0) - no losses should be produced
                                    #RES2 - if depth in structure greater than 0 but less than 1 finishes losses will be produced
                                    if OC =='RES2' and depth < 0:
                                        dsuf = ''
                                        
                                    debriskey = OC + bsm + fnd + dsuf
                                    for lutrow in debris_lut:
                                        if lutrow['DebrisID'] == debriskey:    # This is a string match. For completeness and trailing spaces, may want to make it an integer?
                                            gotcha += 1
                                            ddf1 = lutrow
                                    
                                    dfin_rate    =  float(ddf1['Finishes'])
                                    dstruc_rate =  float(ddf1['Structure'])
                                    dfound_rate =  float(ddf1['Foundation'])
                                    # All LUT numbers are in tons per 1000 square feet, so adjust for your particular structure
                                    dfin        = area * dfin_rate / 1000
                                    dstruc        = area * dstruc_rate / 1000
                                    dfound        = area * dfound_rate / 1000
                                    dtot        = dfin + dstruc + dfound
                                else:
                                    dfin = dstruc = dfound = dtot = debriskey = None

                                setValue(DebrisID, debriskey)
                                setValue(Debris_Fin, dfin)
                                setValue(Debris_Struc, dstruc)
                                setValue(Debris_Found, dfound)
                                setValue(Debris_Tot, dtot)

                                ###########################################################
                                # Restoration Time Calculation - the basis for all Direct Economic Loss numbers
                                # Based on the Min and Max days listed in   [dbo].[flRsFnGBS]
                                # Note how the table differs slightly from the TM, esp with Res with basements
                                # Note that the TM suggests some of these are not subject to a 10% threshold
                                # The method suggests using the Maximum; for completeness, the script produces both.
                                ###########################################################
                                # Calculate only for exposed buildings.
                                if depth is not None and depth > 0:# CBH - added > 0, 8/28/19
                                    # Build up a key for accessing the Restoration Time LUT table
                                    dsuf = '0' if depth <0 else '1' if depth < 1 \
                                        else '4' if depth <4 else '8' if depth < 8 else '12' if depth < 12 else '24'
                                    RsFnkey = OC + dsuf
                                    for lutrow in rest_lut:
                                        if lutrow['RestFnID'] == RsFnkey:    # This is a string match. For completeness and trailing spaces, may want to make it an integer?
                                            ddf1 = lutrow
                                            break
                                    restdays_min =  int(ddf1['Min_Restor_Days']) # This is the maximum days out (flRsFnGBS has a min and a max)
                                    restdays_max =  int(ddf1['Max_Restor_Days']) # This is the maximum days out (flRsFnGBS has a min and a max)
                                else:
                                    restdays_min = restdays_max = 0   # Or should it be None type?
                                setValue(Restor_Days_Min, restdays_min)
                                setValue(Restor_Days_Max, restdays_max)

                            # When running multiple grids, sensitivity tests, etc, adding the gridname makes it easier to sort upon an appended dataset             
                            setValue(GridName, gridroot)
                            recCountNonZeroDepth += 1
                            if counter == 1:
                                writer.writeheader()
                                writer.writerow(row)                           
                                continue
                            writer.writerow(row)
                            """
                            except Exception as e:
                                print(e)
                                logger.info("Expection occured")
                                writer.writerow(row)
                                #counter += 1
                                counter2 += 1
                                continue
                            """
                                    
                    file_out.close()       
                    #UKS - Sorting and logging          
                    logger.info('Loss calculations complete for the selected grid...')
                    logger.info('Sorting reults by Depth in structure...')
                    del data
                    csv_input = csv.DictReader(open(outputDir, 'r', newline=''))#csv.DictReader(f_input)
                    data = sorted(csv.DictReader(open(outputDir, 'r', newline='')), key=lambda row:(abs(float(row['Depth_in_Struc']))< 0, float(row['Depth_in_Struc'])), reverse=True)
                    #f_input.close()       
                    
                    #os.unlink(ResultsFile + '.csv')
                    logger.info('Results saved into ' + ResultsFile + '.csv')
                    with open(ResultsFile + '_sorted.csv', 'w', newline='') as f_output:
                        csv_output = csv.DictWriter(f_output, fieldnames=csv_input.fieldnames)
                        csv_output.writeheader()
                        csv_output.writerows(data)
                    f_output.close()



                #logger.info('Total records processed: ' + str(counter) + ' of ' + str(counter2) + ' records total.' + 'Total records with flooding: ' + str(recCountNonZeroDepth))

                    #CBH
                    #UKS - modified for complete file name on the final message box           
                    log.append([counter, counter2, recCountNonZeroDepth, invalidSOID, os.path.basename(dgp), ResultsFile + '.csv'])            

                    #recCountNonZeroDepth counter logged, concatenated to the message and reset
                message = ''   
                for grid in log:#CBH
                    message += 'For depth-grid: ' + str(grid[4]) + '\n' + str(grid[0])+' records processed of ' + str(grid[0]) + ' records total.\n' + \
                    'Total records with flooding: ' + str(grid[2]) + '\n' + \
                    'Total number of records with unmatched Specific Occupancy IDs found: ' + \
                    str(grid[3]) +'\n File saved to: ' + os.path.realpath(os.path.join(os.path.dirname(outputDir), str(grid[5]))) + '\n\n' #UKS - modified for complete file name #CBH - change added 8/28/19
                            
                    recCountNonZeroDepth = 0    

                #return(True, [counter, counter2, recCountNonZeroDepth, invalidSOID]) #UKS Commented
                return(True, message)#CBH added
        except Exception as e:
            print('something went wrong...')
            print('\n')
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(fname)
            print(exc_type, exc_tb.tb_lineno)
            print('\n')

            logger.info(e)
            print(e)
            return(False, counter)
