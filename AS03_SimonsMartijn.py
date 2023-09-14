#Simons Martijn 2VFX04
import csv
import maya.cmds as cmds
import maya.mel as mel

# If a location/region has to be added in the future, you will need to adapt the data file and location_file so they both have the data needed to process into the script
# While creating the 3D text geometry, it is possible to get an error. This occurs to python version missmatch(2.7 vs 3.0 and higher)
# In the textToSpacedHex method you can change out comments to get the script to work for your python version

# Please before spawning new objects delete the old objects!
# Please close down the spreadsheet menu with the EXIT button and not the 'x' in the top right corner
# If you want to change the csv data files their names, also change the filter for the cmds.fileDialog2 => Has been set to only look for a certain name

class csvProcessing:
    # Creating a list with all the csv data
    def csvReader(self, data_list, file_directory_name):
        # Creating reader for csv data
        csvreader = csv.reader(file_directory_name)
        header = next(csvreader)
        # print(header)
        for row in csvreader:
            data_list.append(row)
        return data_list

    # Get location coordinates based on name of the region
    def get_location(self, csv_location_list, filter):
        location_lst = []
        for element in csv_location_list:
            region = element[0]
            if region == filter:
                location_lst.append((element[1], element[2]))
        return location_lst

    # Creating a list with all possible regions
    def create_region_list(self, csv_list):
        region_list = []
        for element in csv_list:
            region = element[0]
            if not region in region_list:
                region_list.append(region)
        return region_list

    # Create a list with all years in the data
    def create_year_list(self, csv_list):
        year_list = []
        for element in csv_list:
            year = element[2]
            if not year in year_list:
                year_list.append(year)
        return year_list

    def filter_by_year(self, csv_list, region):
        year_lst = []
        for element in csv_list:
            year = element[2]
            if element[0] == region:
                if not year in year_lst:
                    year_lst.append(int(element[2]))
        return year_lst

    # Returns if a specific year exists for a specific reason(boolean)
    def filter_by_specific_year(self, csv_list, region, years):
        bool_result = False
        year_lst = []
        for element in csv_list:
            year = element[2]
            if element[0] == region:
                if not year in year_lst:
                    year_lst.append(element[2])
        # print(year_lst)
        for year in year_lst:
            if year == years:
                bool_result = True
            else:
                return bool_result
        return bool_result

    # Give me the biomass mean number for this exact region and year, I will use this to set the size of the created object
    def get_yearly_biomass_mean(self, csv_list, region, years):
        biomass_list = []
        for element in csv_list:
            year = element[2]
            if element[0] == region and year == years:
                biomass_list.append(element[3])
        return biomass_list

    def close_file(self, file1, file2):
        file1.close()
        file2.close()


