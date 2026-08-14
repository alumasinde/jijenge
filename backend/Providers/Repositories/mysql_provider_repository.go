package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Providers/Models"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }
func (r *MySQLRepository) UpsertProfile(ctx context.Context, p *Models.Profile) error {
	_, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO provider_profiles(user_id,display_name,bio,service_radius_km,verified,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE display_name=VALUES(display_name),bio=VALUES(bio),service_radius_km=VALUES(service_radius_km),verified=VALUES(verified),updated_at=VALUES(updated_at)`, p.UserID, p.DisplayName, p.Bio, p.ServiceRadiusKM, p.Verified, p.CreatedAt, p.UpdatedAt)
	return e
}
func (r *MySQLRepository) UpsertLocation(ctx context.Context, l *Models.Location) error {
	_, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO provider_locations(user_id,country,county,city,area,latitude,longitude,updated_at) VALUES(?,?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE country=VALUES(country),county=VALUES(county),city=VALUES(city),area=VALUES(area),latitude=VALUES(latitude),longitude=VALUES(longitude),updated_at=VALUES(updated_at)`, l.UserID, l.Country, l.County, l.City, l.Area, l.Latitude, l.Longitude, l.UpdatedAt)
	return e
}
func (r *MySQLRepository) FindProfile(ctx context.Context, id uint64) (*Models.Profile, error) {
	var p Models.Profile
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT user_id,display_name,bio,service_radius_km,verified,created_at,updated_at FROM provider_profiles WHERE user_id=?`, id).Scan(&p.UserID, &p.DisplayName, &p.Bio, &p.ServiceRadiusKM, &p.Verified, &p.CreatedAt, &p.UpdatedAt)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	if e != nil {
		return nil, e
	}
	return &p, nil
}
func (r *MySQLRepository) FindLocation(ctx context.Context, id uint64) (*Models.Location, error) {
	var l Models.Location
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT user_id,country,county,city,area,latitude,longitude,updated_at FROM provider_locations WHERE user_id=?`, id).Scan(&l.UserID, &l.Country, &l.County, &l.City, &l.Area, &l.Latitude, &l.Longitude, &l.UpdatedAt)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	if e != nil {
		return nil, e
	}
	return &l, nil
}
func (r *MySQLRepository) Nearby(ctx context.Context, lat, lon, radius float64) []Models.Location {
	rows, e := r.DB.SQL.QueryContext(ctx, `SELECT user_id,country,county,city,area,latitude,longitude,updated_at FROM provider_locations WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?`, lat-radius/111.0, lat+radius/111.0, lon-radius/111.0, lon+radius/111.0)
	if e != nil {
		return []Models.Location{}
	}
	defer rows.Close()
	out := []Models.Location{}
	for rows.Next() {
		var l Models.Location
		if e = rows.Scan(&l.UserID, &l.Country, &l.County, &l.City, &l.Area, &l.Latitude, &l.Longitude, &l.UpdatedAt); e == nil {
			out = append(out, l)
		}
	}
	return out
}

var _ Repository = (*MySQLRepository)(nil)
