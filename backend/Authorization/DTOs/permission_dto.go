package DTOs

type PermissionDTO struct {
	ID          uint64 `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
}

type RoleDTO struct {
	ID          uint64          `json:"id"`
	Name        string          `json:"name"`
	Description string          `json:"description,omitempty"`
	Permissions []PermissionDTO `json:"permissions,omitempty"`
}
