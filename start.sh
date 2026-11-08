#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
LAN_IP="${LAN_IP:-$(hostname -I 2>/dev/null | awk '{print $1}')}"
if [[ -z "${LAN_IP}" ]]; then
  LAN_IP="127.0.0.1"
fi

export DATABASE_URL="${DATABASE_URL:-sqlite:///${ROOT_DIR}/database/teacher_treasure.db}"
export JWT_SECRET="${JWT_SECRET:-dev-only-insecure-jwt-secret-change-before-production}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:5173,http://127.0.0.1:5173,http://${LAN_IP}:5173}"
export SEED_TEACHER_PASSWORD="${SEED_TEACHER_PASSWORD:-Teacher@123}"
export VITE_USE_MOCK="false"
export VITE_API_BASE_URL=""

log() {
  printf '\033[1;36m[课堂签到]\033[0m %s\n' "$*"
}

fail() {
  printf '\033[1;31m[课堂签到]\033[0m %s\n' "$*" >&2
  exit 1
}

install_python_deps() {
  local target="$1"
  local requirements="$2"
  if command -v uv >/dev/null 2>&1; then
    uv venv "${target}/.venv" --python "${PYTHON_BIN}" >/dev/null
    uv pip install --python "${target}/.venv/bin/python" -r "${requirements}" >/dev/null
  else
    "${PYTHON_BIN}" -m venv "${target}/.venv"
    "${target}/.venv/bin/pip" install -r "${requirements}" >/dev/null
  fi
}

if [[ ! -x database/.venv/bin/alembic ]]; then
  log "首次运行：安装数据库依赖..."
  install_python_deps "database" "database/requirements.txt"
fi

if [[ ! -x backend/.venv/bin/uvicorn ]]; then
  log "首次运行：安装后端依赖..."
  install_python_deps "backend" "backend/requirements.txt"
fi

if [[ ! -x frontend/node_modules/.bin/vite ]]; then
  log "首次运行：安装前端依赖..."
  (
    cd frontend
    npm install --package-lock=false --registry=https://registry.npmjs.org
  )
fi

log "初始化数据库并执行迁移..."
database/.venv/bin/alembic -c database/alembic.ini upgrade head
database/.venv/bin/python -m database.seeds.seed_teacher
database/.venv/bin/python -m database.seeds.seed_demo

BACKEND_LOG="$ROOT_DIR/backend/uvicorn.log"
log "启动后端..."
(
  cd backend
  PYTHONPATH="$ROOT_DIR" "$ROOT_DIR/backend/.venv/bin/uvicorn" \
    app.main:app --host 0.0.0.0 --port 8000
) >"${BACKEND_LOG}" 2>&1 &
BACKEND_PID=$!

cleanup() {
  if kill -0 "${BACKEND_PID}" 2>/dev/null; then
    kill "${BACKEND_PID}" 2>/dev/null || true
    wait "${BACKEND_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

log "等待后端就绪..."
READY=0
for _ in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 0.5
done

if [[ "${READY}" -ne 1 ]]; then
  tail -n 40 "${BACKEND_LOG}" || true
  fail "后端启动失败，请检查 ${BACKEND_LOG}"
fi

cat <<EOF

========================================
  课堂签到已启动（真实后端模式）
----------------------------------------
  本机访问:   http://localhost:5173
  手机访问:   http://${LAN_IP}:5173
  后端 API:   http://${LAN_IP}:8000

  教师账号:   teacher / Teacher@123
  学生账号:   20230001 / 20230001（首次登录需改密）
             20230002 / 20230002
  班长账号:   20230003 / 20230003

  手机需与电脑同一 Wi-Fi。
  若手机打不开，尝试：
  LAN_IP=<电脑局域网IP> ./start.sh

  Ctrl+C 同时停止前后端。
========================================

EOF

cd frontend
VITE_USE_MOCK=false VITE_API_BASE_URL="" \
  npm run dev -- --host 0.0.0.0 --port 5173