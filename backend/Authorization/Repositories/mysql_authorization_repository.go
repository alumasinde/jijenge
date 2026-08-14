package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"strings"

	"github.com/alumasinde/jijenge/Authorization/Models"
	"github.com/alumasinde/jijenge/Core/Database"
)

type MySQLAuthorizationRepository struct{ DB *Database.DB }

func NewMySQLAuthorizationRepository(db *Database.DB) *MySQLAuthorizationRepository {
	return &MySQLAuthorizationRepository{DB: db}
}

func (r *MySQLAuthorizationRepository) CreateRole(ctx context.Context, role *Models.Role) error {
	res, err := r.DB.SQL.ExecContext(ctx, `INSERT INTO roles (name, description) VALUES (?, ?)`, role.Name, role.Description)
	if err != nil {
		if strings.Contains(strings.ToLower(err.Error()), "duplicate") {
			return ErrRoleExists
		}
		return err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return err
	}
	role.ID = uint64(id)
	return nil
}

func (r *MySQLAuthorizationRepository) CreatePermission(ctx context.Context, p *Models.Permission) error {
	res, err := r.DB.SQL.ExecContext(ctx, `INSERT INTO permissions (name, description) VALUES (?, ?)`, p.Name, p.Description)
	if err != nil {
		if strings.Contains(strings.ToLower(err.Error()), "duplicate") {
			return ErrPermissionExists
		}
		return err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return err
	}
	p.ID = uint64(id)
	return nil
}

func (r *MySQLAuthorizationRepository) AssignRole(ctx context.Context, userID, roleID uint64) error {
	_, err := r.DB.SQL.ExecContext(ctx, `INSERT IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)`, userID, roleID)
	return err
}

func (r *MySQLAuthorizationRepository) RevokeRole(ctx context.Context, userID, roleID uint64) error {
	_, err := r.DB.SQL.ExecContext(ctx, `DELETE FROM user_roles WHERE user_id = ? AND role_id = ?`, userID, roleID)
	return err
}

func (r *MySQLAuthorizationRepository) GrantPermission(ctx context.Context, roleID, permissionID uint64) error {
	_, err := r.DB.SQL.ExecContext(ctx, `INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)`, roleID, permissionID)
	return err
}

func (r *MySQLAuthorizationRepository) RevokePermission(ctx context.Context, roleID, permissionID uint64) error {
	_, err := r.DB.SQL.ExecContext(ctx, `DELETE FROM role_permissions WHERE role_id = ? AND permission_id = ?`, roleID, permissionID)
	return err
}

func (r *MySQLAuthorizationRepository) UserHasPermission(ctx context.Context, userID uint64, permission string) (bool, error) {
	var one int
	err := r.DB.SQL.QueryRowContext(ctx, `
SELECT 1
FROM user_roles ur
JOIN role_permissions rp ON rp.role_id = ur.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE ur.user_id = ? AND p.name = ?
LIMIT 1`, userID, permission).Scan(&one)
	if errors.Is(err, sql.ErrNoRows) {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	return true, nil
}

func (r *MySQLAuthorizationRepository) UserRoles(ctx context.Context, userID uint64) ([]Models.Role, error) {
	rows, err := r.DB.SQL.QueryContext(ctx, `
SELECT r.id, r.name, r.description, r.created_at
FROM roles r
JOIN user_roles ur ON ur.role_id = r.id
WHERE ur.user_id = ?
ORDER BY r.name`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var roles []Models.Role
	for rows.Next() {
		var role Models.Role
		if err := rows.Scan(&role.ID, &role.Name, &role.Description, &role.CreatedAt); err != nil {
			return nil, err
		}
		roles = append(roles, role)
	}
	return roles, rows.Err()
}
