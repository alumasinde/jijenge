package Payments

import (
	"net/http"

	"github.com/alumasinde/jijenge/Payments/Handlers"
)

// RegisterWebhookRoute registers a provider webhook after the caller has
// explicitly constructed a securely configured webhook handler.
func RegisterWebhookRoute(mux *http.ServeMux, handler *Handlers.WebhookHandler) {
	mux.HandleFunc("POST /api/v1/payments/webhook", handler.Handle)
}
