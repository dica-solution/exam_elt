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
Set up the Environment variables in the `.env.dev` depend on the installed environment. If the installed environment is on `dica-server`, you can skip this step.
```bash
DATABASE_URL
```


## Usage
- Create the `tracking_logs` table if not existed
```bash
python create_id_mapping_table.py
```
- Depending on specific requirements, you will choose one from the following commands:
```bash
# Import exam with single `ID`
python import.py --id [ID]

# Import exam with list IDs (contained in a text file)
python import.py --file [file_path]

# Sync exam with single `ID`
python sync.py --id [ID]

# Sync exam with list IDs (contained in a text file)
python sync.py --file [file_path]
```
### Notes:  
- All error IDs when import or sync are saved in folder `error_logs`
- All imported IDs are saved in folder `exam_ids`
- If you want to import error IDs:
  ```bash
  python import.py --file [file_path_error_ids] # ex: python import.py --file error_logs/import_error_ids_2024-03-04_10-35-11.txt
  ```


## Examples
```bash
python import.py --file example_ids.txt # import with list of IDs
python import.py --id 99 # import with a single ID
```