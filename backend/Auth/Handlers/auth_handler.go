package Handlers

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"

	"github.com/alumasinde/jijenge/Auth/DTOs"
	"github.com/alumasinde/jijenge/Auth/Repositories"
	"github.com/alumasinde/jijenge/Auth/Services"
	"github.com/alumasinde/jijenge/Auth/Validators"
	"github.com/alumasinde/jijenge/Core/HTTP"
)

type AuthHandler struct {
	Service *Services.AuthService

	// AccountProvisioner is an optional hook, wired at composition time
	// (see Routes.Register), that creates a Financial ledger account for
	// a newly registered user. It is deliberately decoupled from
	// Auth/Services so the Auth domain never imports Financial directly.
	//
	// It returns the newly created account's numeric ID so it can be
	// surfaced in the registration response. If it is nil (no database
	// configured, e.g. in-memory/unit-test composition), registration
	// proceeds without provisioning an account.
	AccountProvisioner func(ctx context.Context, userID uint64) (uint64, error)
}

func NewAuthHandler(service *Services.AuthService) *AuthHandler {
	return &AuthHandler{Service: service}
}

// SetAccountProvisioner wires the optional financial-account provisioning
// hook. See the AccountProvisioner field docs for details.
func (h *AuthHandler) SetAccountProvisioner(fn func(ctx context.Context, userID uint64) (uint64, error)) {
	h.AccountProvisioner = fn
}

func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	var req DTOs.RegisterRequest
	if err := decodeJSON(r, &req); err != nil {
		HTTP.ErrorResponse(w, http.StatusBadRequest, "INVALID_JSON", "Invalid request body")
		return
	}
	if err := Validators.Register(req); err != nil {
		HTTP.ErrorResponse(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
		return
	}

	user, err := h.Service.Register(r.Context(), req)
	if err != nil {
		if errors.Is(err, Repositories.ErrEmailExists) {
			HTTP.ErrorResponse(w, http.StatusConflict, "EMAIL_EXISTS", "An account with that email already exists")
			return
		}
		HTTP.ErrorResponse(w, http.StatusInternalServerError, "INTERNAL_SERVER_ERROR", "Unable to create account")
		return
	}

	resp := map[string]any{
		"id":         user.ID,
		"public_id":  user.PublicID,
		"email":      user.Email,
		"first_name": req.FirstName,
		"last_name":  req.LastName,
	}

	// Best-effort financial account provisioning. A failure here must never
	// fail registration itself (the user's login credentials already exist
	// and are valid) -- it is logged so an operator can provision the
	// account manually, and financial_account_id is simply omitted from the
	// response. Nothing about funds is at risk: a brand-new account always
	// starts at a zero balance, so a missing account only blocks that user
	// from receiving/funding escrow until it exists, it never creates an
	// inconsistent financial state.
	if h.AccountProvisioner != nil {
		accountID, err := h.AccountProvisioner(r.Context(), user.ID)
		if err != nil {
			slog.Error("financial account provisioning failed after registration",
				"user_id", user.ID, "error", err)
		} else {
			resp["financial_account_id"] = accountID
		}
	}

	HTTP.JSON(w, http.StatusCreated, resp)
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	var req DTOs.LoginRequest
	if err := decodeJSON(r, &req); err != nil {
		HTTP.ErrorResponse(w, http.StatusBadRequest, "INVALID_JSON", "Invalid request body")
		return
	}
	if err := Validators.Login(req); err != nil {
		HTTP.ErrorResponse(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
		return
	}

	result, err := h.Service.Login(r.Context(), req)
	if err != nil {
		if errors.Is(err, Services.ErrInvalidCredentials) {
			HTTP.ErrorResponse(w, http.StatusUnauthorized, "INVALID_CREDENTIALS", "Invalid email or password")
			return
		}
		if errors.Is(err, Services.ErrAccountDisabled) {
			HTTP.ErrorResponse(w, http.StatusForbidden, "ACCOUNT_DISABLED", "This account is not active")
			return
		}
		HTTP.ErrorResponse(w, http.StatusInternalServerError, "INTERNAL_SERVER_ERROR", "Unable to authenticate")
		return
	}

	HTTP.JSON(w, http.StatusOK, result)
}

func (h *AuthHandler) Refresh(w http.ResponseWriter, r *http.Request) {
	var req DTOs.RefreshRequest
	if err := decodeJSON(r, &req); err != nil {
		HTTP.ErrorResponse(w, http.StatusBadRequest, "INVALID_JSON", "Invalid request body")
		return
	}

	result, err := h.Service.Refresh(r.Context(), req.RefreshToken)
	if err != nil {
		HTTP.ErrorResponse(w, http.StatusUnauthorized, "INVALID_REFRESH_TOKEN", "Invalid refresh token")
		return
	}
	HTTP.JSON(w, http.StatusOK, result)
}

func (h *AuthHandler) Logout(w http.ResponseWriter, r *http.Request) {
	var req DTOs.RefreshRequest
	if err := decodeJSON(r, &req); err != nil {
		HTTP.ErrorResponse(w, http.StatusBadRequest, "INVALID_JSON", "Invalid request body")
		return
	}
	if err := h.Service.Logout(r.Context(), req.RefreshToken); err != nil {
		HTTP.ErrorResponse(w, http.StatusInternalServerError, "INTERNAL_SERVER_ERROR", "Unable to log out")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func decodeJSON(r *http.Request, dst any) error {
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	return decoder.Decode(dst)
}
