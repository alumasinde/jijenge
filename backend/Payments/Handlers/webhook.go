package Handlers

import (
	"bytes"
	"io"
	"net/http"
	"strings"

	"github.com/alumasinde/jijenge/Core/HTTP"
	"github.com/alumasinde/jijenge/Payments/Services"
)

type WebhookHandler struct {
	Service *Services.Service
	MaxBody int64
}

func NewWebhookHandler(service *Services.Service, maxBody int64) *WebhookHandler {
	if maxBody <= 0 || maxBody > 1<<20 {
		maxBody = 1 << 20
	}
	return &WebhookHandler{Service: service, MaxBody: maxBody}
}

// Handle reads a bounded raw payload. Signature verification happens before
// JSON parsing so an unauthenticated body cannot reach financial logic.
func (h *WebhookHandler) Handle(w http.ResponseWriter, r *http.Request) {
	if h.Service == nil {
		HTTP.ErrorResponse(w, http.StatusServiceUnavailable, "PAYMENTS_UNAVAILABLE", "Payment service unavailable")
		return
	}
	signature := strings.TrimSpace(r.Header.Get("X-Provider-Signature"))
	if signature == "" || len(signature) > 1024 {
		HTTP.ErrorResponse(w, http.StatusUnauthorized, "INVALID_SIGNATURE", "Invalid webhook signature")
		return
	}
	body, err := io.ReadAll(io.LimitReader(r.Body, h.MaxBody+1))
	if err != nil {
		HTTP.ErrorResponse(w, http.StatusBadRequest, "INVALID_BODY", "Unable to read request")
		return
	}
	if int64(len(body)) > h.MaxBody {
		HTTP.ErrorResponse(w, http.StatusRequestEntityTooLarge, "BODY_TOO_LARGE", "Webhook payload too large")
		return
	}
	// Keep the exact bytes used for HMAC verification; do not normalize,
	// re-encode, or trim the signed payload.
	_, err = h.Service.HandleWebhook(r.Context(), bytes.Clone(body), signature)
	if err != nil {
		switch {
		case strings.Contains(err.Error(), "signature"):
			HTTP.ErrorResponse(w, http.StatusUnauthorized, "INVALID_SIGNATURE", "Invalid webhook signature")
		case err == Services.ErrProviderEventConflict:
			HTTP.ErrorResponse(w, http.StatusConflict, "PROVIDER_EVENT_CONFLICT", "Provider event conflicts with payment")
		default:
			HTTP.ErrorResponse(w, http.StatusBadRequest, "WEBHOOK_REJECTED", "Webhook rejected")
		}
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
