# scripts/run_worker.sh
#!/bin/bash

source venv/bin/activate
python manage.py rqworker default high low