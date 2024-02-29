# Exam_bank orchestration project
### Import exam with single `ID`
```bash
python import.py --id [ID]
```
### Import exam with list IDs (contained in a text file)
```bash
# example: python import.py --file example_ids.txt
python import.py --file [file_path]
```
### Sync exam with single `ID`
```bash
python sync.py --id [ID]
```
### Sync exam with list IDs (contained in a text file)
```bash
python sync.py --file [file_path]
