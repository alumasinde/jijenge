package Services

import (
	"context"
	"errors"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Core/Security"
	"github.com/alumasinde/jijenge/Tasks/Models"
	"github.com/alumasinde/jijenge/Tasks/Repositories"
)

var (
	ErrInvalidTask        = errors.New("invalid task")
	ErrInvalidApplication = errors.New("invalid application")
	ErrInvalidAssignment  = errors.New("invalid assignment")
)

type Service struct {
	Repo Repositories.TaskRepository
	Now  func() time.Time
}

func New(repo Repositories.TaskRepository) *Service { return &Service{Repo: repo, Now: time.Now} }

func (s *Service) CreateTask(ctx context.Context, ownerID, categoryID uint64, title, description string, budgetCents int64, currency string) (*Models.Task, error) {
	title = strings.TrimSpace(title)
	description = strings.TrimSpace(description)
	currency = strings.ToUpper(strings.TrimSpace(currency))
	if ownerID == 0 || categoryID == 0 || title == "" || len(title) > 200 || len(description) > 5000 || budgetCents <= 0 || budgetCents > 9_000_000_000_000 || len(currency) != 3 {
		return nil, ErrInvalidTask
	}
	if _, err := s.Repo.FindCategory(ctx, categoryID); err != nil {
		return nil, ErrInvalidTask
	}
	now := s.Now()
	t := &Models.Task{PublicID: publicID(), OwnerUserID: ownerID, CategoryID: categoryID, Title: title, Description: description, BudgetCents: budgetCents, Currency: currency, Status: Models.StatusDraft, CreatedAt: now, UpdatedAt: now}
	if err := s.Repo.CreateTask(ctx, t); err != nil {
		return nil, err
	}
	return t, nil
}
func (s *Service) PublishTask(ctx context.Context, ownerID, taskID uint64) error {
	return s.changeTask(ctx, ownerID, taskID, Models.StatusDraft, Models.StatusPublished)
}
func (s *Service) StartTask(ctx context.Context, ownerID, taskID uint64) error {
	return s.changeTask(ctx, ownerID, taskID, Models.StatusPublished, Models.StatusInProgress)
}
func (s *Service) CompleteTask(ctx context.Context, ownerID, taskID uint64) error {
	return s.changeTask(ctx, ownerID, taskID, Models.StatusInProgress, Models.StatusCompleted)
}
func (s *Service) CancelTask(ctx context.Context, ownerID, taskID uint64) error {
	t, err := s.Repo.FindTask(ctx, taskID)
	if err != nil {
		return err
	}
	if t.OwnerUserID != ownerID {
		return Repositories.ErrForbidden
	}
	if t.Status != Models.StatusDraft && t.Status != Models.StatusPublished && t.Status != Models.StatusInProgress {
		return Repositories.ErrInvalidStateTransition
	}
	return s.Repo.UpdateTaskStatus(ctx, taskID, t.Status, Models.StatusCancelled)
}
func (s *Service) changeTask(ctx context.Context, ownerID, taskID uint64, from, to Models.TaskStatus) error {
	t, err := s.Repo.FindTask(ctx, taskID)
	if err != nil {
		return err
	}
	if t.OwnerUserID != ownerID {
		return Repositories.ErrForbidden
	}
	return s.Repo.UpdateTaskStatus(ctx, taskID, from, to)
}
func (s *Service) Apply(ctx context.Context, applicantID, taskID uint64, message string, proposedCents int64) (*Models.Application, error) {
	message = strings.TrimSpace(message)
	if applicantID == 0 || taskID == 0 || len(message) > 2000 || proposedCents <= 0 || proposedCents > 9_000_000_000_000 {
		return nil, ErrInvalidApplication
	}
	t, err := s.Repo.FindTask(ctx, taskID)
	if err != nil {
		return nil, err
	}
	if t.OwnerUserID == applicantID || t.Status != Models.StatusPublished {
		return nil, ErrInvalidApplication
	}
	now := s.Now()
	a := &Models.Application{TaskID: taskID, ApplicantID: applicantID, Message: message, ProposedCents: proposedCents, Status: Models.ApplicationPending, CreatedAt: now, UpdatedAt: now}
	if err := s.Repo.CreateApplication(ctx, a); err != nil {
		return nil, err
	}
	return a, nil
}
func (s *Service) AcceptApplication(ctx context.Context, ownerID, applicationID uint64) (*Models.Assignment, error) {
	if ownerID == 0 || applicationID == 0 {
		return nil, ErrInvalidAssignment
	}
	return s.Repo.AcceptApplicationAndAssign(ctx, ownerID, applicationID, s.Now())
}

func (s *Service) Submit(ctx context.Context, workerID, assignmentID uint64) error {
	a, err := s.Repo.FindAssignment(ctx, assignmentID)
	if err != nil {
		return err
	}
	if a.WorkerID != workerID {
		return Repositories.ErrForbidden
	}
	return s.Repo.UpdateAssignmentStatus(ctx, assignmentID, Models.AssignmentAssigned, Models.AssignmentSubmitted, s.Now())
}
func (s *Service) Verify(ctx context.Context, ownerID, assignmentID uint64) error {
	a, err := s.Repo.FindAssignment(ctx, assignmentID)
	if err != nil {
		return err
	}
	t, err := s.Repo.FindTask(ctx, a.TaskID)
	if err != nil {
		return err
	}
	if t.OwnerUserID != ownerID {
		return Repositories.ErrForbidden
	}
	return s.Repo.UpdateAssignmentStatus(ctx, assignmentID, Models.AssignmentSubmitted, Models.AssignmentVerified, s.Now())
}
func publicID() string {
	b, err := Security.GenerateToken(32)
	if err != nil {
		panic(err)
	}
	return b[:26]
}
