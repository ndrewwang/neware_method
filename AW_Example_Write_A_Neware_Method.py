#Programmatically writing a Neware method is useful
#Here's a basic example on how to use AW_Neware_Method_Writer

# File format is based on BTS7.X but appears to work fine for BTS8.
    #Although: for BTS8, RecordCondition/SafetyLimits are added as "Others" parameters in the table, not in the GUI panel


from AW_Neware_Method_Writer import *

export_path = '/exported_method.xml'

# BEGIN METHOD WRITING
d = start_method()
    
# SET META DATA REMARKS
d = set_remarks(d, Creator='AW', Remark='This is a test method, written with python.')

# SET RECORD/SAFETY PARAMETERS
RC = record_condition(d, Time = 2) #Record Condition (RC)
SL = safety_limit(d, Volt_Upper=5, Volt_Lower=0) #Safety Limits (SL)

# WRITE EACH STEP
d = step('Rest', d, Time=3600, RC=RC, SL=SL) 
d = step('CCCV_Chg', d, Volt=4, Curr=0.001, Stop_Curr=0.0001, RC=RC, SL=SL) 
d = step('Rest', d, Time=60, RC=RC, SL=SL)
d = step('CC_DChg', d, Volt=2, Curr=0.001, RC=RC, SL=SL)
d = step('Rest', d, Time=60, RC=RC, SL=SL)
d = step('Cycle', d, Start_Step=2,Cycle_Count=100, RC=RC, SL=SL) #loop & repeat

printstruct(d) #See XML file structure
write_xml(d, export_path) #Export
