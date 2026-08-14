package Services

import (
	"context"
	"errors"
	"strings"

	"github.com/alumasinde/jijenge/Authorization/Models"
	"github.com/alumasinde/jijenge/Authorization/Repositories"
)

var (
	ErrInvalidPermission = errors.New("invalid permission")
	ErrInvalidRole       = errors.New("invalid role")
)

type AuthorizationService struct {
	Repo Repositories.AuthorizationRepository
}

func NewAuthorizationService(repo Repositories.AuthorizationRepository) *AuthorizationService {
	return &AuthorizationService{Repo: repo}
}

func (s *AuthorizationService) CreateRole(ctx context.Context, name, description string) (*Models.Role, error) {
	name = strings.TrimSpace(name)
	if name == "" || len(name) > 100 {
		return nil, ErrInvalidRole
	}
	role := &Models.Role{Name: name, Description: strings.TrimSpace(description)}
	if err := s.Repo.CreateRole(ctx, role); err != nil {
		return nil, err
	}
	return role, nil
}

func (s *AuthorizationService) CreatePermission(ctx context.Context, name, description string) (*Models.Permission, error) {
	name = strings.TrimSpace(name)
	if name == "" || len(name) > 150 || !strings.Contains(name, ".") {
		return nil, ErrInvalidPermission
	}
	p := &Models.Permission{Name: name, Description: strings.TrimSpace(description)}
	if err := s.Repo.CreatePermission(ctx, p); err != nil {
		return nil, err
	}
	return p, nil
}

func (s *AuthorizationService) AssignRole(ctx context.Context, userID, roleID uint64) error {
	if userID == 0 || roleID == 0 {
		return ErrInvalidRole
	}
	return s.Repo.AssignRole(ctx, userID, roleID)
}

func (s *AuthorizationService) RevokeRole(ctx context.Context, userID, roleID uint64) error {
	if userID == 0 || roleID == 0 {
		return ErrInvalidRole
	}
	return s.Repo.RevokeRole(ctx, userID, roleID)
}

func (s *AuthorizationService) GrantPermission(ctx context.Context, roleID, permissionID uint64) error {
	if roleID == 0 || permissionID == 0 {
		return ErrInvalidPermission
	}
	return s.Repo.GrantPermission(ctx, roleID, permissionID)
}

func (s *AuthorizationService) RevokePermission(ctx context.Context, roleID, permissionID uint64) error {
	if roleID == 0 || permissionID == 0 {
		return ErrInvalidPermission
	}
	return s.Repo.RevokePermission(ctx, roleID, permissionID)
}

func (s *AuthorizationService) HasPermission(ctx context.Context, userID uint64, permission string) (bool, error) {
	if userID == 0 || strings.TrimSpace(permission) == "" {
		return false, ErrInvalidPermission
	}
	return s.Repo.UserHasPermission(ctx, userID, permission)
}
