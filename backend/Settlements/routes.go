package Settlements

import (
	"github.com/alumasinde/jijenge/Settlements/Handlers"
	"net/http"
)

func RegisterRoutes(mux *http.ServeMux, h *Handlers.Handler) {
	mux.Handle("POST /api/v1/settlements", http.HandlerFunc(h.Create))
	mux.Handle("POST /api/v1/settlements/{id}/claim", http.HandlerFunc(h.Claim))
	mux.Handle("POST /api/v1/settlements/{id}/confirm", http.HandlerFunc(h.Confirm))
	mux.Handle("POST /api/v1/settlements/{id}/dispute", http.HandlerFunc(h.Dispute))
}
