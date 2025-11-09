#!/usr/bin/env bash
set -e

# Путь к Alembic (при необходимости измените)
ALEMBIC_CMD="uv run alembic"
VERSIONS_DIR="alembic/versions"

echo "Проверяем наличие изменений в моделях и пытаемся сгенерировать ревизию..."

# Генерируем ревизию (даже если изменений нет, файл будет создан)
${ALEMBIC_CMD} revision --autogenerate -m "auto-$(date +%Y%m%d%H%M%S)" || true

# Находим самый недавно созданный файл в папке с ревизиями
LATEST_FILE=$(ls -1t ${VERSIONS_DIR}/*.py 2>/dev/null | head -n1 || echo "")

# Проверяем, был ли найден файл
if [ -z "${LATEST_FILE}" ]; then
  echo "Файлы миграций не найдены. Выполняем upgrade head..."
  ${ALEMBIC_CMD} upgrade head
elif [ -f "${LATEST_FILE}" ] && grep -q "op\." "${LATEST_FILE}"; then
  echo "Изменения в схеме обнаружены (файл: ${LATEST_FILE}). Выполняем миграцию..."
  ${ALEMBIC_CMD} upgrade head
else
  echo "Изменений в схеме не найдено. Удаляем пустой файл миграции ${LATEST_FILE}..."
  rm "${LATEST_FILE}"
  echo "Выполняем просто upgrade head..."
  ${ALEMBIC_CMD} upgrade head
fi

# Запускаем основное приложение
echo "Запускаем приложение..."
uv run -m src.main
