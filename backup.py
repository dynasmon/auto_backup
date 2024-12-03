#!/usr/bin/env python3
import os
import subprocess
import logging
from datetime import datetime

# Configurações
BACKUP_DIR = "postgres/dumps/"
CONTAINER_NAME = ""
DB_USER = ""
DB_NAME = ""
BACKUP_EXTENSION = ".dump"
LAST_RUN_FILE = "backups_logs/last_backup_time.txt"
LOG_FILE = "backups_logs/backup.log"  # Arquivo de log
MAX_BACKUPS = 7
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"  # Formato ISO 8601

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_backup():
    today = datetime.now().strftime("%Y-%m-%d")
    backup_file = f"{BACKUP_DIR}/backup_{today}{BACKUP_EXTENSION}"

    if os.path.exists(backup_file):
        logger.info(f"Backup já existe para hoje: {backup_file}")
        return

    command = f"docker exec {CONTAINER_NAME} pg_dump -U {DB_USER} {DB_NAME} > {backup_file}"
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        subprocess.run(command, shell=True, check=True)
        logger.info(f"Backup criado: {backup_file}")
        update_last_run()
    except subprocess.CalledProcessError as e:
        logger.critical(f"Erro ao criar o backup: {e}")

def update_last_run():
    os.makedirs(os.path.dirname(LAST_RUN_FILE), exist_ok=True)
    with open(LAST_RUN_FILE, "w") as f:
        f.write(datetime.now().strftime(DATE_FORMAT))
    logger.info(f"Registro de última execução atualizado: {LAST_RUN_FILE}")

def was_backup_done_today():
    if not os.path.exists(LAST_RUN_FILE):
        logger.info("Nenhum registro de backup anterior encontrado.")
        return False
    with open(LAST_RUN_FILE, "r") as f:
        last_run = datetime.strptime(f.read().strip(), DATE_FORMAT)
    logger.info(f"Último backup realizado em: {last_run}")
    return last_run.date() == datetime.now().date()

def clean_old_backups():
    backup_files = [file for file in os.listdir(BACKUP_DIR) if file.endswith(BACKUP_EXTENSION)]
    backup_files.sort()
    while len(backup_files) > MAX_BACKUPS:
        file_to_remove = os.path.join(BACKUP_DIR, backup_files.pop(0))
        os.remove(file_to_remove)
        logger.info(f"Backup antigo removido: {file_to_remove}")

if __name__ == "__main__":
    if not was_backup_done_today():
        create_backup()
    else:
        logger.info("Backup já realizado hoje.")
    clean_old_backups()
