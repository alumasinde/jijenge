package Models

import (
	"crypto/sha256"
	"encoding/hex"
	"strings"
)

func EventHash(e *AuditEvent, previous string) string {
	actor := ""
	if e.ActorUserID != nil {
		actor = uintString(*e.ActorUserID)
	}
	payload := strings.Join([]string{
		previous, e.PublicID, actor, e.Action, e.ResourceType, e.ResourceID,
		e.RequestID, e.IPAddress, e.UserAgent, e.Outcome, e.Reason, e.Metadata,
		e.CreatedAt.UTC().Format("2006-01-02T15:04:05.999999Z07:00"),
	}, "\x1f")
	sum := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(sum[:])
}
func uintString(v uint64) string {
	if v == 0 {
		return "0"
	}
	var b [20]byte
	i := len(b)
	for v > 0 {
		i--
		b[i] = byte('0' + v%10)
		v /= 10
	}
	return string(b[i:])
}
