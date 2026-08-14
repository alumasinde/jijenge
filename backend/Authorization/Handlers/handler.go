package Handlers

import (
	"encoding/json"
	"errors"
	"net/http"

	"github.com/alumasinde/jijenge/Authorization/Services"
	"github.com/alumasinde/jijenge/Core/HTTP"
)

type Handler struct {
	Service *Services.AuthorizationService
}

type createRequest struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}

func New(service *Services.AuthorizationService) *Handler { return &Handler{Service: service} }

func (h *Handler) CreateRole(w http.ResponseWriter, r *http.Request) {
	var req createRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		HTTP.ErrorResponse(w, http.StatusBadRequest, "INVALID_JSON", "Invalid request body")
		return
	}
	role, err := h.Service.CreateRole(r.Context(), req.Name, req.Description)
	if err != nil {
		if errors.Is(err, Services.ErrInvalidRole) {
			HTTP.ErrorResponse(w, http.StatusBadRequest, "VALIDATION_ERROR", "Invalid role")
			return
		}
		HTTP.ErrorResponse(w, http.StatusInternalServerError, "INTERNAL_SERVER_ERROR", "Unable to create role")
		return
	}
	HTTP.JSON(w, http.StatusCreated, role)
}

func (h *Handler) CreatePermission(w http.ResponseWriter, r *http.Request) {
	var req createRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		HTTP.ErrorResponse(w, http.StatusBadRequest, "INVALID_JSON", "Invalid request body")
		return
	}
	p, err := h.Service.CreatePermission(r.Context(), req.Name, req.Description)
	if err != nil {
		if errors.Is(err, Services.ErrInvalidPermission) {
			HTTP.ErrorResponse(w, http.StatusBadRequest, "VALIDATION_ERROR", "Invalid permission")
			return
		}
		HTTP.ErrorResponse(w, http.StatusInternalServerError, "INTERNAL_SERVER_ERROR", "Unable to create permission")
		return
	}
	HTTP.JSON(w, http.StatusCreated, p)
}
