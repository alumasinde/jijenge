package Models

import "time"

type Permission struct {
	ID          uint64
	Name        string
	Description string
	CreatedAt   time.Time
}

type Role struct {
	ID          uint64
	Name        string
	Description string
	CreatedAt   time.Time
}

type UserRole struct {
	UserID    uint64
	RoleID    uint64
	CreatedAt time.Time
}

type RolePermission struct {
	RoleID       uint64
	PermissionID uint64
	CreatedAt    time.Time
}
