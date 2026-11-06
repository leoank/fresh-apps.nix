#!/usr/bin/env bash
# Rolling alert issues for the update pipeline, after neusis's
# .github/scripts/alert.sh.
#
#   alert.sh failed|ok TITLE BODY
#
# failed  comments on the open issue titled TITLE, or opens it and sends
#         the email, so a failure that persists mails once, not every run.
# ok      closes that issue, if open, with BODY as the last comment.
#
# Needs GH_TOKEN (issues: write) and GH_REPO. The email goes through
# Postmark and needs POSTMARK_API_KEY, ALERT_FROM and ALERT_TO; without
# the key the issue is still opened and the email is skipped.
set -euo pipefail

[ $# -eq 3 ] || {
  echo "usage: alert.sh failed|ok TITLE BODY" >&2
  exit 2
}
state=$1
title=$2
body=$3
label=ci-alert

email() {
  if [ -z "${POSTMARK_API_KEY:-}" ]; then
    echo "::warning::POSTMARK_API_KEY is not set; no email sent"
    return 0
  fi
  jq -n --arg from "$ALERT_FROM" --arg to "$ALERT_TO" \
    --arg subject "$title" --arg text "$body" \
    '{From: "fresh-apps <\($from)>", To: $to, Subject: $subject,
      TextBody: $text, MessageStream: "outbound"}' |
    curl -fsS --max-time 30 -o /dev/null \
      -H "X-Postmark-Server-Token: $POSTMARK_API_KEY" \
      -H "Accept: application/json" -H "Content-Type: application/json" \
      --data-binary @- https://api.postmarkapp.com/email
}

gh label create "$label" --force --color B60205 \
  --description "CI alerts (update pipeline)" >/dev/null
num=$(gh issue list --label "$label" --state open --limit 100 --json number,title |
  jq -r --arg t "$title" 'first(.[] | select(.title == $t) | .number) // empty')

case "$state" in
failed)
  if [ -n "$num" ]; then
    gh issue comment "$num" --body "$body"
  else
    gh issue create --title "$title" --label "$label" --body "$body"
    email
  fi
  ;;
ok)
  if [ -n "$num" ]; then
    gh issue close "$num" --comment "Recovered: $body"
  fi
  ;;
*)
  echo "usage: alert.sh failed|ok TITLE BODY" >&2
  exit 2
  ;;
esac
