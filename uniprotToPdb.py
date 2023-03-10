#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
Author: MrZQAQ
Date: 2023-03-10 10:51
LastEditTime: 2023-03-10 16:50
LastEditors: MrZQAQ
Description: 
FilePath: /pyproject/uniprotToPdb.py
CopyRight 2023 by MrZQAQ. All rights reserved.
'''
import warnings
from typing import List,Tuple,Dict
import gzip
import sys
import getpass
import configparser
import argparse
import re

from tqdm import tqdm
import pymysql
from prettytable import PrettyTable

# record number of per commit
COMMIT_BATCH = 2000

# Index of tsv mapping file
POS_INDEX = {
    'INDEX_UNIPROTKB_AC' : 0,
    'INDEX_UNIPROTKB_ID' : 1,
    'INDEX_GENE_ID' : 2,
    'INDEX_REFSEQ' : 3,
    'INDEX_GI' : 4,
    'INDEX_PDB' : 5,
    'INDEX_GO' : 6,
    'INDEX_UNIREF100' : 7,
    'INDEX_UNIREF90' : 8,
    'INDEX_UNIREF50' : 9,
    'INDEX_UNIPARC' : 10,
    'INDEX_PIR' : 11,
    'INDEX_NCBI_TAXON' : 12,
    'INDEX_MIM' : 13,
    'INDEX_UNIGENE' : 14,
    'INDEX_PUBMED' : 15,
    'INDEX_EMBL' : 16,
    'INDEX_EMBL_CDS' : 17,
    'INDEX_ENSEMBL' : 18,
    'INDEX_ENSEMBL_TRS' : 19,
    'INDEX_ENSEMBL_PRO' : 20,
    'INDEX_ADDITIONAL_PUBMED' : 21
}

class DBUniprotToPdb(object):

    INSERT_SQL = "INSERT INTO uniprot_to_pdb(uniprotkb_ac,pdb_id,pdb_chain) \
                VALUES (%s,%s,%s)"
    
    def __init__(self,createModel=False) -> None:
        sqlConfig = configparser.ConfigParser()
        sqlConfig.read('sqlconfig.ini', encoding='utf-8')
        self.sqlHost = sqlConfig['sqlconnect']['host']
        self.userName = sqlConfig['sqlconnect']['username']
        self.userPwd = sqlConfig['sqlconnect']['userpwd']
        self.dbName = sqlConfig['sqlconnect']['database']
        if createModel:
            if self.__check_database_exists() == True:
                self.__createDbSession(self.sqlHost,self.userName,self.userPwd,self.dbName)
                self.__createDataTable()
                self.__dropOldDataFromMysql()
            else:
                self.__createDataBase(self.sqlHost,self.userName,self.userPwd,self.dbName)
                self.__createDbSession(self.sqlHost,self.userName,self.userPwd,self.dbName)
                self.__createDataTable()
        else:
            if self.__check_database_exists() == False:
                print('-'*25)
                warnings.warn('DataBase is not exist! Check again!')
                print('-'*25)
                raise
            self.__createDbSession(self.sqlHost,self.userName,self.userPwd,self.dbName)
        
    def __createDbSession(self,sqlHost,userName,userPwd,dbName):
        self.__db = pymysql.connect(host=sqlHost,
                         user=userName,
                         password=userPwd,
                         database=dbName)

    def __del__(self):
        if '__db' in dir(self):
            self.__db.close()

    def __convertRowData(self, rowData:List[Dict]) -> List[Dict]:
        '''
        description: convert dictionary key format from sql to camel
        return: keep same with rowData.
        '''
        if isinstance(rowData,List):
            for row in rowData:
                row['uniprotId'] = row.pop('uniprotkb_ac')
                row['pdbId'] = row.pop('pdb_id')
                row['pdbChain'] = row.pop('pdb_chain')
        if isinstance(rowData,Dict):
            rowData['uniprotId'] = rowData.pop('uniprotkb_ac')
            rowData['pdbId'] = rowData.pop('pdb_id')
            rowData['pdbChain'] = rowData.pop('pdb_chain')
        return rowData

    def query(self, uniprotId) -> Tuple[int,List[Dict]]:
        '''
        description: query pdb information by uniprot id
        return {*}: A list of dictionary. Like `[{'uniprotId':'P12345','pdbId':'100d','pdbChain':'A'},...]`
                    If record number larger than 100, please use `DBUniprotToPdb.queryAll()`
        '''        
        SQL = "SELECT uniprotkb_ac, pdb_id, pdb_chain FROM uniprot_to_pdb WHERE uniprotkb_ac = %s"
        cursor = self.__db.cursor(pymysql.cursors.DictCursor)
        selectRow = cursor.execute(SQL,uniprotId)
        if selectRow >= 100:
            warnings.warn('Large query, only return part of result. If you want all result, please try to use DBUniprotToPdb.queryAll()',FutureWarning)
            rowData = cursor.fetchmany(100)
        else:
            rowData = cursor.fetchall()
        rowData = self.__convertRowData(rowData)
        return selectRow, rowData

    def queryAll(self, uniprotId) -> Tuple[int,List[Dict]]:
        SQL = "SELECT uniprotkb_ac, pdb_id, pdb_chain FROM uniprot_to_pdb WHERE uniprotkb_ac = %s"
        cursor = self.__db.cursor(pymysql.cursors.DictCursor)
        selectRow = cursor.execute(SQL,uniprotId)
        rowData = self.__convertRowData(cursor.fetchall())
        return selectRow, rowData

    def queryOne(self, uniprotId) -> Tuple[int,Dict]:
        SQL = "SELECT uniprotkb_ac, pdb_id, pdb_chain FROM uniprot_to_pdb WHERE uniprotkb_ac = %s LIMIT 1"
        cursor = self.__db(pymysql.cursors.DictCursor)
        selectRow = cursor.execute(SQL, uniprotId)
        rowData = self.__convertRowData(cursor.fetchone())
        return selectRow, rowData

    def __check_database_exists(self):
        conn = pymysql.connect(
            host=self.sqlHost,
            user=self.userName,
            password=self.userPwd,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{self.dbName}'")
                result = cursor.fetchone()
                if result is not None:
                    return True
                else:
                    return False
        finally:
            conn.close()

    def __dropOldDataFromMysql(self):
        cursor = self.__db.cursor()
        SQL_DROP = 'truncate table uniprot_to_pdb'
        cursor.execute(SQL_DROP)

    def __createDataBase(self,sqlHost,userName,userPwd,dbName):
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'LIKE', 'ORDER BY', 'GROUP BY', 'JOIN', 'INNER JOIN', 'OUTER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'UNION', 'CREATE', 'TABLE', 'INDEX', 'DROP', 'ALTER', 'ADD', 'COLUMN', 'PRIMARY KEY', 'FOREIGN KEY']
        sql_punctuations = ['(', ')', '[', ']', '{', '}', ';', ':', ',', '.', '!', '?']

        def filter_string(input_str):
            input_str = input_str.replace(' ', '').replace('\n', '')
            letters_only = re.sub('[^a-zA-Z]', '', input_str)
            for word in sql_keywords + sql_punctuations:
                if word in letters_only.upper():
                    return True
            return False
        if filter_string(dbName):
            print('-'*25)
            warnings.warn('The database name contains illegal characters.')
            print('-'*25)
            raise
        DDL = "CREATE DATABASE `"+ dbName +"`"
        conn = pymysql.connect(host=sqlHost,user=userName,password=userPwd,charset='utf8mb4')
        with conn.cursor() as cursor:
            cursor.execute(DDL)
    
    def __createDataTable(self):
        DDL = '''
                CREATE TABLE IF NOT EXISTS `uniprot_to_pdb` (
                    `id` bigint unsigned NOT NULL AUTO_INCREMENT,
                    `uniprotkb_ac` varchar(40) COLLATE utf8mb4_general_ci NOT NULL,
                    `pdb_id` varchar(10) COLLATE utf8mb4_general_ci NOT NULL,
                    `pdb_chain` varchar(10) COLLATE utf8mb4_general_ci DEFAULT NULL,
                    PRIMARY KEY (`id`),
                    KEY `uniprot_to_pdb_uniprotkb_ac_IDX` (`uniprotkb_ac`) USING BTREE
                    ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        '''
        with self.__db.cursor() as cursor:
            cursor.execute(DDL)

    def insertData(self,insertData):
        with self.__db.cursor() as cursor:
            cursor.executemany(self.INSERT_SQL,insertData)

    def commit(self):
        self.__db.commit()

def importUniToPdb(fileName):
    db = DBUniprotToPdb(createModel=True)
    with gzip.GzipFile(fileName,'rb') as zipfile:
        for i,oneRecord in tqdm(enumerate(zipfile)):
            oneRecord = oneRecord.decode()
            INSERT_DATA = __praseRecordByLine(oneRecord)
            if INSERT_DATA == -1:
                continue
            db.insertData(INSERT_DATA)
            if i%COMMIT_BATCH == 0:
                db.commit()

def __praseRecordByLine(line):
    lineList = line.strip('\r\n').split('\t')
    pdbList = lineList[POS_INDEX['INDEX_PDB']].strip().split('; ')
    if pdbList[0] == '':
        return -1
    uniprotKB_AC = lineList[POS_INDEX['INDEX_UNIPROTKB_AC']]
    INSERT_DATA = []
    for pdb in pdbList:
        pdbId,pdbChain = tuple(pdb.split(':'))
        INSERT_DATA.append((uniprotKB_AC,pdbId,pdbChain))
    return INSERT_DATA

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog = 'UniProt ID Mapping',
                    description = 'Query UniProt ID Mapping at local'
                    )
    parser.add_argument('-m','--model',default='query',choices=['query','import'],help='query / import model selector')
    parser.add_argument('-f','--filename',default='idmapping_selected.tab.gz',help='mapping file needed when goto import model')
    args = parser.parse_args()

    if args.model == 'import':
        fileName = args.filename
        importUniToPdb(fileName)
        exit(0)
    db = DBUniprotToPdb()
    print('Wecome to UniProtKB_AC to PDB Service!\nYou can exit using \'exit!\'')
    while True:
        uniprotId = input('\nUniProtKB_AC: ')
        if uniprotId == 'exit!':
            break
        rowNumber,rowData = db.queryAll(uniprotId)
        if rowNumber == 0:
            print('Can\'t find any mapping in UniProt IdMapping Service!')
        else:
            print(f'Find {rowNumber} record in UniProt IdMapping Service.')
            table = PrettyTable()
            table.field_names = ['UniProtKB_AC','PDB ID','PDB Chain']
            for row in rowData:
                table.add_row([row['uniprotId'],row['pdbId'],row['pdbChain']])
            print(table)
