#What if we want to write many neware methods at once with slightly different settings?
#This is an example that reads a table with cells/capacities, and makes methods with different top voltage cut offs
#It also uses the same C-rate but scales currents to match based on the capacities of the cells

from AW_Neware_Method_Writer import *

export_path = '/' #EXPORT PATH
cell_csv = 'Multiple_Cell_Data.csv'
zip_name = 'zipped_neware_methods.zip'

files = []
celldf = pd.read_csv(cell_csv)
print(celldf)

for i in range(len(celldf)):

    #Assign data from some csv/gsheet:
    CELL = celldf.iloc[i]['CELL']
    CHANNEL = celldf.iloc[i]['CHANNEL']
    CREATOR = celldf.iloc[i]['CREATOR']
    REMARK = celldf.iloc[i]['REMARKS']
    V_MAX = celldf.iloc[i]['VMAX (V)']
    V_MIN = celldf.iloc[i]['VMIN (V)']
    CAPACITY = celldf.iloc[i]['CAPACITY (mAh)']/1000 #Ah

    EXPORT_PATH = export_path + str(CHANNEL) + '_' + CELL + '.xml'
    files.append(EXPORT_PATH) #list of all files 

    d = start_method()
    d = set_remarks(d, Creator=CREATOR, Remark=REMARK)
    RC = record_condition(d, Time = 2) #Record Condition (RC)
    SL = safety_limit(d, Volt_Upper=5, Volt_Lower=0) #Safety Limits (SL)

    #INITIAL REST
    d = step('Rest', d, Time=60, RC=RC, SL=SL)
    #FORMATION
    C_rate = 0.1
    CV_rate = 0.05
    d = step('CCCV_Chg', d, Volt=V_MAX, Curr=CAPACITY*C_rate, Stop_Curr=CAPACITY*CV_rate, RC=RC, SL=SL)
    d = step('Rest', d, Time=120, RC=RC, SL=SL)
    d = step('CC_DChg', d, Volt=V_MIN, Curr=CAPACITY*C_rate, RC=RC, SL=SL)
    d = step('Rest', d, Time=120, RC=RC, SL=SL)
    d = step('Cycle', d, Start_Step=2,Cycle_Count=3, RC=RC, SL=SL)
    #CYCLING
    C_rate = 1
    CV_rate = 0.05
    d = step('CCCV_Chg', d, Volt=V_MAX, Curr=CAPACITY*C_rate, Stop_Curr=CAPACITY*CV_rate, RC=RC, SL=SL)
    d = step('Rest', d, Time=120, RC=RC, SL=SL)
    d = step('CC_DChg', d, Volt=V_MIN, Curr=CAPACITY*C_rate, RC=RC, SL=SL)
    d = step('Rest', d, Time=120, RC=RC, SL=SL)
    d = step('Cycle', d, Start_Step=7,Cycle_Count=100, RC=RC, SL=SL)
    write_xml(d, EXPORT_PATH)
    # printstruct(d)

with zipfile.ZipFile(export_path + zip_name, 'w') as myzip:
    for f in files:   
        filename = os.path.basename(f)
        myzip.write(f, arcname=filename)
