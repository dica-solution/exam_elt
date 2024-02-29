# Exam_bank orchestration project

## Installation
- Clone the project
```bash
git clone git@github.com:dica-solution/exam_elt.git
cd exam_etl
```
- Setting up the environment
```bash
poetry install
```

## Environment configuration
Set up the Environment variables in the `.env.dev` depend on the installed environment
```bash
DATABASE_URL
```


## Usage
- Import exam with single `ID`
```bash
python import.py --id [ID]
```
- Import exam with list IDs (contained in a text file)
```bash
python import.py --file [file_path]
```
- Sync exam with single `ID`
```bash
python sync.py --id [ID]
```
- Sync exam with list IDs (contained in a text file)
```bash
python sync.py --file [file_path]
```

## Examples
```bash
python import.py --file example_ids.txt # import with list of IDs
python import.py --id 99 # import with a single ID
```