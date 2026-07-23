# Repository Housekeeping Register

Status: AUDIT

## Categories

### Product candidates
- app/
- articles/
- monitoring/
- wizard-src/
- wizard.py
- cognitivelogic_neo4j.py
- qen_context.py
- qen_source_integrations.py
- requirements.txt

### Infrastructure candidates
- Dockerfile
- docker-compose.yml

### Data and runtime candidates
- escalations.json
- graph.json
- pilots.json

### Scripts requiring review
- populate_balneare.py
- populate_balneare_mock.py

### Backup or temporary files
- main.py.bak_20260712_015255
- main.py.bak_20260712_022331
- qen_context.py.bak_20260712_021844

### Architecture and documentation candidates
- editorial-evolution-1.0/
- enterprise-platform-evolution-1.0/

## Rules

- No deletion before classification.
- No bulk git add.
- Backup files must not enter the repository.
- Runtime data must be separated from source code.
- Product and infrastructure files require individual review.
