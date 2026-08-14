package Services

import (
	"context"
	"testing"

	"github.com/alumasinde/jijenge/Authorization/Repositories"
)

func TestAuthorizationFlow(t *testing.T) {
	repo := Repositories.NewMemoryAuthorizationRepository()
	svc := NewAuthorizationService(repo)
	ctx := context.Background()

	role, err := svc.CreateRole(ctx, "employee", "Standard employee")
	if err != nil {
		t.Fatal(err)
	}
	permission, err := svc.CreatePermission(ctx, "tasks.read", "Read tasks")
	if err != nil {
		t.Fatal(err)
	}

	if err := svc.AssignRole(ctx, 42, role.ID); err != nil {
		t.Fatal(err)
	}
	if err := svc.GrantPermission(ctx, role.ID, permission.ID); err != nil {
		t.Fatal(err)
	}

	ok, err := svc.HasPermission(ctx, 42, "tasks.read")
	if err != nil || !ok {
		t.Fatalf("expected permission, got %v %v", ok, err)
	}

	if err := svc.RevokePermission(ctx, role.ID, permission.ID); err != nil {
		t.Fatal(err)
	}
	ok, err = svc.HasPermission(ctx, 42, "tasks.read")
	if err != nil || ok {
		t.Fatalf("expected permission revoked, got %v %v", ok, err)
	}
}

func TestPermissionNameMustBeScoped(t *testing.T) {
	svc := NewAuthorizationService(Repositories.NewMemoryAuthorizationRepository())
	if _, err := svc.CreatePermission(context.Background(), "read", "bad"); err == nil {
		t.Fatal("expected invalid permission")
	}
}
