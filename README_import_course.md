# IMPORT COURSE BY ID

## Description

Used to import courses from CMS to exam_bank, with logging and ID mapping mechanisms.  

Logs are stored in the `logs/import_course_log`.  

## Notice
- Change the environment variables in the `.env.dev` file.  
- Create the `course_id_mapping` table with the following SQL statement:  
  ```sql
    CREATE SEQUENCE IF NOT EXISTS course_id_mapping_id_seq;
    CREATE TABLE course_id_mapping (
        id INTEGER PRIMARY KEY DEFAULT nextval('course_id_mapping_id_seq'),
        created_at TIMESTAMP,
        original_id INTEGER NOT NULL DEFAULT 0,
        new_id BIGINT NOT NULL,
        entity_type VARCHAR(150) NOT NULL,
        parent_new_id BIGINT NOT NULL DEFAULT 0,
        task_name VARCHAR(50) not null
    );
  ```
- In the `course_id_mapping` (cim) table:
  - For `entity_type` other than `course` and `question`, `cim.new_id` will be the ID from the `course_lecture` table.
  - For `course` and `question`, `cim.new_id` will be the ID from the `course` and `quiz_question` tables, respectively.
  - For `guide` and `collection`, `original_id` will be 0.



## Usage

```bash
python import_course_by_id.py --help
```

## Example

```bash
python import_course_by_id.py --course_id=10
```

## Output

Check the newly created log file in the logs folder.