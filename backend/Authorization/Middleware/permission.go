package Middleware

import (
	"net/http"

	"github.com/alumasinde/jijenge/Auth/Middleware"
	"github.com/alumasinde/jijenge/Authorization/Services"
	"github.com/alumasinde/jijenge/Core/HTTP"
)

type PermissionMiddleware struct {
	Authz *Services.AuthorizationService
}

func NewPermissionMiddleware(authz *Services.AuthorizationService) *PermissionMiddleware {
	return &PermissionMiddleware{Authz: authz}
}

func (m *PermissionMiddleware) Require(permission string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		userID, ok := Middleware.UserID(r.Context())
		if !ok || userID == 0 {
			HTTP.ErrorResponse(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
			return
		}
		allowed, err := m.Authz.HasPermission(r.Context(), userID, permission)
		if err != nil {
			HTTP.ErrorResponse(w, http.StatusInternalServerError, "INTERNAL_SERVER_ERROR", "Unable to check permission")
			return
		}
		if !allowed {
			HTTP.ErrorResponse(w, http.StatusForbidden, "FORBIDDEN", "You do not have permission to perform this action")
			return
		}
		next.ServeHTTP(w, r)
	})
}
