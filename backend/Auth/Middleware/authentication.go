package Middleware

import (
	"context"
	"net/http"

	"github.com/alumasinde/jijenge/Auth/Services"
	"github.com/alumasinde/jijenge/Core/HTTP"
	"github.com/alumasinde/jijenge/Core/Security"
)

type contextKey string

const (
	UserIDKey contextKey = "user_id"
)

type Authenticator struct {
	Service *Services.AuthService
}

func (a *Authenticator) Require(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token, err := Security.BearerToken(r)
		if err != nil {
			HTTP.ErrorResponse(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
			return
		}

		user, session, err := a.Service.AuthenticateAccessToken(r.Context(), token)
		if err != nil {
			HTTP.ErrorResponse(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
			return
		}

		ctx := context.WithValue(r.Context(), UserIDKey, user.ID)
		ctx = context.WithValue(ctx, Security.AccessTokenKey, token)
		_ = session
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func UserID(ctx context.Context) (uint64, bool) {
	value, ok := ctx.Value(UserIDKey).(uint64)
	return value, ok
}
