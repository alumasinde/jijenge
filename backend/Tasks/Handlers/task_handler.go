package Handlers

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/alumasinde/jijenge/Auth/Middleware"
	"github.com/alumasinde/jijenge/Core/HTTP"
	EscrowRepos "github.com/alumasinde/jijenge/Escrow/Repositories"
	EscrowServices "github.com/alumasinde/jijenge/Escrow/Services"
	TaskModels "github.com/alumasinde/jijenge/Tasks/Models"
	"github.com/alumasinde/jijenge/Tasks/Repositories"
	"github.com/alumasinde/jijenge/Tasks/Services"
	"net/http"
)

type Handler struct {
	Service *Services.Service
	Escrow  *EscrowServices.Service
}
type createTaskRequest struct {
	CategoryID  uint64 `json:"category_id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	BudgetCents int64  `json:"budget_cents"`
	Currency    string `json:"currency"`
}
type applyRequest struct {
	Message       string `json:"message"`
	ProposedCents int64  `json:"proposed_cents"`
}

func New(s *Services.Service) *Handler                 { return &Handler{Service: s} }
func (h *Handler) SetEscrow(s *EscrowServices.Service) { h.Escrow = s }
func (h *Handler) Create(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	var q createTaskRequest
	if json.NewDecoder(r.Body).Decode(&q) != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_JSON", "Invalid request body")
		return
	}
	t, err := h.Service.CreateTask(r.Context(), uid, q.CategoryID, q.Title, q.Description, q.BudgetCents, q.Currency)
	if err != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_TASK", "Invalid task")
		return
	}
	HTTP.JSON(w, 201, t)
}
func (h *Handler) Publish(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	id, err := pathID(r)
	if err != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid task ID")
		return
	}
	err = h.Service.PublishTask(r.Context(), uid, id)
	writeStateError(w, err, string(TaskModels.StatusPublished))
}
func (h *Handler) Apply(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	id, err := pathID(r)
	if err != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid task ID")
		return
	}
	var q applyRequest
	if json.NewDecoder(r.Body).Decode(&q) != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_JSON", "Invalid request body")
		return
	}
	a, err := h.Service.Apply(r.Context(), uid, id, q.Message, q.ProposedCents)
	if err != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_APPLICATION", "Unable to apply")
		return
	}
	HTTP.JSON(w, 201, a)
}
func pathID(r *http.Request) (uint64, error) {
	var id uint64
	_, err := fmt.Sscanf(r.PathValue("id"), "%d", &id)
	if err != nil || id == 0 {
		return 0, err
	}
	return id, nil
}
func writeStateError(w http.ResponseWriter, err error, newStatus string) {
	if err == nil {
		HTTP.JSON(w, http.StatusOK, map[string]string{"status": newStatus})
		return
	}
	if errors.Is(err, Repositories.ErrForbidden) {
		HTTP.ErrorResponse(w, 403, "FORBIDDEN", "You are not allowed to perform this action")
		return
	}
	if errors.Is(err, Repositories.ErrTaskNotFound) {
		HTTP.ErrorResponse(w, 404, "NOT_FOUND", "Task not found")
		return
	}
	if errors.Is(err, Repositories.ErrInvalidStateTransition) {
		HTTP.ErrorResponse(w, 409, "INVALID_STATE", "Invalid state transition")
		return
	}
	HTTP.ErrorResponse(w, 500, "INTERNAL_SERVER_ERROR", "Unable to update task")
}

func (h *Handler) Start(w http.ResponseWriter, r *http.Request) {
	h.stateAction(w, r, string(TaskModels.StatusInProgress), func(uid, id uint64) error { return h.Service.StartTask(r.Context(), uid, id) })
}
func (h *Handler) Complete(w http.ResponseWriter, r *http.Request) {
	h.stateAction(w, r, string(TaskModels.StatusCompleted), func(uid, id uint64) error { return h.Service.CompleteTask(r.Context(), uid, id) })
}
func (h *Handler) Cancel(w http.ResponseWriter, r *http.Request) {
	h.stateAction(w, r, string(TaskModels.StatusCancelled), func(uid, id uint64) error { return h.Service.CancelTask(r.Context(), uid, id) })
}
func (h *Handler) AcceptApplication(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	id, err := pathID(r)
	if err != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid application ID")
		return
	}
	a, err := h.Service.AcceptApplication(r.Context(), uid, id)
	if err != nil {
		writeAssignmentError(w, err)
		return
	}
	HTTP.JSON(w, 201, a)
}
func (h *Handler) Submit(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	id, err := pathID(r)
	if err != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid assignment ID")
		return
	}
	if err = h.Service.Submit(r.Context(), uid, id); err != nil {
		writeAssignmentError(w, err)
		return
	}
	if h.Escrow != nil {
		if e, eerr := h.Escrow.Repo.GetByAssignment(r.Context(), id); eerr == nil && e != nil {
			if eerr = h.Escrow.SubmitAssignment(r.Context(), id); eerr != nil {
				HTTP.ErrorResponse(w, 409, "ESCROW_STATE", "Work submitted but escrow state could not be updated")
				return
			}
		} else if eerr != nil && !errors.Is(eerr, EscrowRepos.ErrEscrowNotFound) {
			HTTP.ErrorResponse(w, 500, "ESCROW_ERROR", "Unable to load escrow")
			return
		}
	}
	HTTP.JSON(w, http.StatusOK, map[string]string{"status": string(TaskModels.AssignmentSubmitted)})
}
func (h *Handler) Verify(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	id, err := pathID(r)
	if err != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid assignment ID")
		return
	}
	if err = h.Service.Verify(r.Context(), uid, id); err != nil {
		writeAssignmentError(w, err)
		return
	}
	if h.Escrow != nil {
		if e, eerr := h.Escrow.Repo.GetByAssignment(r.Context(), id); eerr == nil && e != nil {
			if eerr = h.Escrow.ReleaseVerifiedAssignment(r.Context(), id); eerr != nil {
				HTTP.ErrorResponse(w, 409, "ESCROW_RELEASE_PENDING", "Work verified but escrow release is pending")
				return
			}
		} else if eerr != nil && !errors.Is(eerr, EscrowRepos.ErrEscrowNotFound) {
			HTTP.ErrorResponse(w, 500, "ESCROW_ERROR", "Unable to load escrow")
			return
		}
	}
	HTTP.JSON(w, http.StatusOK, map[string]string{"status": string(TaskModels.AssignmentVerified)})
}
func (h *Handler) stateAction(w http.ResponseWriter, r *http.Request, newStatus string, fn func(uint64, uint64) error) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	id, err := pathID(r)
	if err != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid task ID")
		return
	}
	writeStateError(w, fn(uid, id), newStatus)
}
func writeAssignmentError(w http.ResponseWriter, err error) {
	if err == nil {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	if errors.Is(err, Repositories.ErrForbidden) {
		HTTP.ErrorResponse(w, 403, "FORBIDDEN", "You are not allowed to perform this action")
		return
	}
	if errors.Is(err, Repositories.ErrAssignmentNotFound) || errors.Is(err, Repositories.ErrApplicationNotFound) {
		HTTP.ErrorResponse(w, 404, "NOT_FOUND", "Assignment or application not found")
		return
	}
	if errors.Is(err, Repositories.ErrTaskAlreadyAssigned) || errors.Is(err, Repositories.ErrInvalidStateTransition) {
		HTTP.ErrorResponse(w, 409, "INVALID_STATE", "Invalid workflow state")
		return
	}
	HTTP.ErrorResponse(w, 500, "INTERNAL_SERVER_ERROR", "Unable to update workflow")
}

func (h *Handler) Release(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	id, err := pathID(r)
	if err != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid assignment ID")
		return
	}
	if h.Escrow == nil {
		HTTP.ErrorResponse(w, 503, "ESCROW_UNAVAILABLE", "Escrow service unavailable")
		return
	}
	if err = h.Escrow.ReleaseVerifiedAssignmentForUser(r.Context(), id, uid); err != nil {
		HTTP.ErrorResponse(w, 409, "ESCROW_RELEASE_REJECTED", "Escrow release could not be completed")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
