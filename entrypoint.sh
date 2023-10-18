#!/bin/bash
exec python3 -m uvicorn service_for_ui_checker.service.main:app --host 0.0.0.0 --port 5000 --workers 5
