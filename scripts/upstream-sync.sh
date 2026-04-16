#!/bin/bash
# Kaven upstream 자동 동기화 스크립트
# 매주 일요일 실행 — upstream(avlp12/kaven) 변경사항을 머지하고 fork에 push
#
# 충돌 발생 시 머지를 중단하고 텔레그램으로 알림

set -euo pipefail

REPO_DIR="/Users/skaya/Project/kaven"
LOG_FILE="$HOME/Library/Logs/kaven-sync.log"
KAVEN_PLIST="$HOME/Library/LaunchAgents/com.skaya.kaven.plist"

# 텔레그램 알림 (kaven .env에서 읽기)
source "$REPO_DIR/src/kaven/.env" 2>/dev/null || true
BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"
TOPIC_ID="5052"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

notify() {
    local message="$1"
    if [[ -n "$BOT_TOKEN" && -n "$CHAT_ID" ]]; then
        curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
            -d "chat_id=${CHAT_ID}" \
            -d "message_thread_id=${TOPIC_ID}" \
            -d "text=${message}" \
            -d "parse_mode=Markdown" >/dev/null 2>&1 || true
    fi
}

cd "$REPO_DIR"

log "=== Upstream 동기화 시작 ==="

# 1. upstream fetch
log "upstream fetch 중..."
git fetch upstream 2>&1 | tee -a "$LOG_FILE"

# 2. 새 커밋 확인
NEW_COMMITS=$(git log HEAD..upstream/main --oneline 2>/dev/null)
if [[ -z "$NEW_COMMITS" ]]; then
    log "upstream 변경 없음 — 동기화 스킵"
    log "=== 동기화 완료 (변경 없음) ==="
    exit 0
fi

COMMIT_COUNT=$(echo "$NEW_COMMITS" | wc -l | tr -d ' ')
log "upstream 새 커밋 ${COMMIT_COUNT}건 감지:"
echo "$NEW_COMMITS" | head -10 | tee -a "$LOG_FILE"

# 3. 로컬 변경 확인 — dirty 상태면 중단
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    log "ERROR: 커밋되지 않은 로컬 변경 있음 — 머지 중단"
    notify "⚠️ *Kaven Sync 실패*: 커밋되지 않은 로컬 변경이 있어 upstream 머지를 건너뜀"
    exit 1
fi

# 4. kaven 데몬 중지 (머지 중 코드 변경 방지)
log "kaven 데몬 일시 중지..."
launchctl bootout "gui/$(id -u)" "$KAVEN_PLIST" 2>/dev/null || true
sleep 2

# 5. 머지 시도
log "upstream/main 머지 시도..."
if git merge upstream/main --no-edit 2>&1 | tee -a "$LOG_FILE"; then
    log "머지 성공"

    # 6. fork에 push
    log "origin(fork)에 push..."
    git push origin main 2>&1 | tee -a "$LOG_FILE"
    log "push 완료"

    notify "✅ *Kaven Upstream Sync*
새 커밋 ${COMMIT_COUNT}건 머지 완료
\`\`\`
$(echo "$NEW_COMMITS" | head -5)
\`\`\`"
else
    # 충돌 발생 — 머지 중단
    log "ERROR: 머지 충돌 발생 — 수동 해결 필요"
    git merge --abort 2>/dev/null || true

    CONFLICT_SUMMARY=$(echo "$NEW_COMMITS" | head -3)
    notify "🔴 *Kaven Upstream Sync 충돌*
수동 머지 필요 (${COMMIT_COUNT}건 커밋)
\`\`\`
${CONFLICT_SUMMARY}
\`\`\`
\`cd ~/Project/kaven && git merge upstream/main\`"
fi

# 7. kaven 데몬 재시작
log "kaven 데몬 재시작..."
launchctl bootstrap "gui/$(id -u)" "$KAVEN_PLIST" 2>/dev/null || true
sleep 2

if launchctl list 2>/dev/null | grep -q "com.skaya.kaven"; then
    log "kaven 데몬 재시작 완료"
else
    log "WARNING: kaven 데몬 재시작 실패"
    notify "⚠️ Kaven 데몬 재시작 실패 — 수동 확인 필요"
fi

log "=== 동기화 완료 ==="
