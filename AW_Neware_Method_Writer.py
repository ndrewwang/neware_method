import xmltodict as xd
import pandas as pd
import zipfile
import os
from copy import deepcopy

#EDIT PATH <<<<<<<<<<<<
PATH = '/baseline_neware.xml' #Baseline method filepath (a BTS7.X method file with a single "end step")

def printstruct(data):
    '''
    Print XML file for navigating structure
    '''
    import json
    print(json.dumps(data, indent=5, default=str))

def read_xml(TEMPLATE_PATH):
    '''
    Read XML file into python dictionary
    '''
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f: 
        xml_content = f.read()
    d = xd.parse(xml_content)
    return d

def write_xml(d, EXPORT_PATH):
    '''
    Export dictionary of Neware method file into XML format
    '''
    xml_output = xd.unparse(d, pretty=True)
    with open(EXPORT_PATH, 'w', encoding='utf-8') as new_file:
        new_file.write(xml_output)

def set_val(key,val):
    '''
    General "@Is_Select" & "@Value" setter for Neware methods
    Catches weird scaling for voltage and current here.
        Ultimately dependent on Scale@Value in Root/Config/HeadInfo.
    '''
    if 'Volt' in key:
        val = val*1E4
    elif 'Curr' in key:
        val = val*1E6
    elif 'Time' in key:
        val = val*1E3
    elif 'Cap' in key:
        val = val*1E6*3600 #Ah from As
    val_dict = {"@Is_Select": 1,
                "@Value": val}
    return val_dict

def set_remarks(dd,**kwargs):
    '''
    Set meta-data in Neware method. 
    Viable entries:
        Creator
        Remarks
    '''
    d = deepcopy(dd)
    for key, value in kwargs.items():
        d['root']['config']['Head_Info'][key]['@Value']=value
    return deepcopy(d)

def record_condition(dd,**kwargs):
    '''
    Set Record Condition, as in the Neware method aux settings. Updated via Dict Reference.
    Viable entries:
        Time (s)
        Volt (V)
        Curr (A)
    '''
    d = deepcopy(dd)
    record = d['root']['config']['Step_Info']['Step1']['Record']['Main']
    for key, value in kwargs.items():
        record[key] = set_val(key,value)
    return deepcopy(record)

def safety_limit(dd,**kwargs):
    '''
    Set Safety Limit, as in the Neware method aux settings. Updated via Dict Reference.
    Viable entries:
        Volt_Lower (V)
        Volt_Upper (V)
        Curr_Lower (A)
        Curr_Upper (A)
        Cap_Upper (AH)
        Delay_Time (s)
    '''
    d = deepcopy(dd)
    safety = d['root']['config']['Step_Info']['Step1']['Protect']['Main']
    for key, value in kwargs.items():
        if 'Volt' in key:
            key = key.replace('Volt_','')
            safety['Volt'][key] = set_val('Volt',value)
        elif 'Curr' in key:
            key = key.replace('Curr_','')
            safety['Curr'][key] = set_val('Curr',value)
        elif 'Cap_Upper' in key:
            safety['Cap']['Upper'] = set_val('Cap',value)
        else:
            safety[key] = set_val(key,value)
    return deepcopy(safety)

def add_step_space(dd):
    '''
    Increments number of steps in Neware method
    '''
    d = deepcopy(dd)
    old_num_steps = int(d['root']['config']['Step_Info']['@Num'])
    new_num_steps = old_num_steps + 1
    d['root']['config']['Step_Info']['@Num'] = new_num_steps
    old_last_key = 'Step' + str(old_num_steps)
    new_last_key = 'Step' + str(new_num_steps)
    #Copy end condition to steps+1
    d['root']['config']['Step_Info'][new_last_key] = deepcopy(d['root']['config']['Step_Info'][old_last_key])
    d['root']['config']['Step_Info'][new_last_key]['@Step_ID']=new_num_steps
    #Replace previous end condition with template end step
    d['root']['config']['Step_Info'][old_last_key] = deepcopy(d['root']['config']['Step_Info'][old_last_key])
    d['root']['config']['Step_Info'][old_last_key]['@Step_ID']=old_num_steps
    return deepcopy(d)

def step(step_str,dd,**kwargs):
    '''
    Add a step with step details on limits/parameters
    Common step limits:
        Time (s)
        Curr (A)
        Volt (V)
        Stop_Curr (A) for CV
    Cycle loop parameters:
        Start_Step
        Cycle_Count
    '''
    d = add_step_space(dd)
    n = int(d['root']['config']['Step_Info']['@Num'])-1
        

    step_dict = {'Rest': 4,
               'CC_DChg': 2,
               'CC_Chg': 1,
               'CV_Chg': 3,
               'CV_DChg': 19,
               'CCCV_Chg': 7,
               'CCCV_DChg': 20,
               'Cycle': 5}

    step_id = step_dict[step_str]
    d['root']['config']['Step_Info']['Step' + str(n)]['@Step_Type'] = step_id

    d_root = d['root']['config']['Step_Info']['Step'+str(n)]['Limit']['Main'] #mapped dict

    if 'CC_' in step_str:
        kwargs['Stop_Volt'] = kwargs.pop('Volt') #CC steps use a StopVolt limit and not a Volt limit

    if step_str == 'Cycle': #Cycle edits Limit-Other, not main
        d_root = d['root']['config']['Step_Info']['Step' + str(n)]['Limit']['Other'] #mapped dict
    
    for key, value in kwargs.items(): #General case rest/cv/cccv
        if key=='RC': #Record Condition
            d['root']['config']['Step_Info']['Step' + str(n)]['Record']['Main'] = value
            
        elif key=='SL': #Safety Limit
            d['root']['config']['Step_Info']['Step' + str(n)]['Protect']['Main'] = value
            
        else:
            d_root[key] = set_val(key,value)

    return deepcopy(d)

def start_method():
    '''
    Read the template Neware XML file to start new method writing
    '''
    d = read_xml(PATH)
    return d
