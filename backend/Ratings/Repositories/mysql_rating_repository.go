package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Ratings/Models"
	"strings"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }
func (r *MySQLRepository) Create(ctx context.Context, x *Models.Rating) error {
	if x == nil || x.AssignmentID == 0 || x.ReviewerUserID == 0 || x.RevieweeUserID == 0 || x.ReviewerUserID == x.RevieweeUserID || x.Score < 1 || x.Score > 5 {
		return ErrInvalid
	}
	var owner, worker uint64
	var status string
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT t.owner_user_id,a.worker_user_id,a.status FROM task_assignments a JOIN tasks t ON t.id=a.task_id WHERE a.id=?`, x.AssignmentID).Scan(&owner, &worker, &status)
	if errors.Is(e, sql.ErrNoRows) {
		return ErrInvalid
	}
	if e != nil {
		return e
	}
	if status != "verified" || !((x.ReviewerUserID == owner && x.RevieweeUserID == worker) || (x.ReviewerUserID == worker && x.RevieweeUserID == owner)) {
		return ErrInvalid
	}
	res, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO ratings(assignment_id,reviewer_user_id,reviewee_user_id,score,comment,status,created_at) VALUES(?,?,?,?,?,?,?)`, x.AssignmentID, x.ReviewerUserID, x.RevieweeUserID, x.Score, x.Comment, x.Status, x.CreatedAt)
	if e != nil {
		if strings.Contains(strings.ToLower(e.Error()), "duplicate") {
			return ErrDuplicate
		}
		return e
	}
	id, e := res.LastInsertId()
	x.ID = uint64(id)
	return e
}
func (r *MySQLRepository) Average(ctx context.Context, user uint64) (float64, int, error) {
	var avg sql.NullFloat64
	var n int
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT AVG(score),COUNT(*) FROM ratings WHERE reviewee_user_id=? AND status='published'`, user).Scan(&avg, &n)
	if e != nil {
		return 0, 0, e
	}
	if !avg.Valid {
		return 0, 0, nil
	}
	return avg.Float64, n, nil
}
func _(_ string) { _ = strings.TrimSpace("") }

var _ = errors.Is
var _ *Database.DB

var _ Repository = (*MySQLRepository)(nil)
