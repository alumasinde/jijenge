package Security

import (
	"context"
	"errors"
	"net/http"
	"strings"
)

type AccessTokenContextKey string

const AccessTokenKey AccessTokenContextKey = "access_token"

var ErrMissingBearerToken = errors.New("missing bearer token")

func BearerToken(r *http.Request) (string, error) {
	value := strings.TrimSpace(r.Header.Get("Authorization"))
	if value == "" {
		return "", ErrMissingBearerToken
	}
	parts := strings.Fields(value)
	if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") || parts[1] == "" {
		return "", ErrMissingBearerToken
	}
	return parts[1], nil
}

func WithAccessToken(ctx context.Context, token string) context.Context {
	return context.WithValue(ctx, AccessTokenKey, token)
}

func AccessTokenFromContext(ctx context.Context) (string, bool) {
	value, ok := ctx.Value(AccessTokenKey).(string)
	return value, ok
}
