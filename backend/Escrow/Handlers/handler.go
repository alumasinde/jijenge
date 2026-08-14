package Handlers

import (
	"encoding/json"
	Auth "github.com/alumasinde/jijenge/Auth/Middleware"
	"github.com/alumasinde/jijenge/Core/HTTP"
	"github.com/alumasinde/jijenge/Escrow/Models"
	"github.com/alumasinde/jijenge/Escrow/Services"
	"net/http"
	"strconv"
	"strings"
	"time"
)

type Handler struct{ Service *Services.Service }
type fundRequest struct {
	TaskID, AssignmentID, PayerAccountID, WorkerAccountID uint64
	AmountCents                                           int64
	Currency                                              string
}
type disputeRequest struct {
	Reason string `json:"reason"`
}

func New(s *Services.Service) *Handler { return &Handler{Service: s} }

func (h *Handler) Fund(w http.ResponseWriter, r *http.Request) {
	uid, ok := Auth.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	var q fundRequest
	if json.NewDecoder(r.Body).Decode(&q) != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_JSON", "Invalid request body")
		return
	}
	if q.TaskID == 0 || q.AssignmentID == 0 || q.PayerAccountID == 0 || q.WorkerAccountID == 0 || q.AmountCents <= 0 || len(strings.TrimSpace(q.Currency)) != 3 {
		HTTP.ErrorResponse(w, 400, "INVALID_ESCROW", "Invalid escrow request")
		return
	}
	key := strings.TrimSpace(r.Header.Get("Idempotency-Key"))
	if len(key) < 16 || len(key) > 128 {
		HTTP.ErrorResponse(w, 400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key must be 16-128 characters")
		return
	}
	e := &Models.Escrow{TaskID: q.TaskID, AssignmentID: q.AssignmentID, PayerAccountID: q.PayerAccountID, WorkerAccountID: q.WorkerAccountID, AmountCents: q.AmountCents, Currency: q.Currency, IdempotencyKey: key, CreatedAt: time.Now(), UpdatedAt: time.Now()}
	if err := h.Service.FundForUser(r.Context(), e, uid); err != nil {
		HTTP.ErrorResponse(w, 409, "ESCROW_FUNDING_FAILED", "Unable to fund escrow")
		return
	}
	HTTP.JSON(w, 201, e)
}
func (h *Handler) Dispute(w http.ResponseWriter, r *http.Request) {
	uid, ok := Auth.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	id, err := strconv.ParseUint(r.PathValue("id"), 10, 64)
	if err != nil || id == 0 {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid escrow ID")
		return
	}
	var q disputeRequest
	if json.NewDecoder(r.Body).Decode(&q) != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_JSON", "Invalid request body")
		return
	}
	d, err := h.Service.Dispute(r.Context(), id, uid, q.Reason)
	if err != nil {
		HTTP.ErrorResponse(w, 409, "DISPUTE_REJECTED", "Unable to open dispute")
		return
	}
	HTTP.JSON(w, 201, d)
}
