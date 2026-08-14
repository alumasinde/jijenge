package Handlers

import (
	"encoding/json"
	"github.com/alumasinde/jijenge/Auth/Middleware"
	"github.com/alumasinde/jijenge/Core/HTTP"
	"github.com/alumasinde/jijenge/Settlements/Models"
	"github.com/alumasinde/jijenge/Settlements/Services"
	"net/http"
	"strconv"
	"strings"
)

type Handler struct{ Service *Services.Service }
type createRequest struct {
	TaskID            uint64        `json:"task_id"`
	AssignmentID      uint64        `json:"assignment_id"`
	PayeeUserID       uint64        `json:"payee_user_id"`
	Method            Models.Method `json:"method"`
	AmountCents       int64         `json:"amount_cents"`
	Currency          string        `json:"currency"`
	EvidenceReference string        `json:"evidence_reference"`
}
type noteRequest struct {
	Note string `json:"note"`
}
type reasonRequest struct {
	Reason string `json:"reason"`
}

func New(s *Services.Service) *Handler { return &Handler{Service: s} }

func id(r *http.Request) (uint64, error) { return strconv.ParseUint(r.PathValue("id"), 10, 64) }

func (h *Handler) Create(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	key := strings.TrimSpace(r.Header.Get("Idempotency-Key"))
	if len(key) < 16 || len(key) > 128 {
		HTTP.ErrorResponse(w, 400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key must be 16-128 characters")
		return
	}
	var q createRequest
	if json.NewDecoder(r.Body).Decode(&q) != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_JSON", "Invalid request body")
		return
	}
	x, err := h.Service.CreateManualForUser(r.Context(), q.TaskID, q.AssignmentID, uid, q.PayeeUserID, uid, q.Method, q.AmountCents, q.Currency, q.EvidenceReference, key)
	if err != nil {
		HTTP.ErrorResponse(w, 409, "SETTLEMENT_REJECTED", "Settlement could not be created")
		return
	}
	HTTP.JSON(w, 201, x)
}
func (h *Handler) Claim(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	sid, err := id(r)
	if err != nil || sid == 0 {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid settlement ID")
		return
	}
	if err = h.Service.Claim(r.Context(), sid, uid); err != nil {
		HTTP.ErrorResponse(w, 409, "SETTLEMENT_STATE", "Settlement cannot be claimed")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
func (h *Handler) Confirm(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	sid, err := id(r)
	if err != nil || sid == 0 {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid settlement ID")
		return
	}
	var q noteRequest
	if json.NewDecoder(r.Body).Decode(&q) != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_JSON", "Invalid request body")
		return
	}
	if err = h.Service.ConfirmWithNote(r.Context(), sid, uid, q.Note); err != nil {
		HTTP.ErrorResponse(w, 409, "SETTLEMENT_STATE", "Settlement cannot be confirmed")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
func (h *Handler) Dispute(w http.ResponseWriter, r *http.Request) {
	uid, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	sid, err := id(r)
	if err != nil || sid == 0 {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid settlement ID")
		return
	}
	var q reasonRequest
	if json.NewDecoder(r.Body).Decode(&q) != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_JSON", "Invalid request body")
		return
	}
	if err = h.Service.DisputeWithReason(r.Context(), sid, uid, q.Reason); err != nil {
		HTTP.ErrorResponse(w, 409, "SETTLEMENT_DISPUTED", "Settlement cannot be disputed")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
