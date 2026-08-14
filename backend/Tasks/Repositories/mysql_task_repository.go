package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Tasks/Models"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }

func (r *MySQLRepository) CreateCategory(ctx context.Context, c *Models.Category) error {
	res, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO task_categories(name,slug) VALUES(?,?)`, c.Name, c.Slug)
	if e != nil {
		return e
	}
	id, e := res.LastInsertId()
	c.ID = uint64(id)
	return e
}
func (r *MySQLRepository) FindCategory(ctx context.Context, id uint64) (*Models.Category, error) {
	var c Models.Category
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT id,name,slug FROM task_categories WHERE id=?`, id).Scan(&c.ID, &c.Name, &c.Slug)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, ErrCategoryNotFound
	}
	if e != nil {
		return nil, e
	}
	return &c, nil
}
func (r *MySQLRepository) CreateTask(ctx context.Context, t *Models.Task) error {
	res, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO tasks(public_id,owner_user_id,category_id,title,description,budget_cents,currency,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)`, t.PublicID, t.OwnerUserID, t.CategoryID, t.Title, t.Description, t.BudgetCents, t.Currency, t.Status, t.CreatedAt, t.UpdatedAt)
	if e != nil {
		return e
	}
	id, e := res.LastInsertId()
	t.ID = uint64(id)
	return e
}
func (r *MySQLRepository) FindTask(ctx context.Context, id uint64) (*Models.Task, error) {
	var t Models.Task
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT id,public_id,owner_user_id,category_id,title,description,budget_cents,currency,status,created_at,updated_at FROM tasks WHERE id=?`, id).Scan(&t.ID, &t.PublicID, &t.OwnerUserID, &t.CategoryID, &t.Title, &t.Description, &t.BudgetCents, &t.Currency, &t.Status, &t.CreatedAt, &t.UpdatedAt)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, ErrTaskNotFound
	}
	if e != nil {
		return nil, e
	}
	return &t, nil
}
func (r *MySQLRepository) UpdateTaskStatus(ctx context.Context, id uint64, f, t Models.TaskStatus) error {
	if !validTaskTransition(f, t) {
		return ErrInvalidStateTransition
	}
	res, e := r.DB.SQL.ExecContext(ctx, `UPDATE tasks SET status=?,updated_at=CURRENT_TIMESTAMP(6) WHERE id=? AND status=?`, t, id, f)
	if e != nil {
		return e
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return ErrInvalidStateTransition
	}
	return nil
}
func (r *MySQLRepository) CreateApplication(ctx context.Context, a *Models.Application) error {
	res, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO task_applications(task_id,applicant_user_id,message,proposed_cents,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)`, a.TaskID, a.ApplicantID, a.Message, a.ProposedCents, a.Status, a.CreatedAt, a.UpdatedAt)
	if e != nil {
		if strings.Contains(strings.ToLower(e.Error()), "duplicate") {
			return ErrDuplicateApplication
		}
		return e
	}
	id, e := res.LastInsertId()
	a.ID = uint64(id)
	return e
}
func (r *MySQLRepository) FindApplication(ctx context.Context, id uint64) (*Models.Application, error) {
	var a Models.Application
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT id,task_id,applicant_user_id,message,proposed_cents,status,created_at,updated_at FROM task_applications WHERE id=?`, id).Scan(&a.ID, &a.TaskID, &a.ApplicantID, &a.Message, &a.ProposedCents, &a.Status, &a.CreatedAt, &a.UpdatedAt)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, ErrApplicationNotFound
	}
	if e != nil {
		return nil, e
	}
	return &a, nil
}
func (r *MySQLRepository) UpdateApplicationStatus(ctx context.Context, id uint64, f, t Models.ApplicationStatus) error {
	res, e := r.DB.SQL.ExecContext(ctx, `UPDATE task_applications SET status=?,updated_at=CURRENT_TIMESTAMP(6) WHERE id=? AND status=?`, t, id, f)
	if e != nil {
		return e
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return ErrInvalidStateTransition
	}
	return nil
}
func (r *MySQLRepository) CreateAssignment(ctx context.Context, a *Models.Assignment) error {
	res, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO task_assignments(task_id,application_id,worker_user_id,assigned_by_user_id,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)`, a.TaskID, a.ApplicationID, a.WorkerID, a.AssignedBy, a.Status, a.CreatedAt, a.UpdatedAt)
	if e != nil {
		if strings.Contains(strings.ToLower(e.Error()), "duplicate") {
			return ErrAssignmentExists
		}
		return e
	}
	id, e := res.LastInsertId()
	a.ID = uint64(id)
	return e
}
func (r *MySQLRepository) FindAssignment(ctx context.Context, id uint64) (*Models.Assignment, error) {
	var a Models.Assignment
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT id,task_id,application_id,worker_user_id,assigned_by_user_id,status,submitted_at,verified_at,created_at,updated_at FROM task_assignments WHERE id=?`, id).Scan(&a.ID, &a.TaskID, &a.ApplicationID, &a.WorkerID, &a.AssignedBy, &a.Status, &a.SubmittedAt, &a.VerifiedAt, &a.CreatedAt, &a.UpdatedAt)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, ErrAssignmentNotFound
	}
	if e != nil {
		return nil, e
	}
	return &a, nil
}
func (r *MySQLRepository) UpdateAssignmentStatus(ctx context.Context, id uint64, f, t Models.AssignmentStatus, at time.Time) error {
	var q string
	var args []any
	switch t {
	case Models.AssignmentSubmitted:
		q = `UPDATE task_assignments SET status=?,submitted_at=?,updated_at=? WHERE id=? AND status=?`
		args = []any{t, at, at, id, f}
	case Models.AssignmentVerified:
		q = `UPDATE task_assignments SET status=?,verified_at=?,updated_at=? WHERE id=? AND status=?`
		args = []any{t, at, at, id, f}
	default:
		q = `UPDATE task_assignments SET status=?,updated_at=? WHERE id=? AND status=?`
		args = []any{t, at, id, f}
	}
	res, e := r.DB.SQL.ExecContext(ctx, q, args...)
	if e != nil {
		return e
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return ErrInvalidStateTransition
	}
	return nil
}

