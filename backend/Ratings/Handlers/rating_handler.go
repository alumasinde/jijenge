package Handlers

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/alumasinde/jijenge/Auth/Middleware"
	"github.com/alumasinde/jijenge/Core/HTTP"
	"github.com/alumasinde/jijenge/Ratings/Repositories"
	"github.com/alumasinde/jijenge/Ratings/Services"
	"net/http"
)

type Handler struct{ Service *Services.Service }
type createRequest struct {
	RevieweeUserID uint64 `json:"reviewee_user_id"`
	Score          int    `json:"score"`
	Comment        string `json:"comment"`
}

func New(s *Services.Service) *Handler { return &Handler{Service: s} }

func (h *Handler) Create(w http.ResponseWriter, r *http.Request) {
	reviewer, ok := Middleware.UserID(r.Context())
	if !ok {
		HTTP.ErrorResponse(w, 401, "UNAUTHORIZED", "Authentication required")
		return
	}
	var assignment uint64
	if _, err := fmt.Sscanf(r.PathValue("id"), "%d", &assignment); err != nil || assignment == 0 {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid assignment ID")
		return
	}
	var q createRequest
	if json.NewDecoder(r.Body).Decode(&q) != nil {
		HTTP.ErrorResponse(w, 400, "INVALID_JSON", "Invalid request body")
		return
	}
	x, err := h.Service.Create(r.Context(), assignment, reviewer, q.RevieweeUserID, q.Score, q.Comment)
	if err != nil {
		if errors.Is(err, Repositories.ErrDuplicate) {
			HTTP.ErrorResponse(w, 409, "DUPLICATE_RATING", "Rating already exists")
			return
		}
		HTTP.ErrorResponse(w, 400, "INVALID_RATING", "Unable to create rating")
		return
	}
	HTTP.JSON(w, 201, x)
}
func (h *Handler) Average(w http.ResponseWriter, r *http.Request) {
	var user uint64
	if _, err := fmt.Sscanf(r.PathValue("id"), "%d", &user); err != nil || user == 0 {
		HTTP.ErrorResponse(w, 400, "INVALID_ID", "Invalid user ID")
		return
	}
	avg, n, err := h.Service.Repo.Average(r.Context(), user)
	if err != nil {
		HTTP.ErrorResponse(w, 500, "INTERNAL_SERVER_ERROR", "Unable to load rating")
		return
	}
	HTTP.JSON(w, 200, map[string]any{"average": avg, "count": n})
}
