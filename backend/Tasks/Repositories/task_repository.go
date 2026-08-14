package Repositories

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/alumasinde/jijenge/Tasks/Models"
)

var (
	ErrTaskNotFound           = errors.New("task not found")
	ErrCategoryNotFound       = errors.New("category not found")
	ErrApplicationNotFound    = errors.New("application not found")
	ErrAssignmentNotFound     = errors.New("assignment not found")
	ErrAssignmentExists       = errors.New("assignment already exists")
	ErrTaskAlreadyAssigned    = errors.New("task already assigned")
	ErrDuplicateApplication   = errors.New("application already exists")
	ErrInvalidStateTransition = errors.New("invalid state transition")
	ErrForbidden              = errors.New("forbidden")
)

type TaskRepository interface {
	CreateCategory(ctx context.Context, c *Models.Category) error
	FindCategory(ctx context.Context, id uint64) (*Models.Category, error)
	CreateTask(ctx context.Context, t *Models.Task) error
	FindTask(ctx context.Context, id uint64) (*Models.Task, error)
	UpdateTaskStatus(ctx context.Context, taskID uint64, from, to Models.TaskStatus) error
	CreateApplication(ctx context.Context, a *Models.Application) error
	FindApplication(ctx context.Context, id uint64) (*Models.Application, error)
	UpdateApplicationStatus(ctx context.Context, id uint64, from, to Models.ApplicationStatus) error
	CreateAssignment(ctx context.Context, a *Models.Assignment) error
	FindAssignment(ctx context.Context, id uint64) (*Models.Assignment, error)
	UpdateAssignmentStatus(ctx context.Context, id uint64, from, to Models.AssignmentStatus, at time.Time) error
	AcceptApplicationAndAssign(ctx context.Context, ownerID, applicationID uint64, now time.Time) (*Models.Assignment, error)
}

