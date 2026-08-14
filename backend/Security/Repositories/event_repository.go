package Repositories

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Core/Security"
	"github.com/alumasinde/jijenge/Security/Models"
)

type Repository interface {
	Record(context.Context, *Models.Event) error
}
type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }
func (r *MySQLRepository) Record(ctx context.Context, e *Models.Event) error {
	if e == nil || e.UserID == nil || e.EventType == "" || len(e.EventType) > 64 {
		return errors.New("invalid security event")
	}
	b, err := Security.GenerateToken(32)
	if err != nil {
		return err
	}
	e.PublicID = b[:26]
	res, err := r.DB.SQL.ExecContext(ctx, `INSERT INTO security_events(public_id,user_id,event_type,request_id,ip_address,user_agent,metadata,created_at) VALUES(?,?,?,?,?,?,?,?)`, e.PublicID, e.UserID, e.EventType, e.RequestID, e.IPAddress, e.UserAgent, e.Metadata, e.CreatedAt)
	if err != nil {
		return err
	}
	id, err := res.LastInsertId()
	e.ID = uint64(id)
	return err
}
