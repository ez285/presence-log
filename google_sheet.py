from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass
import gspread as gs
from google.oauth2.service_account import Credentials
import streamlit as sl
from datetime import date

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

@sl.cache_resource
def get_worksheets():
    creds = Credentials.from_service_account_info(sl.secrets['gcp_service_account'], scopes=SCOPES)
    gc = gs.authorize(creds)
    wbk = gc.open_by_key(sl.secrets['sheet_id'])
    return wbk.worksheet('Presence Log'), wbk.worksheet('Companies'), wbk.worksheet('People')
    
class _Sheets:
    def __init__(self) -> None:
        self.PresenceLog:gs.Worksheet
        self.Companies:gs.Worksheet
        self.People:gs.Worksheet

class _Data:
    def __init__(self) -> None:
        self.PresenceLog:list[dict[str, int|float|str]]
        self.Companies:list[dict[str, int|float|str]]
        self.People:list[dict[str, int|float|str]]

class _Search_Company:
    def ByID(self, id:int) -> list[dict[str, int|float|str]]: # type: ignore
        pass

    def ByName(self, name:str) -> list[dict[str, int|float|str]]:  # type: ignore
        pass

class _Search_Person:
    def ByID(self, id:int) -> list[dict[str, int|float|str]]: # type: ignore
        pass

    def ByName(self, kwargs:dict[str,str]) -> list[dict[str, int|float|str]]: # type: ignore
        pass

    def ByCompany(self, companyName:str) -> list[dict[str, int|float|str]]: # type: ignore
        pass

class _Search:
    def __init__(self) -> None:
        self.Company = _Search_Company()
        self.Person = _Search_Person()

class PresenceLog:
    def __init__(self) -> None:
        self.Sheets = _Sheets()
        self.Sheets.PresenceLog, self.Sheets.Companies, self.Sheets.People = get_worksheets()
        self.Data = _Data()
        self.Data.PresenceLog = self.Sheets.PresenceLog.get_all_records()
        self.Data.Companies = self.Sheets.Companies.get_all_records()
        self.Data.People = self.Sheets.People.get_all_records()
        self.Search = _Search()
        self.Search.Company.ByID = self._SearchCompanyByID
        self.Search.Company.ByName = self._SearchCompanyByName
        self.Search.Person.ByID = self._SearchPersonByID
        self.Search.Person.ByName = self._SearchPersonByName
        self.Search.Person.ByCompany = self._SearchPersonByCompany
    
    def LogPresence(self, data:list[dict[str, int|float|str]]) -> None:
        if list(data[0].keys()) != list(self.Data.PresenceLog[0].keys()):
            raise ValueError('Given titles do not match the expected ones')
        self.Sheets.PresenceLog.append_rows([0, '', itm['Company ID'], itm['Person ID'], itm['In'], itm['Out']] for itm in data], insert_data_option=gs.utils.InsertDataOption.insert_rows, table_range='A1')
    
    def AddCompanies(self, data:list[dict[str, int|float|str]]) -> list[int]:
        if self.Data.Companies[0].keys() - data[0].keys() != {'Company ID'}:
            raise ValueError('Given titles do not match the expected ones')
        ids = [itm['Company ID'] for itm in self.Data.Companies]
        idStart:int = 1 if not ids else max(ids) + 1 # type: ignore
        idsNew = [idStart + i for i in range(0, data.__len__())]
        self.Sheets.Companies.append_rows([[idNew, itm['Company Name'], itm['Role']] for idNew, itm in zip(idsNew, data)], insert_data_option=gs.utils.InsertDataOption.insert_rows, table_range='A1')
        return idsNew
    
    def AddPeople(self, data:list[dict[str, int|float|str]]) -> list[int]:
        if self.Data.People[0].keys() - data[0].keys() != {'Person ID'}:
            raise ValueError('Given titles do not match the expected ones')
        ids = [itm['Person ID'] for itm in self.Data.People]
        idStart:int = 1 if not ids else max(ids) + 1 # type: ignore
        idsNew = [idStart + i for i in range(0, data.__len__())]
        self.Sheets.People.append_rows([[idNew, itm['Company ID'], itm['First Name'], itm['Last Name'], '', '', '', True] for idNew, itm in zip(idsNew, data)], insert_data_option=gs.utils.InsertDataOption.insert_rows, table_range='A1')
        return idsNew
    
    def _SearchCompanyByID(self, id:int) -> list[dict[str, int|float|str]]:
        return [itm for itm in self.Data.Companies if itm['Company ID'] == id]
    
    def _SearchCompanyByName(self, name:str) -> list[dict[str, int|float|str]]:
        return [itm for itm in self.Data.Companies if itm['Company Name'] == name]
    
    def _SearchPersonByID(self, id:int) -> list[dict[str, int|float|str]]:
        return [itm for itm in self.Data.People if itm['Person ID'] == id]
    
    def _SearchPersonByName(self, kwargs:dict[str,str]) -> list[dict[str, int|float|str]]:
        if kwargs.keys() - {'First Name', 'Last Name'} or all([itm not in kwargs.keys() for itm in ['First Name', 'Last Name']]):
            raise ValueError('Given titles do not match the expected ones')
        res = self.Data.People
        for condition in kwargs.items():
            res = [itm for itm in res if itm[condition[0]] == condition[1]]
        return res
    
    def _SearchPersonByCompany(self, companyName:str) -> list[dict[str, int|float|str]]:
        if companyName not in [itm['Company Name'] for itm in self.Data.Companies]:
            raise ValueError('Given company name does not exist')
        companyID = self.Search.Company.ByName(companyName)[0]['Company ID']

        return [itm for itm in self.Data.People if itm['Company ID'] == companyID]