func (r *MySQLRepository) AcceptApplicationAndAssign(ctx context.Context, ownerID, applicationID uint64, now time.Time) (*Models.Assignment, error) {
	var out Models.Assignment
	err := Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var taskID, taskOwner uint64
		var taskStatus Models.TaskStatus
		e := Database.QueryRowForUpdate(tx, `SELECT id,owner_user_id,status FROM tasks WHERE id=(SELECT task_id FROM task_applications WHERE id=?)`, applicationID).Scan(&taskID, &taskOwner, &taskStatus)
		if errors.Is(e, sql.ErrNoRows) {
			return ErrApplicationNotFound
		}
		if e != nil {
			return e
		}
		if taskOwner != ownerID {
			return ErrForbidden
		}
		if taskStatus != Models.StatusPublished {
			return ErrInvalidStateTransition
		}
		var appTask, applicant uint64
		var appStatus Models.ApplicationStatus
		e = Database.QueryRowForUpdate(tx, `SELECT task_id,applicant_user_id,status FROM task_applications WHERE id=?`, applicationID).Scan(&appTask, &applicant, &appStatus)
		if errors.Is(e, sql.ErrNoRows) {
			return ErrApplicationNotFound
		}
		if e != nil {
			return e
		}
		if appTask != taskID || appStatus != Models.ApplicationPending {
			return ErrInvalidStateTransition
		}
		var existing uint64
		e = tx.QueryRow(`SELECT id FROM task_assignments WHERE task_id=? LIMIT 1 FOR UPDATE`, taskID).Scan(&existing)
		if e == nil {
			return ErrTaskAlreadyAssigned
		}
		if !errors.Is(e, sql.ErrNoRows) {
			return e
		}
		res, e := tx.Exec(`UPDATE task_applications SET status=?,updated_at=? WHERE id=? AND status=?`, Models.ApplicationAccepted, now, applicationID, Models.ApplicationPending)
		if e != nil {
			return e
		}
		n, _ := res.RowsAffected()
		if n != 1 {
			return ErrInvalidStateTransition
		}
		res, e = tx.Exec(`INSERT INTO task_assignments(task_id,application_id,worker_user_id,assigned_by_user_id,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)`, taskID, applicationID, applicant, ownerID, Models.AssignmentAssigned, now, now)
		if e != nil {
			return e
		}
		id, e := res.LastInsertId()
		if e != nil {
			return e
		}
		out = Models.Assignment{ID: uint64(id), TaskID: taskID, ApplicationID: applicationID, WorkerID: applicant, AssignedBy: ownerID, Status: Models.AssignmentAssigned, CreatedAt: now, UpdatedAt: now}
		_, e = tx.Exec(`INSERT INTO task_events(task_id,actor_user_id,event_type,from_status,to_status,metadata,created_at) VALUES(?,?,?,?,?,?,?)`, taskID, ownerID, "application_accepted_assignment_created", Models.ApplicationPending, Models.ApplicationAccepted, fmt.Sprintf(`{"application_id":%d,"assignment_id":%d}`, applicationID, id), now)
		return e
	})
	if err != nil {
		return nil, err
	}
	return &out, nil
}