type MemoryRepository struct {
	mu                                                      sync.RWMutex
	nextTask, nextCategory, nextApplication, nextAssignment uint64
	categories                                              map[uint64]*Models.Category
	tasks                                                   map[uint64]*Models.Task
	applications                                            map[uint64]*Models.Application
	assignments                                             map[uint64]*Models.Assignment
	applicationKey                                          map[[2]uint64]uint64
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{nextTask: 1, nextCategory: 1, nextApplication: 1, nextAssignment: 1,
		categories: map[uint64]*Models.Category{}, tasks: map[uint64]*Models.Task{},
		applications: map[uint64]*Models.Application{}, assignments: map[uint64]*Models.Assignment{},
		applicationKey: map[[2]uint64]uint64{}}
}
func (r *MemoryRepository) CreateCategory(ctx context.Context, c *Models.Category) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	c.ID = r.nextCategory
	r.nextCategory++
	r.categories[c.ID] = cloneCategory(c)
	return nil
}
func cloneCategory(c *Models.Category) *Models.Category { x := *c; return &x }
func (r *MemoryRepository) FindCategory(ctx context.Context, id uint64) (*Models.Category, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	c, ok := r.categories[id]
	if !ok {
		return nil, ErrCategoryNotFound
	}
	return cloneCategory(c), nil
}
func (r *MemoryRepository) CreateTask(ctx context.Context, t *Models.Task) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.categories[t.CategoryID]; !ok {
		return ErrCategoryNotFound
	}
	t.ID = r.nextTask
	r.nextTask++
	r.tasks[t.ID] = cloneTask(t)
	return nil
}
func cloneTask(t *Models.Task) *Models.Task { x := *t; return &x }
func (r *MemoryRepository) FindTask(ctx context.Context, id uint64) (*Models.Task, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	t, ok := r.tasks[id]
	if !ok {
		return nil, ErrTaskNotFound
	}
	return cloneTask(t), nil
}
func validTaskTransition(from, to Models.TaskStatus) bool {
	switch from {
	case Models.StatusDraft:
		return to == Models.StatusPublished || to == Models.StatusCancelled
	case Models.StatusPublished:
		return to == Models.StatusInProgress || to == Models.StatusCancelled
	case Models.StatusInProgress:
		return to == Models.StatusCompleted || to == Models.StatusCancelled
	default:
		return false
	}
}
func (r *MemoryRepository) UpdateTaskStatus(ctx context.Context, id uint64, from, to Models.TaskStatus) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	t, ok := r.tasks[id]
	if !ok {
		return ErrTaskNotFound
	}
	if t.Status != from || !validTaskTransition(from, to) {
		return ErrInvalidStateTransition
	}
	t.Status = to
	t.UpdatedAt = time.Now()
	return nil
}
func (r *MemoryRepository) CreateApplication(ctx context.Context, a *Models.Application) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.tasks[a.TaskID]; !ok {
		return ErrTaskNotFound
	}
	key := [2]uint64{a.TaskID, a.ApplicantID}
	if _, ok := r.applicationKey[key]; ok {
		return ErrDuplicateApplication
	}
	a.ID = r.nextApplication
	r.nextApplication++
	r.applications[a.ID] = cloneApplication(a)
	r.applicationKey[key] = a.ID
	return nil
}
func cloneApplication(a *Models.Application) *Models.Application { x := *a; return &x }
func (r *MemoryRepository) FindApplication(ctx context.Context, id uint64) (*Models.Application, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	a, ok := r.applications[id]
	if !ok {
		return nil, ErrApplicationNotFound
	}
	return cloneApplication(a), nil
}
func validApplicationTransition(from, to Models.ApplicationStatus) bool {
	switch from {
	case Models.ApplicationPending:
		return to == Models.ApplicationAccepted || to == Models.ApplicationRejected || to == Models.ApplicationWithdrawn
	default:
		return false
	}
}
func (r *MemoryRepository) UpdateApplicationStatus(ctx context.Context, id uint64, from, to Models.ApplicationStatus) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	a, ok := r.applications[id]
	if !ok {
		return ErrApplicationNotFound
	}
	if a.Status != from || !validApplicationTransition(from, to) {
		return ErrInvalidStateTransition
	}
	a.Status = to
	a.UpdatedAt = time.Now()
	return nil
}
func (r *MemoryRepository) CreateAssignment(ctx context.Context, a *Models.Assignment) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.applications[a.ApplicationID]; !ok {
		return ErrApplicationNotFound
	}
	a.ID = r.nextAssignment
	r.nextAssignment++
	r.assignments[a.ID] = cloneAssignment(a)
	return nil
}
func cloneAssignment(a *Models.Assignment) *Models.Assignment { x := *a; return &x }
func (r *MemoryRepository) FindAssignment(ctx context.Context, id uint64) (*Models.Assignment, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	a, ok := r.assignments[id]
	if !ok {
		return nil, ErrAssignmentNotFound
	}
	return cloneAssignment(a), nil
}
func validAssignmentTransition(from, to Models.AssignmentStatus) bool {
	switch from {
	case Models.AssignmentAssigned:
		return to == Models.AssignmentSubmitted || to == Models.AssignmentCancelled
	case Models.AssignmentSubmitted:
		return to == Models.AssignmentVerified || to == Models.AssignmentRejected
	default:
		return false
	}
}
func (r *MemoryRepository) UpdateAssignmentStatus(ctx context.Context, id uint64, from, to Models.AssignmentStatus, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	a, ok := r.assignments[id]
	if !ok {
		return ErrAssignmentNotFound
	}
	if a.Status != from || !validAssignmentTransition(from, to) {
		return ErrInvalidStateTransition
	}
	a.Status = to
	a.UpdatedAt = at
	if to == Models.AssignmentSubmitted {
		a.SubmittedAt = &at
	}
	if to == Models.AssignmentVerified {
		a.VerifiedAt = &at
	}
	return nil
}

func (r *MemoryRepository) AcceptApplicationAndAssign(ctx context.Context, ownerID, applicationID uint64, now time.Time) (*Models.Assignment, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	a, ok := r.applications[applicationID]
	if !ok {
		return nil, ErrApplicationNotFound
	}
	t, ok := r.tasks[a.TaskID]
	if !ok {
		return nil, ErrTaskNotFound
	}
	if t.OwnerUserID != ownerID {
		return nil, ErrForbidden
	}
	if t.Status != Models.StatusPublished || a.Status != Models.ApplicationPending {
		return nil, ErrInvalidStateTransition
	}
	for _, x := range r.assignments {
		if x.TaskID == a.TaskID {
			return nil, ErrTaskAlreadyAssigned
		}
	}
	a.Status = Models.ApplicationAccepted
	a.UpdatedAt = now
	x := &Models.Assignment{ID: r.nextAssignment, TaskID: a.TaskID, ApplicationID: a.ID, WorkerID: a.ApplicantID, AssignedBy: ownerID, Status: Models.AssignmentAssigned, CreatedAt: now, UpdatedAt: now}
	r.nextAssignment++
	r.assignments[x.ID] = cloneAssignment(x)
	return x, nil
}