class CSVDataUI:
    def __init__(self):
        self.main_path = "None"
        self.main_path2 = "None"
        self.csv_data = []
        self.csv_location_data = []
        self.my_data = csvProcessing()
        self.csv_file = ""
        self.csv_location_file = ""
        self.region_list = []
        self.region_year_list = []

        self.checkbox_bool = []
        self.delete_obj_list = []

        self.my_aiStandardSurface_G = ""
        self.my_aiStandardSurface_R = ""
        self.my_aiStandardSurface_B = ""
        self.my_aiStandardSurface_Text = ""
        self.material_control = 0
        self.TxtObjects = []

        # Close the spreadsheet when objects get deleted
        self.checkIfDeleted = False

        # Is there already a spreadsheet open?
        self.spreadSheetBool = False

        # Creating window
        FRAME_WIDTH = 300
        self.window = cmds.window(title="Biomass fish stock per region", resizeToFitChildren=True)
        self.c_layout = cmds.columnLayout(adjustableColumn=True, rs=3)

        # Creating select folder buttons
        self.csv_data_button = cmds.button(parent=self.c_layout, label="Select CSV DATA file", width=FRAME_WIDTH,
                                           command=self.findCSVData)

        cmds.separator(style='none', h=5)

        self.csv_data_location_button = cmds.button(parent=self.c_layout, label="Select CSV LOCATION file",
                                                    width=FRAME_WIDTH, command=self.findCSVLocationData)

        cmds.separator(style='none', h=10)

        # Displaying window
        cmds.showWindow(self.window)

    def createRestUI(self):
        # Creating year slider
        min_year = int(min(self.my_data.create_year_list(self.csv_data)))

        max_year = int(max(self.my_data.create_year_list(self.csv_data)))
        # print(max_year)
        self.curr_year = min_year
        self.year_slider = cmds.intSliderGrp(field=True, label='Year', minValue=min_year, maxValue=max_year,
                                             value=min_year, cc=self.updateCurrYear)
        cmds.separator(style='none', h=10)

        # Creating checkboxes per region(greyed out of the data for the selected year does not exist)
        self.region_list = self.my_data.create_region_list(self.csv_data)
        r_layout = cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 200), (2, 200)])
        # Creating dictionary to easily acces the checkbox controls
        self.region_CB_controls = {}
        for region in self.region_list:
            boolean_cb_start = self.my_data.filter_by_specific_year(self.csv_data, region, "1970")
            if boolean_cb_start:
                checkbox_control = cmds.checkBox(label=region, v=boolean_cb_start)
                self.region_CB_controls[region] = checkbox_control
            else:
                checkbox_control = cmds.checkBox(label=region, v=boolean_cb_start, enable=False)
                self.region_CB_controls[region] = checkbox_control

        print(self.region_list)

        # Creating create object button
        cmds.separator(style='none', p=self.c_layout, h=5)
        self.create_button = cmds.button(label='Create objects', p=self.c_layout, command=self.createObjects,
                                         enable=True)
        cmds.separator(style='none', p=self.c_layout, h=5)

        # Creating create spreadsheet button
        self.spreadSheet_button = cmds.button(label='Create Spreadsheet', p=self.c_layout,
                                              command=self.createSpreadSheet,
                                              enable=True)
        cmds.separator(style='none', p=self.c_layout, h=5)

        # Creating delete create objs and exit button
        cmds.button(label='Delete all objects', p=self.c_layout, command=self.deleteCreatedObjects)
        cmds.separator(style='none', p=self.c_layout, h=5)
        cmds.button(label='Exit', p=self.c_layout, command='cmds.deleteUI(\"' + self.window + '\", window=True)')

        self.my_data.close_file(open(self.csv_file), open(self.csv_location_file))

    def findCSVData(self, args):
        self.main_path = cmds.fileDialog2(ff="*biomass-fish-stocks-region.csv", ds=2, fm=1)
        self.csv_file = self.main_path[0]
        print(self.csv_file)
        self.csv_data = self.my_data.csvReader(self.csv_data, open(self.csv_file))
        

    # Create select file function
    def findCSVLocationData(self, data_file):
        self.main_path2 = cmds.fileDialog2(ff="*Locations_map.csv", ds=2, fm=1)
        self.csv_location_file = self.main_path2[0]
        print(self.csv_location_file)
        self.csv_location_data = self.my_data.csvReader(self.csv_location_data, open(self.csv_location_file))
        self.createRestUI()
        

    # Creating spreadsheet button command
    def createSpreadSheet(self, args):
        if not self.spreadSheetBool:
            self.spreadSheetWindow = cmds.window(title="Data Spreadsheet", resizeToFitChildren=True)
            self.col_layout = cmds.columnLayout(adjustableColumn=True, rs=3)
            r_layout = cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 200), (2, 100)])
            cmds.text("Region", font="boldLabelFont")
            cmds.text("Float value", font="boldLabelFont")
            cmds.text(" ")
            cmds.text(" ")

            # Creating labels
            temp_lst = []
            temp_lst_converted_float = []
            for region in self.region_list:
                print(region)
                temp_bool = False
                temp_bool = cmds.checkBox(self.region_CB_controls[region], q=True, v=True)
                print(temp_bool)
                if temp_bool:
                    # Region column
                    temp_text = cmds.text(region)
                    cmds.text(temp_text, q=True, enable=cmds.checkBox(self.region_CB_controls[region], q=True, v=True))
                    temp_lst = self.my_data.get_yearly_biomass_mean(self.csv_data, region, str(self.curr_year))
                    print(temp_lst)
                    # Float value column
                    temp_lst_converted_float = round(float(temp_lst[0]), 2)

                    # Green = close to one, in this case i take values between 0.6 and 1.4, green = good for fish and humans
                    # bigger than one = Red = good for fish, bad for humans
                    # lower than one = blue = bad for fish, good for humans
                    if temp_lst_converted_float < 1.4 and temp_lst_converted_float > 0.6:
                        cmds.text(str(temp_lst_converted_float), backgroundColor=[0, 255, 0])
                    elif temp_lst_converted_float <= 0.6:
                        cmds.text(str(temp_lst_converted_float), backgroundColor=[0, 0, 255])
                    else:
                        cmds.text(str(temp_lst_converted_float), backgroundColor=[255, 0, 0])

            # When closing down the window please use the Exit button and not the X on the top right!

            cmds.text("Green", p=self.col_layout, backgroundColor=[0, 255, 0])
            cmds.text("Positive for both humans and fish", p=self.col_layout)

            cmds.text("Red", p=self.col_layout, backgroundColor=[255, 0, 0])
            cmds.text("Negative for humans, positive for fish", p=self.col_layout)

            cmds.text("Blue", p=self.col_layout, backgroundColor=[0, 0, 255])
            cmds.text("Positive for humans, negative for fish", p=self.col_layout)

            # Exit button
            cmds.separator(style='none', p=self.col_layout, h=5)
            cmds.button(label='Exit', p=self.col_layout,
                        command=self.exitButtonSpreadSheet)
            cmds.separator(style='none', p=self.col_layout, h=5)

            cmds.showWindow(self.spreadSheetWindow)
            self.spreadSheetBool = True

        else:
            self.spreadSheetWindowPopup()

    def exitButtonSpreadSheet(self, args):
        self.spreadSheetBool = False
        cmds.deleteUI(self.spreadSheetWindow)

    # Create popupwindow if a spreadsheet window is already open at this moment
    def spreadSheetWindowPopup(self):
        alreadyOpen = cmds.window(title="Spreadsheet popup", width=200, h=50)
        cmds.columnLayout(adjustableColumn=True)
        cmds.text("Spreadsheet is already open at this time.")
        cmds.separator(style='none', h=10)
        cmds.button(label='Exit', command='cmds.deleteUI(\"' + alreadyOpen + '\", window=True)')
        cmds.showWindow()

    # Create popupwindow if there are no created objects to delete
    def noObjectsWindow(self):
        secondWindow = cmds.window(title="No objects in scene to delete", width=200, h=50)
        cmds.columnLayout(adjustableColumn=True)
        cmds.text("You need to create objects before you can delete.")
        cmds.separator(style='none', h=10)
        cmds.button(label='Exit', command='cmds.deleteUI(\"' + secondWindow + '\", window=True)')
        cmds.showWindow()

    # Next 2 functions are used to create 3D text geometry
    def textToSpacedHex(self, text=''):
        out = []
        for c in text:
            # Change commented code depending on python version
            # Python 3.0 and up
            hx = c.encode("utf-8").hex()
            
            # Python 2.7
            # hx = c.encode('hex')
            out.append(hx)
        return ' '.join(out)

    def create3Dgeo(self, name, x, y, z, args):
        hx = self.textToSpacedHex(name)

        # Creating the Polygon Type
        cmds.CreatePolygonType()
        cmds.scale(0.2, 0.2, 0.2)
        cmds.move(x, y * 2, z)

        # Getting the node name from selection because the CreatePolygonType() command doesnt actually return the node name.
        NewTextObj = cmds.ls(sl=True)[0]
        print(NewTextObj)
        # Listing connections on the New Text object node to find the type node.
        TypeNode = cmds.listConnections(NewTextObj + ".message")

        # If we find it, Set attributes on it.
        if TypeNode:
            # Place any other preset settings in here.
            cmds.setAttr(TypeNode[0] + ".textInput", hx, type="string")
            cmds.setAttr("{}.curveResolution".format(TypeNode[0]), 1)
            # cmds.setAttr('type.alignmentMode', 2)
            # Apply material
            cmds.select(NewTextObj)
            cmds.hyperShade(assign=self.my_aiStandardSurface_Text)
        # Adding the New text object to the TxtObjects List
        cmds.parent(NewTextObj, self.text_geo_group)
        self.TxtObjects.append(NewTextObj)

        # cmds.rename(NewTextObj, name)

    def createMaterial(self, args):
        # green
        self.my_aiStandardSurface_G = cmds.shadingNode('aiStandardSurface', asShader=True)
        shdSG_G = cmds.sets(name='%sSG' % self.my_aiStandardSurface_G, empty=True, renderable=True,
                            noSurfaceShader=True)
        cmds.connectAttr('%s.outColor' % self.my_aiStandardSurface_G, '%s.surfaceShader' % shdSG_G)
        cmds.setAttr((self.my_aiStandardSurface_G + '.baseColor'), 1, 0, 0, type='double3')
        # self.delete_standardsurface_list.append(self.my_aiStandardSurface_G)

        # red
        self.my_aiStandardSurface_R = cmds.shadingNode('aiStandardSurface', asShader=True)
        shdSG_R = cmds.sets(name='%sSG' % self.my_aiStandardSurface_R, empty=True, renderable=True,
                            noSurfaceShader=True)
        cmds.connectAttr('%s.outColor' % self.my_aiStandardSurface_R, '%s.surfaceShader' % shdSG_R)
        cmds.setAttr((self.my_aiStandardSurface_R + '.baseColor'), 0, 1, 0, type='double3')
        # self.delete_standardsurface_list.append(self.my_aiStandardSurface_R)

        # blue
        self.my_aiStandardSurface_B = cmds.shadingNode('aiStandardSurface', asShader=True)
        shdSG_B = cmds.sets(name='%sSG' % self.my_aiStandardSurface_B, empty=True, renderable=True,
                            noSurfaceShader=True)
        cmds.connectAttr('%s.outColor' % self.my_aiStandardSurface_B, '%s.surfaceShader' % shdSG_B)
        cmds.setAttr((self.my_aiStandardSurface_B + '.baseColor'), 0, 0, 1, type='double3')
        # self.delete_standardsurface_list.append(self.my_aiStandardSurface_B)

        # Text

        self.my_aiStandardSurface_Text = cmds.shadingNode('aiStandardSurface', asShader=True)
        shdSG_Text = cmds.sets(name='%sSG' % self.my_aiStandardSurface_Text, empty=True, renderable=True,
                               noSurfaceShader=True)
        cmds.connectAttr('%s.outColor' % self.my_aiStandardSurface_Text, '%s.surfaceShader' % shdSG_Text)
        cmds.setAttr((self.my_aiStandardSurface_Text + '.baseColor'), 0, 0, 0, type='double3')

         # Delete button
    def deleteCreatedObjects(self, args):
        self.checkIfDeleted = True
        if self.checkIfDeleted:
            print(self.checkIfDeleted)
            try:
                cmds.deleteUI(self.spreadSheetWindow, control=True)
                self.spreadSheetBool = False
            except:
                pass
        if not self.delete_obj_list:
            print("No objects in scene to delete")
            self.noObjectsWindow()
            try:
                cmds.delete(self.text_geo_group)

            except:
                pass

        else:
            cmds.delete(self.delete_obj_list)
            cmds.delete(self.TxtObjects)
            cmds.delete(self.text_geo_group)
            self.TxtObjects = []
            self.delete_obj_list = []

    def noRegionsSelected(self, args):
        thirdWindow = cmds.window(title="No region selected", width=200, h=50)

        cmds.columnLayout(adjustableColumn=True)
        cmds.text("You need to select atleast one region.")
        cmds.separator(style='none', h=10)
        cmds.button(label='Exit', command='cmds.deleteUI(\"' + thirdWindow + '\", window=True)')
        cmds.showWindow()

    def createObjects(self, args):
        self.createBool = True
        # Creating the 3 used materials
        # print(self.csv_location_data)
        # biomass_list = []
        self.obj_green = []
        self.obj_red = []
        self.obj_blue = []
        self.obj_text = []
        # self.delete_obj_list = []
        self.checkbox_bool = {}
        self.no_selection_bool = []
        for region in self.region_list:
            temp_bool = False
            temp_bool = cmds.checkBox(self.region_CB_controls[region], q=True, v=True)
            self.no_selection_bool.append(temp_bool)
            self.checkbox_bool[region] = temp_bool

        self.text_geo_group = cmds.group(em=True, name='Region Geo Name Group')
        if True not in self.no_selection_bool:
            self.noRegionsSelected(args)
        else:
            if self.material_control == 0:
                self.createMaterial(args)
            self.material_control += 1
            for location in self.csv_location_data:
                if self.checkbox_bool[location[0]]:
                    region_location_x = float(location[1])
                    region_location_z = float(location[2])

                    print(location[0])
                    temp_biomass_value_lst = self.my_data.get_yearly_biomass_mean(self.csv_data, location[0],
                                                                                  str(self.curr_year))
                    temp_biomass_value_converted_float = float(temp_biomass_value_lst[0])
                    print(temp_biomass_value_converted_float)
                    radius = 5 * temp_biomass_value_converted_float
                    obj_locator = cmds.polySphere(n=location[0], r=radius)

                    # Assigning material and color based on the value
                    # Green = close to one, in this case i take values between 0.6 and 1.4, green = good for fish and humans
                    # bigger than one = Red = good for fish, bad for humans
                    # lower than one = blue = bad for fish, good for humans
                    print(obj_locator)
                    if temp_biomass_value_converted_float < 1.4 and temp_biomass_value_converted_float > 0.6:
                        # print("green")
                        self.obj_green.append(obj_locator[0])

                    elif temp_biomass_value_converted_float <= 0.6:
                        # print("blue")
                        self.obj_blue.append(obj_locator[0])

                    elif temp_biomass_value_converted_float >= 1.4:
                        # print("red")
                        self.obj_red.append(obj_locator[0])

                    cmds.move(region_location_x, 4 + radius / 2, region_location_z)
                    self.delete_obj_list.append(obj_locator[0])

                    # Creating the region name objects
                    self.create3Dgeo(location[0], region_location_x, 5 + radius / 2, region_location_z, args)
                    # print(self.obj_red)
                    # print(self.obj_blue)
                    # print(self.obj_green)
            self.addObjectMaterials(self.obj_green, self.obj_red, self.obj_blue, args)

            # Mel script part because i did not know how to get this with python and maya.cmds
            mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')
            
            self.createMaterial(args)
            cmds.select(clear=True)

    def addObjectMaterials(self, green, red, blue, args):
        # Red
        print(red)
        cmds.select(red)
        cmds.hyperShade(assign=self.my_aiStandardSurface_G)
        # self.delete_standardsurface_list.append(my_aiStandardSurface)

        # Green
        cmds.select(green)
        cmds.hyperShade(assign=self.my_aiStandardSurface_R)
        # self.delete_standardsurface_list.append(my_aiStandardSurface)

        # Blue
        cmds.select(blue)
        cmds.hyperShade(assign=self.my_aiStandardSurface_B)
        # self.delete_standardsurface_list.append(my_aiStandardSurface)

    def updateCurrYear(self, args):
        # Get current year
        self.curr_year = cmds.intSliderGrp(self.year_slider, q=True, v=True)
        self.updateCheckboxes(args)
        print(self.curr_year)

    def updateCheckboxes(self, args):
        # print("i update")
        enabled = False
        for region in self.region_list:
            self.region_year_list = self.my_data.filter_by_year(self.csv_data, region)
            # print(region)

            if self.curr_year in self.region_year_list:
                enabled = True

                # print("Year is avaialble")

            else:
                enabled = False

                # print("Year is not avaialble")
            # print(enabled)

            if enabled:
                cmds.checkBox(self.region_CB_controls[region], v=True, e=True, enable=enabled)
            else:
                cmds.checkBox(self.region_CB_controls[region], v=False, e=True, enable=enabled)
            # print(self.region_year_list)


my_data_UI = CSVDataUI()
