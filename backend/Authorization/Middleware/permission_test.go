package Middleware

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	AuthMiddleware "github.com/alumasinde/jijenge/Auth/Middleware"
	"github.com/alumasinde/jijenge/Authorization/Repositories"
	"github.com/alumasinde/jijenge/Authorization/Services"
)

func TestPermissionMiddleware(t *testing.T) {
	repo := Repositories.NewMemoryAuthorizationRepository()
	authz := Services.NewAuthorizationService(repo)
	role, _ := authz.CreateRole(context.Background(), "employee", "")
	perm, _ := authz.CreatePermission(context.Background(), "tasks.read", "")
	_ = authz.AssignRole(context.Background(), 7, role.ID)
	_ = authz.GrantPermission(context.Background(), role.ID, perm.ID)

	handler := NewPermissionMiddleware(authz).Require("tasks.read",
		http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusNoContent) }))

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req = req.WithContext(context.WithValue(req.Context(), AuthMiddleware.UserIDKey, uint64(7)))
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)
	if rec.Code != http.StatusNoContent {
		t.Fatalf("expected 204, got %d", rec.Code)
	}

	req2 := httptest.NewRequest(http.MethodGet, "/", nil)
	req2 = req2.WithContext(context.WithValue(req2.Context(), AuthMiddleware.UserIDKey, uint64(8)))
	rec2 := httptest.NewRecorder()
	handler.ServeHTTP(rec2, req2)
	if rec2.Code != http.StatusForbidden {
		t.Fatalf("expected 403, got %d", rec2.Code)
	}
}
