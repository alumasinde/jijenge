package Repositories

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/alumasinde/jijenge/Authorization/Models"
)

var (
	ErrRoleNotFound       = errors.New("role not found")
	ErrPermissionNotFound = errors.New("permission not found")
	ErrRoleExists         = errors.New("role already exists")
	ErrPermissionExists   = errors.New("permission already exists")
)

type AuthorizationRepository interface {
	CreateRole(ctx context.Context, role *Models.Role) error
	CreatePermission(ctx context.Context, permission *Models.Permission) error
	AssignRole(ctx context.Context, userID, roleID uint64) error
	RevokeRole(ctx context.Context, userID, roleID uint64) error
	GrantPermission(ctx context.Context, roleID, permissionID uint64) error
	RevokePermission(ctx context.Context, roleID, permissionID uint64) error
	UserHasPermission(ctx context.Context, userID uint64, permission string) (bool, error)
	UserRoles(ctx context.Context, userID uint64) ([]Models.Role, error)
}

type MemoryAuthorizationRepository struct {
	mu               sync.RWMutex
	nextRoleID       uint64
	nextPermissionID uint64
	roles            map[uint64]Models.Role
	permissions      map[uint64]Models.Permission
	userRoles        map[uint64]map[uint64]struct{}
	rolePermissions  map[uint64]map[uint64]struct{}
}

func NewMemoryAuthorizationRepository() *MemoryAuthorizationRepository {
	return &MemoryAuthorizationRepository{
		nextRoleID:       1,
		nextPermissionID: 1,
		roles:            make(map[uint64]Models.Role),
		permissions:      make(map[uint64]Models.Permission),
		userRoles:        make(map[uint64]map[uint64]struct{}),
		rolePermissions:  make(map[uint64]map[uint64]struct{}),
	}
}

func (r *MemoryAuthorizationRepository) CreateRole(ctx context.Context, role *Models.Role) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, existing := range r.roles {
		if existing.Name == role.Name {
			return ErrRoleExists
		}
	}
	role.ID = r.nextRoleID
	r.nextRoleID++
	if role.CreatedAt.IsZero() {
		role.CreatedAt = time.Now()
	}
	r.roles[role.ID] = *role
	return nil
}

func (r *MemoryAuthorizationRepository) CreatePermission(ctx context.Context, p *Models.Permission) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, existing := range r.permissions {
		if existing.Name == p.Name {
			return ErrPermissionExists
		}
	}
	p.ID = r.nextPermissionID
	r.nextPermissionID++
	if p.CreatedAt.IsZero() {
		p.CreatedAt = time.Now()
	}
	r.permissions[p.ID] = *p
	return nil
}

func (r *MemoryAuthorizationRepository) AssignRole(ctx context.Context, userID, roleID uint64) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.roles[roleID]; !ok {
		return ErrRoleNotFound
	}
	if r.userRoles[userID] == nil {
		r.userRoles[userID] = make(map[uint64]struct{})
	}
	r.userRoles[userID][roleID] = struct{}{}
	return nil
}

func (r *MemoryAuthorizationRepository) RevokeRole(ctx context.Context, userID, roleID uint64) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.roles[roleID]; !ok {
		return ErrRoleNotFound
	}
	if roles := r.userRoles[userID]; roles != nil {
		delete(roles, roleID)
	}
	return nil
}

func (r *MemoryAuthorizationRepository) GrantPermission(ctx context.Context, roleID, permissionID uint64) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.roles[roleID]; !ok {
		return ErrRoleNotFound
	}
	if _, ok := r.permissions[permissionID]; !ok {
		return ErrPermissionNotFound
	}
	if r.rolePermissions[roleID] == nil {
		r.rolePermissions[roleID] = make(map[uint64]struct{})
	}
	r.rolePermissions[roleID][permissionID] = struct{}{}
	return nil
}

func (r *MemoryAuthorizationRepository) RevokePermission(ctx context.Context, roleID, permissionID uint64) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.roles[roleID]; !ok {
		return ErrRoleNotFound
	}
	if permissions := r.rolePermissions[roleID]; permissions != nil {
		delete(permissions, permissionID)
	}
	return nil
}

func (r *MemoryAuthorizationRepository) UserHasPermission(ctx context.Context, userID uint64, permission string) (bool, error) {
	if err := ctx.Err(); err != nil {
		return false, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	for roleID := range r.userRoles[userID] {
		for permissionID := range r.rolePermissions[roleID] {
			if p, ok := r.permissions[permissionID]; ok && p.Name == permission {
				return true, nil
			}
		}
	}
	return false, nil
}

func (r *MemoryAuthorizationRepository) UserRoles(ctx context.Context, userID uint64) ([]Models.Role, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	var result []Models.Role
	for roleID := range r.userRoles[userID] {
		if role, ok := r.roles[roleID]; ok {
			result = append(result, role)
		}
	}
	return result, nil
}
