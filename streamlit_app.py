from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass
from enum import IntEnum
import streamlit as sl
from datetime import date
from google_sheet import PresenceLog

@sl.cache_resource
def GetPresenceLog() -> PresenceLog:
    return PresenceLog()
pL = GetPresenceLog()

class StreamlitMode(IntEnum):
    NameInputStandard = 1
    NameInputNewCompany = 2
    NameInputNewPeople = 3
    InOut = 4
    FullListToday = 5
    InToday = 6

def ShowDateCompany() -> None:
    sl.session_state.setdefault('selectedDate', date.today())
    sl.date_input('Date', label_visibility='visible', format='DD/MM/YYYY', key='selectedDate')
    sl.selectbox('Company name', sorted([itm['Company Name'] for itm in pL.Data.Companies]) + ['Add New'], label_visibility='visible', key = 'selectedCompany')

def ShowPersonellInput(companyName:str) -> None:
    left, middle, right = sl.columns([4, 4, 1], vertical_alignment='bottom')
    with left:
        sl.text_input('First Name', label_visibility='visible', key='firstName')
    with middle:
        sl.text_input('Last Name', label_visibility='visible', key='lastName')
    with right:
        sl.button('Add', use_container_width=True, on_click=lambda companyName=companyName:AddNames(companyName))
    sl.markdown('**** Names added ****')
    sl.text('\n'.join(['\t'.join([itm2.__str__() for itm2 in itm]) for itm in sl.session_state.addedNames]))

def ShowNamesForCompany() -> None:
    selected = []
    for person in sorted(pL.Search.Person.ByCompany(sl.session_state.selectedCompany), key=lambda itm: f'{itm["First Name"]} {itm["Last Name"]}'):
        if sl.checkbox(f'{person["First Name"]} {person["Last Name"]}', key=f'person_{person["Person ID"]}'):
            selected.append(person['Person ID'])
    sl.session_state.selectedNameIDs = selected

def ShowSubmitButton() -> None:
    sl.button('Submit', on_click=Submit)

def Submit() -> None:
    # Firstly add the names that already exist in the tables
    if sl.session_state.selectedNameIDs:
        pL.LogPresence([{
            'Project Code':0, 'Project Name':'', 'Company ID':pL.Search.Company.ByName(sl.session_state.selectedCompany)[0]['Company ID'], # type: ignore
            'Person ID':itm, 'In':sl.session_state.selectedDate, 'Out':sl.session_state.selectedDate
        } for itm in sl.session_state.selectedNameIDs])
    # If additional names exist, add them now
    if sl.session_state.addedNames:
        # Get the given company names and find which are not already included in the table
        addedNamesCompaniesUnique = set(itm[1] for itm in sl.session_state.addedNames)
        existingCompanies = [itm['Company Name'] for itm in pL.Data.Companies]
        companyNamesToAdd = [itm for itm in addedNamesCompaniesUnique if itm not in existingCompanies]
        # If there are company names not included in the table, add them
        newCompanyIDs = {}
        if companyNamesToAdd:
            newCompanyIDs = pL.AddCompanies([{'Company Name':itm, 'Role':''} for itm in companyNamesToAdd])
            newCompanyIDs = dict(zip(companyNamesToAdd, newCompanyIDs))
        # Inevitably, there are people to add, so add them as well
        peopleToAdd = [{'Company ID':newCompanyIDs[itm[1]] if itm[1] in newCompanyIDs else pL.Search.Company.ByName(itm[1])[0]['Company ID'],
                       'First Name':itm[2], 'Last Name':itm[3], 'Role':'', 'Phone Number':'', 'Email':'','New Entry':True
                    } for itm in sl.session_state.addedNames]
        newPeopleIDs = pL.AddPeople(peopleToAdd)
        pL.LogPresence([{'Project Code':0, 'Project Name':'', 'Company ID':peopleToAdd[i]['Company ID'], 'Person ID':newPeopleIDs[i],
                         'In':sl.session_state.addedNames[i][0], 'Out':sl.session_state.addedNames[i][0]
                        } for i in range(0, newPeopleIDs.__len__())])
    # clear state variables and rerun from the beginning
    for itm in list(sl.session_state.keys()):
        sl.text(itm)
        if itm.startswith('person_'): # type:ignore
            sl.text('     handled')
            sl.session_state[itm] = False
            del sl.session_state[itm]
    sl.session_state.selectedNameIDs = []
    sl.session_state.addedNames = []

    sl.session_state.PreviousMode = sl.session_state.Mode
    sl.session_state.Mode = StreamlitMode.NameInputStandard
    GetPresenceLog.clear()

def AddNames(companyName:str) -> None:
    sl.session_state.addedNames.append([sl.session_state.selectedDate, companyName, sl.session_state.firstName, sl.session_state.lastName])
    sl.session_state.firstName = ''
    sl.session_state.lastName = ''

# First thing, set up state variables
if 'Mode' not in sl.session_state:
    sl.session_state.Mode = StreamlitMode.NameInputStandard
if 'PreviousMode' not in sl.session_state:
    sl.session_state.PreviousMode = StreamlitMode.NameInputStandard
if 'selectedNameIDs' not in sl.session_state:
    sl.session_state.selectedNameIDs = []
if 'addedNames' not in sl.session_state:
    sl.session_state.addedNames = []

# Second thing, reset state variable if mode changes
if sl.session_state.Mode.value != sl.session_state.PreviousMode.value:
    sl.session_state.selectedNameIDs = []
    sl.session_state.addedNames = []
    sl.session_state.PreviousMode = sl.session_state.Mode
    
if sl.session_state.Mode.value == StreamlitMode.NameInputStandard.value:
    ShowDateCompany()
    if sl.session_state.selectedCompany == 'Add New':
        sl.session_state.PreviousMode = sl.session_state.Mode
        sl.session_state.Mode = StreamlitMode.NameInputNewCompany
        sl.rerun()
    ShowNamesForCompany()
    ShowPersonellInput(sl.session_state.selectedCompany)
    ShowSubmitButton()
elif sl.session_state.Mode.value == StreamlitMode.NameInputNewCompany.value:
    ShowDateCompany()
    if sl.session_state.selectedCompany != 'Add New':
        sl.session_state.PreviousMode = sl.session_state.Mode
        sl.session_state.Mode = StreamlitMode.NameInputStandard
        sl.rerun()
    sl.text_input('Company Name', label_visibility='visible', key='newCompany')
    ShowPersonellInput(sl.session_state.newCompany)
    ShowSubmitButton()
elif sl.session_state.Mode.value == StreamlitMode.InOut.value:
    pass
elif sl.session_state.Mode.value == StreamlitMode.FullListToday.value:
    pass
elif sl.session_state.Mode.value == StreamlitMode.InToday.value:
    pass
