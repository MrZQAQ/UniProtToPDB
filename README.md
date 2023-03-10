<!--
 * @Author: MrZQAQ
 * @Date: 2023-03-10 12:38
 * @LastEditTime: 2023-03-10 16:53
 * @LastEditors: MrZQAQ
 * @Description: README of project
 * @FilePath: /pyproject/README.md
 * CopyRight 2023 by MrZQAQ. All rights reserved.
-->

# UniProt ID to PDB ID and Chain

## Usage

There is two method to use this program: call API or CLI

### CLI

Run file, and input UniProtID, program will show a table of reuslt like:

```
+--------------+--------+-----------+
| UniProtKB_AC | PDB ID | PDB Chain |
+--------------+--------+-----------+
|    P02768    |  1AO6  |     A     |
|    P02768    |  1AO6  |     B     |
|    P02768    |  1BJ5  |     A     |
|    P02768    |  1BKE  |     A     |
+--------------+--------+-----------+
```

If you are first use, please import first:`python uniprotToPdb.py -m import -f <filename>`

File is provide by UniProt at [UniProt FTP Server](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/), download `idmapping_selected.tab.gz`

Import will take minutes or hours, be patience.

### API

#### `uniprotToPdb.importUniToPdb(fileName)`

Input: `fileName`: id mapping file from [UniProt](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/)

Action: import data to mysql

### Class Method

There is one class: `DBUniprotToPdb`

#### `uniprotToPdb.DBUniprotToPdb.query(uniprotId)`

Input: `uniprotId`: UniProtKB_AC ID, like `P12345`

Return: `selectRow, rowData`:

- `selectRow`: row number of query
- `rowData`: A list of Dictionary, like `[{'uniprotId':'P12345','pdbId':'100d','pdbChain':'A'},...]`

Note: If record number larger than 100, please use `DBUniprotToPdb.queryAll()`

#### `uniprotToPdb.DBUniProtToPdb.queryOne(uniprotId)`

Input: `uniprotId`: UniProtKB\_AC ID, like `P12345`

Return: `selectRow, rowData`:

- `selectRow`: should be `1`
- `rowData`: A list of Dictionary, like `[{'uniprotId':'P12345','pdbId':'100d','pdbChain':'A'}]`

#### `uniprotToPdb.DBUniProtToPdb.queryAll(uniprotId)`

Input: `uniprotId`: UniProtKB\_AC ID, like `P12345`

Return: `selectRow, rowData`:

- `selectRow`: row number of query
- `rowData`: A list of Dictionary, like `[{'uniprotId':'P12345','pdbId':'100d','pdbChain':'A'},...]`

Note: No limit to large query, **use carefully**.

---

## Dependencies

- `tqdm`
- `PyMySQL`
- `PrettyTable`

---

## Thanks

Thanks to [UniProt](https://www.uniprot.org/). 

<img src="https://raw.githubusercontent.com/ebi-uniprot/uniprot-website/main/src/images/uniprot-logo.img.svg" width="200px">

The data from UniProt is shared under the Creative Commons Attribution 4.0 International (CC BY 4.0) License (https://creativecommons.org/licenses/by/4.0/).

## License

Code is shared under GNU General Public License v3.0

Data is shared under the Creative Commons Attribution 4.0 International (CC BY 4.0) License
