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
# Import by list of IDs or just one ID
python data_integration.py --file [file_path]
python data_integration.py --id [ID]

# Sync
python data_integration.py --sync
```
### Notes:  
- Runtime logs in `logs/runtime_log`  
- Sync logs in `logs/sync_log`


## Examples
```bash
python data_integration.py --file example_ids.txt # import with list of IDs
python data_integration.py --id 99 # import with a single ID
python data_integration.py --file example_ids.txt --sync
python data_integration.py --id 99 --sync
```