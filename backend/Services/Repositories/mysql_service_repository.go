package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Services/Models"
	"strings"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }
func (r *MySQLRepository) CreateCategory(ctx context.Context, c *Models.Category) error {
	res, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO service_categories(name,slug,parent_id) VALUES(?,?,?)`, c.Name, c.Slug, c.ParentID)
	if e != nil {
		return e
	}
	id, e := res.LastInsertId()
	c.ID = uint64(id)
	return e
}
func (r *MySQLRepository) Create(ctx context.Context, s *Models.Service) error {
	res, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO service_listings(public_id,provider_user_id,category_id,title,description,starting_price_cents,currency,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)`, s.PublicID, s.ProviderUserID, s.CategoryID, s.Title, s.Description, s.StartingPriceCents, s.Currency, s.Status, s.CreatedAt, s.UpdatedAt)
	if e != nil {
		return e
	}
	id, e := res.LastInsertId()
	s.ID = uint64(id)
	return e
}
func (r *MySQLRepository) Find(ctx context.Context, id uint64) (*Models.Service, error) {
	var s Models.Service
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT id,public_id,provider_user_id,category_id,title,description,currency,starting_price_cents,status,created_at,updated_at FROM service_listings WHERE id=?`, id).Scan(&s.ID, &s.PublicID, &s.ProviderUserID, &s.CategoryID, &s.Title, &s.Description, &s.Currency, &s.StartingPriceCents, &s.Status, &s.CreatedAt, &s.UpdatedAt)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	if e != nil {
		return nil, e
	}
	return &s, nil
}
func (r *MySQLRepository) ListByCategory(ctx context.Context, id uint64) []*Models.Service {
	rows, e := r.DB.SQL.QueryContext(ctx, `SELECT id,public_id,provider_user_id,category_id,title,description,currency,starting_price_cents,status,created_at,updated_at FROM service_listings WHERE category_id=? AND status='active' ORDER BY created_at DESC`, id)
	if e != nil {
		return []*Models.Service{}
	}
	defer rows.Close()
	out := []*Models.Service{}
	for rows.Next() {
		var s Models.Service
		if e = rows.Scan(&s.ID, &s.PublicID, &s.ProviderUserID, &s.CategoryID, &s.Title, &s.Description, &s.Currency, &s.StartingPriceCents, &s.Status, &s.CreatedAt, &s.UpdatedAt); e == nil {
			out = append(out, &s)
		}
	}
	return out
}
func _(_ string) { _ = strings.TrimSpace("") }

var _ Repository = (*MySQLRepository)(nil)
